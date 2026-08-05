"""Utilidades para exponer información transparente del modelo predictivo."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "ml" / "model.pkl"
FEATURES = [
    "temperature",
    "vibration",
    "current",
    "pressure",
    "rpm",
    "load",
    "operating_hours",
]


def get_model_report(machine_data: dict[str, Any], visible_risk: float | None = None) -> dict[str, Any]:
    model = joblib.load(MODEL_PATH)
    risk = float(visible_risk if visible_risk is not None else machine_data.get("failure_probability", 0.0))
    if risk < 30:
        classification = "Healthy"
        conclusion = "Operación normal según el umbral del modelo."
    elif risk < 70:
        classification = "Warning"
        conclusion = "El modelo recomienda mantenimiento preventivo."
    else:
        classification = "Critical"
        conclusion = "El modelo detecta alta probabilidad de falla."

    feature_importances = getattr(model, "feature_importances_", None)
    importance_rows = []
    if feature_importances is not None:
        importance_rows = sorted(
            [
                {
                    "feature": feature,
                    "importance": round(float(importance) * 100, 2),
                    "value": machine_data.get(feature),
                }
                for feature, importance in zip(FEATURES, feature_importances)
            ],
            key=lambda row: row["importance"],
            reverse=True,
        )

    modified_at = datetime.fromtimestamp(MODEL_PATH.stat().st_mtime, tz=timezone.utc).isoformat()
    return {
        "model_name": type(model).__name__,
        "model_file": MODEL_PATH.name,
        "model_last_modified": modified_at,
        "features_used": {feature: machine_data.get(feature) for feature in FEATURES},
        "failure_probability": round(risk, 1),
        "classification": classification,
        "model_conclusion": conclusion,
        "decision_thresholds": {
            "healthy": "< 30%",
            "warning": "30% a < 70%",
            "critical": ">= 70%",
        },
        "global_feature_importance": importance_rows,
        "disclaimer": "La probabilidad proviene del modelo predictivo; la recomendación del manual debe ser validada por mantenimiento y seguridad industrial.",
    }
