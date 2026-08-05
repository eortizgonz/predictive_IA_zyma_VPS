from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api.routes import router

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Manufacturing AI Predictive Dashboard")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.include_router(router)
