"""PRAHARI risk-logic backend — FastAPI application entry point.

Run from the repo root:

    .venv/bin/uvicorn src.main:app --reload

Docs: http://127.0.0.1:8000/docs
Health: http://127.0.0.1:8000/health
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from anthropometry import who_tables
from api.routes.beneficiaries import router as beneficiaries_router
from api.routes.screening import router as screening_router
from models.schemas import HealthResponse

APP_VERSION = "0.1.0"


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Load the WHO primary-source tables into memory at startup so the
    screening pipeline never touches the filesystem lazily."""
    who_tables.preload()
    yield


app = FastAPI(
    title="PRAHARI — Risk / Clinical Logic Backend",
    description=(
        "Early-warning screening backend for anemia & malnutrition risk. "
        "Fuses CV-pipeline output, anthropometry, context, and visit history "
        "into an explainable, safety-railed risk assessment. "
        "Screening only — never a diagnosis."
    ),
    version=APP_VERSION,
    lifespan=lifespan,
)

app.include_router(screening_router, prefix="/api")
app.include_router(beneficiaries_router, prefix="/api")


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="prahari-risk-backend", version=APP_VERSION)
