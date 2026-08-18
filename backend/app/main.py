from fastapi import FastAPI, Response
from sqlalchemy import text

from .config import settings
from .database import engine

app = FastAPI(title="PRAHARI Backend")


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
