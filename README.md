# Manufacturing AI Predictive Dashboard

Proyecto desarrollado para demostrar Machine Learning aplicado a mantenimiento predictivo.

---

## Tecnologías

- Python
- FastAPI
- Scikit-Learn
- Plotly
- Bootstrap
- Pandas
- NumPy

---

## Instalación

Crear entorno virtual

Windows

```bash
python -m venv .venv
```

Activar

```bash
.venv\Scripts\activate
```

Instalar dependencias

```bash
pip install -r requirements.txt
```

Ejecutar

```bash
uvicorn app:app --reload
```

Abrir

http://127.0.0.1:8000

---

## Funcionalidades

- Dashboard Industrial
- KPIs
- Predicción de Fallas
- Machine Learning
- Simulación de Sensores
- Gráficas en Tiempo Real
## Predictive Copilot

The dashboard now includes an executive chat interface for Operations, Finance, and Technology. It provides:

- Conversation history
- Free-text questions
- Quick questions by profile
- Machine selector
- Profile selector
- "Analyzing data" status
- Predictive cards based on current machine data
- Integration with the existing local AI diagnostic endpoint

The current Copilot is a demonstrative rule-based interface connected to the simulator. Financial calculations require client-specific cost and production parameters in a later phase.
