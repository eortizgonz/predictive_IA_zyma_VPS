"""
Configuración general del proyecto
"""

import os

# ------------------------------------------------------------------
# Información de la aplicación
# ------------------------------------------------------------------

APP_NAME = "Manufacturing AI Predictive Dashboard"

VERSION = "1.0.0"

# ------------------------------------------------------------------
# Directorios
# ------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_FOLDER = os.path.join(BASE_DIR, "data")

MODEL_FILE = os.path.join(BASE_DIR, "model.pkl")

HISTORICAL_DATA = os.path.join(DATA_FOLDER, "historical_data.csv")

# ------------------------------------------------------------------
# Simulación
# ------------------------------------------------------------------

NUMBER_OF_MACHINES = 20

REFRESH_SECONDS = 3

# ------------------------------------------------------------------
# Machine Learning
# ------------------------------------------------------------------

RANDOM_STATE = 42

TEST_SIZE = 0.20