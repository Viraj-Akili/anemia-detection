"""Production inference engine for the PRAHARI anemia screening signal.

Pipeline (Hour 5):

    image -> validate -> quality gate -> alpha-masked tissue features
           -> saved scaler + classifier -> prediction + probability
           -> structured result

The saved Random Forest pipeline (models/baseline_classifier.joblib)
ALREADY contains feature extraction + scaler + classifier, so no
preprocessing is duplicated here. Features come from the RAW RGBA crop's
alpha-masked tissue pixels (NOT the white-padded 224x224 image).

Usage:

    engine = AnemiaInferenceEngine()
    engine.load()                       # loads the model ONCE
    result = engine.analyze(image)      # full pipeline -> structured dict

Boundary (do not cross): this engine returns an IMAGE-BASED ANEMIA SIGNAL
only. It never computes final risk, severity, WHO rules, or referrals —
those belong to Swayam's multimodal engine.
"""

from __future__ import annotations

import io
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
from PIL import Image, UnidentifiedImageError

from app.ai.errors import (
    ImageCorruptedError,
    ImageQualityLowError,
    ImageTooLargeError,
    InvalidImageError,
    ModelConfigError,
    ModelNotLoadedError,
    UnsupportedImageError,
)
from app.ai.quality_gate import assess_image
from app.config import settings

ANEMIC = "anemic"
NON_ANEMIC = "non_anemic"

# Formats PIL can decode that we accept for screening.
SUPPORTED_FORMATS = {"PNG", "JPEG", "WEBP", "BMP", "TIFF"}

MODEL_METADATA = {
    "random_forest": {
        "name": "random_forest_color_baseline",
        "version": "1.0",
        "dataset": "CP-AnemiC (Mendeley 10.17632/m53vz6b7fx.1)",
        "feature_pipeline": "alpha-masked RGB/LAB tissue features (19) + StandardScaler",
        "training_seed": 42,
        "notes": "non-clinical model version; screening research prototype",
    },
    "cnn": {
        "name": "mobilenet_v2_cnn",
        "version": "1.0",
        "dataset": "CP-AnemiC (Mendeley 10.17632/m53vz6b7fx.1)",
        "feature_pipeline": "224x224 RGB white-padded crop -> ImageNet normalize -> MobileNetV2",
        "training_seed": 42,
        "notes": "secondary fallback; faster but less accurate than random_forest",
    },
}


@dataclass(frozen=True)
class AnemiaPrediction:
    label: str          # "anemic" | "non_anemic" (dataset labels)
    probability: float  # model probability of the anemic class (0-1)
    confidence: float   # model probability for the predicted class (0-1)
    model_name: str


class BaselineClassifier:
    """Thin wrapper around the saved sklearn pipeline (kept for compatibility)."""

    def __init__(self, model_path: str | Path | None = None):
        self.model_path = Path(model_path or settings.model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"model not found at {self.model_path}. Run scripts/train_baseline.py first."
            )
        self.pipeline = joblib.load(self.model_path)
        clf = self.pipeline.named_steps.get("clf")
        if clf is not None and hasattr(clf, "n_jobs"):
            clf.n_jobs = 1  # avoid ~70ms loky per-call overhead on Windows
        self._classes = list(self.pipeline.classes_)
        self._pos_idx = self._classes.index(ANEMIC)

    def predict(self, image_path: str | Path) -> AnemiaPrediction:
        proba = self.pipeline.predict_proba([str(image_path)])[0]
        p_anemic = float(proba[self._pos_idx])
        label = ANEMIC if p_anemic >= settings.confidence_threshold else NON_ANEMIC
        return AnemiaPrediction(
            label=label,
            probability=p_anemic,
            confidence=float(max(proba)),
            model_name="baseline_random_forest",
        )

    def predict_proba(self, image_path: str | Path) -> np.ndarray:
        return self.pipeline.predict_proba([str(image_path)])[0]


class AnemiaInferenceEngine:
    """Full pipeline: validate -> quality gate -> features -> model -> result.

    The model is loaded exactly once by ``load()`` (idempotent). ``analyze``
    returns a structured dict (including quality-rejected results); hard
    input failures raise typed errors from app.ai.errors.
    """

    def __init__(
        self,
        model_path: str | Path | None = None,
        ai_model: str | None = None,
        confidence_threshold: float | None = None,
        max_image_size: int | None = None,
    ):
        self.ai_model = (ai_model or settings.ai_model or "random_forest").lower()
        if self.ai_model not in MODEL_METADATA:
            raise ModelConfigError(
                f"unknown AI_MODEL {self.ai_model!r}; choose from {sorted(MODEL_METADATA)}"
            )
        self.model_path = Path(model_path or (
            settings.model_path if self.ai_model == "random_forest" else settings.cnn_model_path
        ))
        self.confidence_threshold = confidence_threshold if confidence_threshold is not None else settings.confidence_threshold
        self.max_image_size = max_image_size or settings.max_image_size
        self.metadata = MODEL_METADATA[self.ai_model]
        self._pipeline = None      # RF: sklearn pipeline
        self._cnn = None           # CNN: torch model
        self._cnn_transform = None

    # ------------------------------------------------------------------ load
    def load(self) -> "AnemiaInferenceEngine":
        """Load the model once. Idempotent. Returns self."""
        if self._pipeline is not None or self._cnn is not None:
            return self
        if not self.model_path.exists():
            raise ModelNotLoadedError(
                f"model not found at {self.model_path}. "
                + ("Run scripts/train_baseline.py first." if self.ai_model == "random_forest"
                   else "Run scripts/train_cnn.py first.")
            )
        if self.ai_model == "random_forest":
            self._pipeline = joblib.load(self.model_path)
            # The RF was trained with n_jobs=-1; per-call loky pool overhead on
            # Windows costs ~70ms for a single-sample predict. n_jobs=1 keeps the
            # identical trees and makes single-image inference fast (measured
            # ~0.2ms/image on a batch; the residual ~20ms is sklearn call overhead).
            clf = self._pipeline.named_steps.get("clf")
            if clf is not None and hasattr(clf, "n_jobs"):
                clf.n_jobs = 1
            self._classes = list(self._pipeline.classes_)
            self._pos_idx = self._classes.index(ANEMIC)
        else:
            import torch
            from app.ai.cnn_model import load_checkpoint
            from app.ai.dataset import eval_transform

            self._cnn = load_checkpoint(self.model_path, device=settings.resolve_device())
            self._cnn.eval()
            self._cnn_transform = eval_transform()
        object.__setattr__(settings, "model_loaded", True)
        return self

    # ------------------------------------------------------------- image prep
    def _load_image(self, image) -> tuple[Image.Image, str | None, bool]:
        """Decode + basic-validate an image.

        Accepts: path (str/Path), PIL Image, or raw bytes.
        Returns (pil_image, path_for_features, is_temp_path).
        Raises typed errors for invalid/corrupt/unsupported/oversized input.
        """
        pil_image: Image.Image | None = None
        temp_path: str | None = None
        is_temp = False
        try:
            if isinstance(image, (str, Path)):
                path = Path(image)
                if not path.exists():
                    raise InvalidImageError(f"image does not exist: {path}")
                try:
                    pil_image = Image.open(path)
                    pil_image.load()
                except (UnidentifiedImageError, OSError) as exc:
                    raise ImageCorruptedError(f"cannot decode image: {path}") from exc
                feature_path = str(path)
            elif isinstance(image, Image.Image):
                pil_image = image
                feature_path = None
            elif isinstance(image, (bytes, bytearray)):
                try:
                    pil_image = Image.open(io.BytesIO(bytes(image)))
                    pil_image.load()
                except (UnidentifiedImageError, OSError) as exc:
                    raise ImageCorruptedError("cannot decode image bytes") from exc
                feature_path = None
            else:
                raise InvalidImageError(
                    f"unsupported input type {type(image).__name__}; expected path, PIL Image or bytes"
                )

            if pil_image.format and pil_image.format.upper() not in SUPPORTED_FORMATS:
                raise UnsupportedImageError(
                    f"unsupported format {pil_image.format!r}; supported: {sorted(SUPPORTED_FORMATS)}"
                )
            if pil_image.mode not in ("RGB", "RGBA", "L", "LA", "P"):
                raise UnsupportedImageError(f"unsupported image mode {pil_image.mode!r}")

            w, h = pil_image.size
            if max(w, h) > self.max_image_size:
                raise ImageTooLargeError(
                    f"image {w}x{h} exceeds max side {self.max_image_size}px"
                )
            if min(w, h) < 8:
                raise InvalidImageError(f"image {w}x{h} is too small to screen")

            # Model feature extraction needs a file path: materialize temp file.
            if feature_path is None:
                fd, temp_path = tempfile.mkstemp(suffix=".png")
                import os

                os.close(fd)
                pil_image.save(temp_path, format="PNG")
                feature_path = temp_path
                is_temp = True
            return pil_image, feature_path, is_temp
        except Exception:
            if temp_path:
                Path(temp_path).unlink(missing_ok=True)
            raise

    # -------------------------------------------------------------- predict
    def predict(self, image) -> AnemiaPrediction:
        """Validate + quality-gate + predict. Raises ImageQualityLowError on poor quality."""
        if self._pipeline is None and self._cnn is None:
            raise ModelNotLoadedError("engine not loaded; call load() first")

        pil_image, feature_path, is_temp = self._load_image(image)
        try:
            quality = assess_image(
                pil_image,
                min_brightness=settings.quality_min_brightness,
                max_brightness=settings.quality_max_brightness,
                min_contrast=settings.quality_min_contrast,
                min_sharpness=settings.quality_min_sharpness,
                min_resolution=settings.quality_min_resolution,
                min_tissue_fraction=settings.quality_min_tissue_fraction,
            )
            if not quality.passed:
                raise ImageQualityLowError(
                    "Image quality is insufficient. Please retake the image."
                )

            p_anemic, _ = self._run_model(feature_path)
            label = ANEMIC if p_anemic >= self.confidence_threshold else NON_ANEMIC
            return AnemiaPrediction(
                label=label,
                probability=float(p_anemic),
                confidence=float(max(p_anemic, 1.0 - p_anemic)),
                model_name=self.metadata["name"],
            )
        finally:
            if is_temp:
                Path(feature_path).unlink(missing_ok=True)

    # --------------------------------------------------------------- analyze
    def analyze(self, image) -> dict:
        """Full pipeline with latency breakdown and structured result.

        Never raises for low quality (returns success=False); raises typed
        errors for invalid/corrupt/oversized/unsupported input and when the
        model is not loaded.
        """
        if self._pipeline is None and self._cnn is None:
            raise ModelNotLoadedError("engine not loaded; call load() first")

        timings: dict[str, float] = {}
        t0 = time.perf_counter()

        pil_image, feature_path, is_temp = self._load_image(image)
        timings["decode_ms"] = (time.perf_counter() - t0) * 1000.0
        try:
            t1 = time.perf_counter()
            quality = assess_image(
                pil_image,
                min_brightness=settings.quality_min_brightness,
                max_brightness=settings.quality_max_brightness,
                min_contrast=settings.quality_min_contrast,
                min_sharpness=settings.quality_min_sharpness,
                min_resolution=settings.quality_min_resolution,
                min_tissue_fraction=settings.quality_min_tissue_fraction,
            )
            timings["quality_ms"] = (time.perf_counter() - t1) * 1000.0

            quality_payload = {
                "status": quality.status,
                "score": quality.score,
                "checks": quality.checks,
                "reasons": quality.reasons,
            }

            if not quality.passed:
                return {
                    "success": False,
                    "prediction": None,
                    "image_quality": quality_payload,
                    "inference": None,
                    "error": {
                        "code": ImageQualityLowError.code,
                        "message": "Image quality is insufficient. Please retake the image.",
                    },
                    "timings_ms": {**timings, "total_ms": (time.perf_counter() - t0) * 1000.0},
                }

            t2 = time.perf_counter()
            p_anemic, model_ms = self._run_model(feature_path)
            timings["features_ms"] = model_ms
            timings["predict_ms"] = model_ms

            label = ANEMIC if p_anemic >= self.confidence_threshold else NON_ANEMIC
            return {
                "success": True,
                "prediction": {
                    "label": label,
                    "model_probability": round(float(p_anemic), 4),
                    "model_confidence": round(float(max(p_anemic, 1.0 - p_anemic)), 4),
                },
                "image_quality": quality_payload,
                "inference": {
                    "model": self.metadata["name"],
                    "version": self.metadata["version"],
                    "model_path": str(self.model_path),
                    "dataset": self.metadata["dataset"],
                    "latency_ms": round((time.perf_counter() - t0) * 1000.0, 3),
                },
                "timings_ms": {k: round(v, 3) for k, v in {**timings, "total_ms": (time.perf_counter() - t0) * 1000.0}.items()},
            }
        finally:
            if is_temp:
                Path(feature_path).unlink(missing_ok=True)

    # ------------------------------------------------------------ internals
    def _run_model(self, feature_path: str) -> tuple[float, float]:
        """Return (p_anemic, model_time_ms)."""
        t0 = time.perf_counter()
        if self._pipeline is not None:
            proba = self._pipeline.predict_proba([feature_path])[0]
            p_anemic = float(proba[self._pos_idx])
        else:
            import torch
            from PIL import Image as PILImage

            img = PILImage.open(feature_path).convert("RGB")
            x = self._cnn_transform(img).unsqueeze(0)
            with torch.inference_mode():
                logit = self._cnn(x.to(next(self._cnn.parameters()).device))
                p_anemic = float(torch.sigmoid(logit).item())
        return p_anemic, (time.perf_counter() - t0) * 1000.0
