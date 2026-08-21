from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .config import settings
from .database import Base, engine
from .models import *  # noqa: F403
from .routers import (
    beneficiaries_router,
    screenings_router,
    measurements_router,
    results_router,
    followups_router,
    history_router,
    nutrition_router,
)

app = FastAPI(title="PRAHARI Backend")

@app.on_event("startup")
def on_startup():
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        pass

# CORS for local frontend development (React on 3000, Vite on 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(beneficiaries_router)
app.include_router(screenings_router)
app.include_router(measurements_router)
app.include_router(results_router)
app.include_router(followups_router)
app.include_router(history_router)
app.include_router(nutrition_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "PRAHARI Backend"}


@app.get("/health/db")
def health_db(response: Response) -> dict[str, str]:
    """Perform an actual PostgreSQL connectivity check (SELECT 1)."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 - report the real connection problem
        response.status_code = 503
        return {
            "status": "error",
            "database": "disconnected",
            "detail": str(exc),
        }
    return {"status": "ok", "database": "connected"}
