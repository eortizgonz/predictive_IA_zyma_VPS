"""Orquestador del Predictive Copilot con RAG y generación opcional."""
from __future__ import annotations

import os
import re
from typing import Any

from services.database_service import DatabaseService
from services.rag_service import RAGService


class CopilotService:
    def __init__(self, simulator, rag: RAGService, database: DatabaseService) -> None:
        self.simulator = simulator
        self.rag = rag
        self.database = database

    @staticmethod
    def _rank(machines: list[dict]) -> list[dict]:
        return sorted(machines, key=lambda item: item["failure_probability"], reverse=True)

    @staticmethod
    def _intent(question: str) -> str:
        q = question.lower()
        if any(word in q for word in ["por qué", "porque", "explica", "causa"]):
            return "explain_prediction"
        if any(word in q for word in ["esper", "aplaz", "días", "horas", "qué pasa si"]):
            return "simulate_delay"
        if any(word in q for word in ["dinero", "costo", "pérdida", "roi", "financ", "inversión"]):
            return "financial_risk"
        if any(word in q for word in ["sensor", "datos", "modelo", "tecnolog", "confianza"]):
            return "technology_health"
        if any(word in q for word in ["orden", "mantenimiento", "intervenir"]):
            return "recommended_action"
        return "highest_risk_asset"

    @staticmethod
    def _financial(machine: dict) -> dict:
        cost_per_hour = float(os.getenv("COST_PER_DOWNTIME_HOUR", "5500"))
        planned_cost = float(os.getenv("PLANNED_MAINTENANCE_COST", "4500"))
        repair_hours = float(max(2.0, round(3 + float(machine["failure_probability"]) / 8, 1)))
        probability = float(machine["failure_probability"]) / 100
        potential_loss = float(round(cost_per_hour * repair_hours * probability + planned_cost * 2, 2))
        avoidable_loss = float(max(0, round(potential_loss - planned_cost, 2)))
        roi = float(round(avoidable_loss / planned_cost, 2)) if planned_cost else 0.0
        return {
            "currency": os.getenv("CURRENCY", "USD"),
            "cost_per_downtime_hour": cost_per_hour,
            "estimated_downtime_hours": repair_hours,
            "potential_loss": potential_loss,
            "intervention_cost": planned_cost,
            "avoidable_loss": avoidable_loss,
            "roi_multiple": roi,
            "is_estimate": True,
        }

    @staticmethod
    def _operational(machine: dict) -> dict:
        production_rate = float(os.getenv("PRODUCTION_UNITS_PER_HOUR", "85"))
        downtime = float(max(2.0, round(3 + float(machine["failure_probability"]) / 8, 1)))
        return {
            "estimated_downtime_hours": downtime,
            "production_units_at_risk": round(production_rate * downtime),
            "production_rate_per_hour": production_rate,
            "recommended_window": "próxima ventana de menor carga",
            "is_estimate": True,
        }

    @staticmethod
    def _factors(machine: dict) -> list[dict]:
        raw = {
            "Vibración": min(100, machine["vibration"] / 3 * 100),
            "Temperatura": min(100, machine["temperature"] / 90 * 100),
            "Carga": min(100, machine["load"]),
            "Corriente": min(100, machine["current"] / 40 * 100),
            "Desgaste": min(100, machine["wear_level"]),
        }
        total = sum(raw.values()) or 1
        return [
            {"name": name, "contribution": round(value / total * 100, 1)}
            for name, value in sorted(raw.items(), key=lambda item: item[1], reverse=True)
        ]

    def process(self, request) -> dict[str, Any]:
        self.simulator.update()
        machines = self.simulator.get_all()
        if request.machine_id:
            selected = [m for m in machines if m["machine_id"] == request.machine_id]
            if selected:
                machines = selected
        ranked = self._rank(machines)
        top = ranked[0]
        intent = self._intent(request.question)
        operational = self._operational(top)
        financial = self._financial(top)
        factors = self._factors(top)
        context = self.rag.query_context(
            top["machine_id"], top["temperature"], top["vibration"],
            top["status"], top["failure_probability"],
        )
        source = {
            "name": "manuales_planta.txt",
            "type": "technical_manual",
            "excerpt": context[:420],
        }

        recommendation = (
            f"Validar técnicamente {top['machine_id']} y programar una inspección en la "
            f"{operational['recommended_window']}."
        )
        if intent == "explain_prediction":
            summary = (
                f"{top['machine_id']} registra {top['failure_probability']:.1f}% de riesgo. "
                f"Los factores con mayor contribución estimada son {factors[0]['name']} "
                f"y {factors[1]['name']}."
            )
        elif intent == "financial_risk":
            summary = (
                f"La exposición económica estimada de {top['machine_id']} es "
                f"{financial['currency']} {financial['potential_loss']:,.0f}. "
                f"La pérdida potencial evitable se estima en {financial['currency']} "
                f"{financial['avoidable_loss']:,.0f}."
            )
        elif intent == "technology_health":
            summary = (
                "La respuesta combina los datos actuales del simulador, el modelo predictivo "
                "y recuperación documental desde ChromaDB persistente."
            )
        elif intent == "simulate_delay":
            days = self._extract_number(request.question, default=3)
            simulated_risk = min(99.0, top["failure_probability"] + days * 2.5)
            increase = simulated_risk - top["failure_probability"]
            summary = (
                f"Al simular una espera de {days:g} días, el riesgo de {top['machine_id']} "
                f"aumentaría aproximadamente {increase:.1f} puntos, hasta {simulated_risk:.1f}%."
            )
        else:
            summary = (
                f"El activo prioritario es {top['machine_id']}, con riesgo de falla de "
                f"{top['failure_probability']:.1f}% y estado {top['status']}."
            )

        conversation_id = self.database.ensure_conversation(
            request.conversation_id, request.profile, request.machine_id
        )
        self.database.save_message(conversation_id, "user", request.question)
        payload = {
            "conversation_id": conversation_id,
            "intent": intent,
            "profile": request.profile,
            "summary": summary,
            "recommendation": recommendation,
            "machine": top,
            "operational_impact": operational,
            "financial_impact": financial,
            "explanation_factors": factors,
            "sources": [source],
            "model": {
                "mode": "grounded-local",
                "generative_provider": "optional",
                "data_environment": "simulated-demo",
                "confidence": round(max(0.55, min(0.97, 1 - abs(top["failure_probability"] - 50) / 180)), 2),
            },
            "actions": [
                {"id": "explain_prediction", "label": "Explicar predicción"},
                {"id": "compare_scenarios", "label": "Comparar escenarios"},
                {"id": "preview_work_order", "label": "Preparar orden"},
            ],
            "disclaimer": "Escenario demostrativo con datos simulados. Validar técnicamente antes de ejecutar acciones.",
        }
        self.database.save_message(conversation_id, "assistant", summary, payload)
        self.database.audit("copilot_query", {"question": request.question, "intent": intent}, entity_id=top["machine_id"])
        return payload

    @staticmethod
    def _extract_number(text: str, default: float) -> float:
        match = re.search(r"(\d+(?:[.,]\d+)?)", text)
        return float(match.group(1).replace(",", ".")) if match else default

    def work_order_preview(self, machine_id: str, estimated_cost: float | None = None) -> dict:
        machine_obj = self.simulator.get_by_id(machine_id)
        if not machine_obj:
            raise ValueError("Máquina no encontrada")
        machine = machine_obj.to_dict()
        financial = self._financial(machine)
        payload = {
            "machine_id": machine_id,
            "priority": "critical" if machine["failure_probability"] >= 80 else "high",
            "title": f"Inspección predictiva de {machine_id}",
            "description": (
                f"Validar vibración, temperatura y condición mecánica. Riesgo actual: "
                f"{machine['failure_probability']:.1f}%."
            ),
            "estimated_hours": 3.0,
            "estimated_cost": estimated_cost or financial["intervention_cost"],
            "required_actions": [
                "Inspeccionar rodamientos y elementos rotativos",
                "Validar sensores y calidad de señal",
                "Registrar hallazgos y retroalimentar el modelo",
            ],
        }
        draft = self.database.create_work_order_draft(payload)
        self.database.audit("work_order_draft_created", draft, entity_id=machine_id)
        return draft
