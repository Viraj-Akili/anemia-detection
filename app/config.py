"""Central configuration for the PRAHARI AI/CV backend.

All values are overridable via environment variables (see .env.example).
No machine-specific paths are hardcoded here.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Project root = parent of this file's directory (app/../)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _env(key: str, default: str) -> str:
    return os.getenv(key, default)


@dataclass(frozen=True)
class Settings:
    # --- Paths -----------------------------------------------------------
    model_path: Path = field(
        default_factory=lambda: Path(_env("ANEMIA_MODEL_PATH", "models/baseline_classifier.joblib"))
    )
    cnn_model_path: Path = field(
        default_factory=lambda: Path(_env("ANEMIA_CNN_MODEL_PATH", "models/mobilenetv2_best.pth"))
    )
    data_raw_dir: Path = field(
        default_factory=lambda: Path(_env("DATA_RAW_DIR", "data/raw"))
    )
    data_processed_dir: Path = field(
        default_factory=lambda: Path(_env("DATA_PROCESSED_DIR", "data/processed"))
    )

    # --- Image handling ---------------------------------------------------
    image_size: int = int(_env("IMAGE_SIZE", "224"))          # model input (square)
    max_image_size: int = int(_env("MAX_IMAGE_SIZE", "4096"))  # long-side cap, px

    # --- Quality gate thresholds ------------------------------------------
    # Defaults calibrated against actual CP-AnemiC data (Hour 2): observed
    # brightness 173-249, contrast 15-98, sharpness 70-3492, tissue 0.08-0.48.
    quality_min_brightness: float = float(_env("QUALITY_MIN_BRIGHTNESS", "30"))   # mean pixel value 0-255
    quality_max_brightness: float = float(_env("QUALITY_MAX_BRIGHTNESS", "250"))
    quality_min_sharpness: float = float(_env("QUALITY_MIN_SHARPNESS", "50"))     # Laplacian variance
    quality_min_contrast: float = float(_env("QUALITY_MIN_CONTRAST", "10"))       # std of grayscale
    quality_min_tissue_fraction: float = float(_env("QUALITY_MIN_TISSUE_FRACTION", "0.10"))  # alpha coverage
    quality_min_resolution: int = int(_env("QUALITY_MIN_RESOLUTION", "16"))  # min side, px

    # --- Data pipeline -------------------------------------------------------
    data_seed: int = int(_env("DATA_SEED", "42"))  # deterministic split seed (see dataset_summary.json)

    # --- Model -------------------------------------------------------------
    device: str = _env("DEVICE", "auto")  # "auto" | "cuda" | "cpu"
    model_version: str = _env("MODEL_VERSION", "0.1.0-dev")
    confidence_threshold: float = float(_env("CONFIDENCE_THRESHOLD", "0.5"))
    ai_model: str = _env("AI_MODEL", "random_forest")  # "random_forest" (primary) | "cnn" (fallback)

    # --- API ---------------------------------------------------------------
    api_title: str = _env("API_TITLE", "PRAHARI Anemia Screening API")
    api_version: str = _env("API_VERSION", "0.1.0")
    max_upload_size_mb: int = int(_env("MAX_IMAGE_SIZE_MB", "4"))  # upload safety limit (MB)

    # --- Runtime state (populated at load time, not from env) ----------------
    model_loaded: bool = False

    def resolve_device(self) -> str:
        """Resolve 'auto' to the best available device."""
        if self.device != "auto":
            return self.device
        try:
            import torch

            return "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            return "cpu"


settings = Settings()
