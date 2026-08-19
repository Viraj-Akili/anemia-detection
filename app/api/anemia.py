"""Anemia screening endpoint.

POST /api/v1/anemia/screen
  multipart/form-data  { image: <file> }
  → 200  success: true  + prediction + quality + inference metadata
  → 200  success: false + quality rejection + error code  (quality gate)
  → 4xx/5xx for hard failures (invalid, corrupt, oversized, model down)

The route is a THIN translation layer — all logic lives in
``AnemiaInferenceEngine`` (app/ai/inference.py).  No inference,
preprocessing, or model logic belongs here.
"""

from __future__ import annotations

import logging
import time

from fastapi import APIRouter, File, UploadFile, HTTPException

from app.ai.errors import InferenceError
from app.ai.inference import AnemiaInferenceEngine, SUPPORTED_FORMATS
from app.config import settings

log = logging.getLogger(__name__)

router = APIRouter(prefix="/anemia", tags=["anemia"])

# Module-level engine (populated at startup via lifespan in main.py).
# Do NOT load the model here — that is main.py's responsibility.
engine: AnemiaInferenceEngine | None = None


def set_engine(e: AnemiaInferenceEngine) -> None:
    """Called by the application lifespan after model loading."""
    global engine
    engine = e


# ---- helpers -------------------------------------------------------------

_MAX_UPLOAD_BYTES = settings.max_image_size  # reuse existing config
_MIN_UPLOAD_BYTES = 100  # anything smaller is almost certainly broken
_ALLOWED_MIMES = {
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/bmp",
    "image/tiff",
}


def _ensure_engine() -> AnemiaInferenceEngine:
    if engine is None:
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "error": {
                    "code": "MODEL_NOT_LOADED",
                    "message": "The screening model is not loaded. The service may be starting up.",
                },
            },
        )
    return engine


# ---- endpoint ------------------------------------------------------------

@router.post(
    "/screen",
    summary="Anemia screening prediction",
    description=(
        "Upload a conjunctival (eye) image for an image-based anemia "
        "screening prediction.  This is a research prototype and is NOT a "
        "clinical diagnostic tool.  The prediction is an image-based signal "
        "only; final risk determination combines this with other data in the "
        "PRAHARI multimodal engine."
    ),
    response_description="Structured screening result with prediction, quality assessment, and inference metadata.",
    status_code=200,
)
async def screen_anemia(
    image: UploadFile = File(
        ...,
        description="Conjunctival image (PNG, JPEG, WebP, BMP, TIFF).  Max size is configurable via MAX_IMAGE_SIZE_MB.",
    ),
) -> dict:
    """Screen a conjunctival image for anemia risk signal."""
    t0 = time.perf_counter()
    eng = _ensure_engine()

    # --- upload validation ------------------------------------------------
    if image.content_type and image.content_type not in _ALLOWED_MIMES:
        raise HTTPException(
            status_code=415,
            detail={
                "success": False,
                "error": {
                    "code": "UNSUPPORTED_IMAGE",
                    "message": f"Unsupported content type '{image.content_type}'.  "
                    f"Supported: {', '.join(sorted(_ALLOWED_MIMES))}.",
                },
            },
        )

    try:
        raw = await image.read()
    except Exception as exc:
        log.warning("Failed to read uploaded file: %s", exc)
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_IMAGE",
                    "message": "Could not read the uploaded file.",
                },
            },
        )

    if len(raw) < _MIN_UPLOAD_BYTES:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_IMAGE",
                    "message": "Uploaded file is empty or too small to be a valid image.",
                },
            },
        )

    if len(raw) > _MAX_UPLOAD_BYTES * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail={
                "success": False,
                "error": {
                    "code": "IMAGE_TOO_LARGE",
                    "message": f"Image exceeds the maximum upload size of {_MAX_UPLOAD_BYTES} MB.",
                },
            },
        )

    # --- inference --------------------------------------------------------
    try:
        result = eng.analyze(raw)
    except InferenceError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "success": False,
                "error": {
                    "code": exc.code,
                    "message": str(exc),
                },
            },
        )
    except Exception as exc:
        log.exception("Unexpected error during inference")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": "INFERENCE_FAILED",
                    "message": "An unexpected error occurred during screening.",
                },
            },
        )

    api_ms = (time.perf_counter() - t0) * 1000.0
    result["api_latency_ms"] = round(api_ms, 3)

    # Strip internal fields the engine adds (model_path, timings breakdown)
    # that aren't part of the public contract.
    if "timings_ms" in result:
        del result["timings_ms"]
    if "inference" in result and result["inference"] and "model_path" in result["inference"]:
        del result["inference"]["model_path"]

    return result
