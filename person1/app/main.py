"""FastAPI application entrypoint for the PRAHARI AI/CV backend.

The model is loaded ONCE during startup via the lifespan context manager.
All routes are thin translation layers around the inference engine.
"""

from __future__ import annotations

import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure the project root is on sys.path so ``app.*`` resolves when run
# with ``python -m uvicorn app.main:app`` from the repo root.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from app.api.anemia import router as anemia_router, set_engine
from app.config import settings

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the inference engine once at startup; clean up on shutdown."""
    log.info("Loading inference engine (model=%s) ...", settings.ai_model)
    try:
        from app.ai.inference import AnemiaInferenceEngine

        eng = AnemiaInferenceEngine()
        eng.load()
        set_engine(eng)
        log.info(
            "Inference engine ready: %s v%s",
            eng.metadata["name"],
            eng.metadata["version"],
        )
    except Exception:
        log.exception("FATAL: failed to load inference engine")
        # Let the app start anyway — /health will report model_loaded=False,
        # and /screen will return 503.  This is better than crashing the
        # whole service during a hackathon demo.
    yield
    log.info("Shutting down.")


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=(
        "PRAHARI Person 1 AI/CV backend — image-based anemia screening "
        "prediction.  This is a research prototype and NOT a clinical "
        "diagnostic tool.  The screening signal is combined with other data "
        "by the PRAHARI multimodal risk engine."
    ),
    lifespan=lifespan,
)

# ---- CORS ----------------------------------------------------------------

_cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
_cors_origins = [o.strip() for o in _cors_origins_str.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- routes --------------------------------------------------------------

app.include_router(anemia_router, prefix="/api/v1")


@app.get("/health", tags=["ops"])
def health() -> dict:
    """Health check — returns model loading status."""
    from app.api.anemia import engine as _eng

    meta = {}
    if _eng is not None:
        meta = {"model": _eng.metadata["name"], "version": _eng.metadata["version"]}
    return {
        "status": "ok" if _eng is not None else "degraded",
        "model_loaded": _eng is not None,
        "model": meta.get("model", "none"),
        "version": meta.get("version", "n/a"),
    }


@app.get("/models", tags=["ops"])
def model_info() -> dict:
    """Metadata about the loaded model (optional endpoint)."""
    from app.api.anemia import engine as _eng

    if _eng is None:
        return {"error": "no model loaded"}
    return {
        "name": _eng.metadata["name"],
        "version": _eng.metadata["version"],
        "type": "sklearn RandomForestClassifier (binary)" if _eng.ai_model == "random_forest" else "MobileNetV2 CNN (binary)",
        "dataset": _eng.metadata["dataset"],
        "labels": ["non_anemic", "anemic"],
        "feature_pipeline": _eng.metadata["feature_pipeline"],
        "training_seed": _eng.metadata["training_seed"],
        "notes": _eng.metadata["notes"],
    }
