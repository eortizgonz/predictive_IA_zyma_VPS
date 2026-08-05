import re
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from models.copilot import CopilotRequest, WorkOrderPreviewRequest
from ml.model_info import get_model_report
from services.copilot_service import CopilotService
from services.database_service import DatabaseService
from services.rag_service import RAGService
from services.simulator_service import SimulatorService

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
simulator = SimulatorService()
rag_service = RAGService()
database_service = DatabaseService()
copilot_service = CopilotService(simulator, rag_service, database_service)

history = {"time": [], "temperature": [], "vibration": [], "risk": []}
counter = 0


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/api/health")
async def health():
    return {
        "status": "ok",
        "database": "sqlite",
        "vector_database": "chromadb",
        "vector_documents": rag_service.count(),
        "copilot_mode": "grounded-local",
    }


@router.get("/api/machines")
async def get_machines():
    global counter
    simulator.update()
    machines = simulator.get_all()
    avg_temperature = sum(m["temperature"] for m in machines) / len(machines)
    avg_vibration = sum(m["vibration"] for m in machines) / len(machines)
    avg_risk = sum(m["failure_probability"] for m in machines) / len(machines)
    history["time"].append(counter)
    history["temperature"].append(round(avg_temperature, 2))
    history["vibration"].append(round(avg_vibration, 2))
    history["risk"].append(round(avg_risk, 2))
    counter += 1
    for key in history:
        if len(history[key]) > 30:
            history[key].pop(0)
    return machines


@router.get("/api/history")
async def get_history():
    return history


@router.post("/api/copilot/chat")
async def predictive_copilot(request: CopilotRequest):
    try:
        return copilot_service.process(request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"No fue posible procesar la consulta: {exc}") from exc


@router.post("/api/work-orders/preview")
async def preview_work_order(request: WorkOrderPreviewRequest):
    try:
        return copilot_service.work_order_preview(request.machine_id, request.estimated_cost)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/api/knowledge/search")
async def search_knowledge(q: str, machine_id: str | None = None, limit: int = 4):
    return {"results": rag_service.search(q, machine_id=machine_id, limit=max(1, min(limit, 10)))}


@router.get("/api/machines/{machine_id}/ai-report")
async def get_machine_ai_report(machine_id: str, risk: Optional[float] = None):
    machine = simulator.get_by_id(machine_id)
    if not machine:
        raise HTTPException(status_code=404, detail="Máquina no encontrada")

    m_data = machine.to_dict()
    failure_probability = float(risk if risk is not None else m_data.get("failure_probability", 0))

    manual = rag_service.get_machine_manual_info(machine_id, failure_probability)
    contexto_rag = manual["content"]
    model_report = get_model_report(m_data, failure_probability)

    diag_match = re.search(
        r"Diagnóstico:\s*(.*?)(?=\nRecomendaciones:|\nAcciones:|\Z)",
        contexto_rag,
        re.DOTALL | re.IGNORECASE,
    )
    causa_probable = diag_match.group(1).strip() if diag_match else contexto_rag.strip()
    recom_match = re.search(r"Recomendaciones:\s*(.*)", contexto_rag, re.DOTALL | re.IGNORECASE)
    acciones_mantenimiento = []
    if recom_match:
        for line in recom_match.group(1).strip().split("\n"):
            line_clean = re.sub(r"^[\-\*\d\.\)\s]+", "", line.strip()).strip()
            if line_clean and not line_clean.startswith("="):
                acciones_mantenimiento.append(line_clean)
    if not acciones_mantenimiento:
        acciones_mantenimiento = [
            "Ejecutar procedimiento técnico de inspección según SOP de la máquina.",
            "Verificar temperatura, vibración y corriente antes del reencendido.",
            "Consultar al supervisor de planta antes de reanudar el proceso.",
        ]

    return {
        "diagnostico_resumido": (
            f"{manual['equipment_name']}: riesgo predictivo de {failure_probability:.1f}% "
            f"clasificado como {model_report['classification']}."
        ),
        "causa_probable": causa_probable,
        "prioridad_atencion": m_data.get("status", model_report["classification"]),
        "acciones_mantenimiento": acciones_mantenimiento,
        "manual": manual,
        "modelo_predictivo": model_report,
        "telemetria_actual": {
            "temperature": m_data.get("temperature"),
            "vibration": m_data.get("vibration"),
            "current": m_data.get("current"),
            "pressure": m_data.get("pressure"),
            "rpm": m_data.get("rpm"),
            "load": m_data.get("load"),
            "operating_hours": m_data.get("operating_hours"),
        },
        "referencia_rag": contexto_rag,
    }

