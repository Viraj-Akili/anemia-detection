"""Quality gate for the PRAHARI anemia pipeline.

Assesses whether an image is usable for screening and returns a
QualityResult with a pass/fail verdict, per-check status, a 0-1 score and
reasons. Thresholds live in app/config.py and are calibrated against the
actual CP-AnemiC data (see data/dataset_validation.csv for the observed
distributions):

- brightness 173-249 (min/max defaults 30/250 are intentionally lenient)
- contrast 15-98    (default 10)
- sharpness 70-3492 (default 50)
- tissue coverage 0.08-0.48 (default 0.10)

IMPORTANT (Hour 5): these thresholds are deliberately lenient — the dataset
itself contains the range of acceptable field-captured images. Tightening
them would require new labeled data or model-driven calibration; arbitrary
medical thresholds are NOT invented here.

Score: starts at 1.0 and subtracts a fixed penalty per failed check
(weights below). This is an engineering score for prioritizing retakes,
not a clinical measure.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import cv2
import numpy as np
from PIL import Image

from app.ai.preprocessing import load_rgb

# Penalty per failed check (sum <= 1.0). Engineering weights, not clinical.
CHECK_PENALTIES = {
    "blur": 0.35,
    "too_dark": 0.25,
    "too_bright": 0.15,
    "low_contrast": 0.15,
    "low_resolution": 0.20,
    "low_tissue": 0.15,
}


@dataclass
class QualityResult:
    passed: bool
    checks: dict[str, str] = field(default_factory=dict)  # check name -> "pass" | "fail"
    reasons: list[str] = field(default_factory=list)
    score: float = 1.0
    metrics: dict[str, float] = field(default_factory=dict)

    @property
    def status(self) -> str:
        return "good" if self.passed else "poor"

    def __str__(self) -> str:  # pragma: no cover - convenience
        return f"QualityResult(status={self.status}, score={self.score:.2f}, reasons={self.reasons})"


def _to_rgb_array(image: Image.Image | np.ndarray) -> np.ndarray:
    """RGBA images are alpha-composited over white before metric computation.

    Converting RGBA->RGB by dropping alpha would count transparent pixels'
    underlying (often black) RGB values, dragging brightness down and
    wrongly rejecting real dataset crops.
    """
    if isinstance(image, Image.Image):
        if "A" in image.getbands():
            rgba = image.convert("RGBA")
            background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
            composited = Image.alpha_composite(background, rgba).convert("RGB")
        else:
            composited = image.convert("RGB")
        return np.asarray(composited, dtype=np.uint8)
    return np.asarray(image, dtype=np.uint8)


def compute_metrics(image: Image.Image | np.ndarray) -> dict[str, float]:
    """Compute quality metrics from an RGB/RGBA PIL image or uint8 array."""
    arr = _to_rgb_array(image)
    if arr.ndim != 3 or arr.shape[2] != 3:
        raise ValueError(f"expected RGB image, got shape {arr.shape}")

    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    h, w = gray.shape
    return {
        "brightness": float(gray.mean()),
        "contrast": float(gray.std()),
        "sharpness": float(laplacian.var()),
        "width": int(w),
        "height": int(h),
    }


def assess_image(
    image: Image.Image | np.ndarray,
    min_brightness: float = 30.0,
    max_brightness: float = 250.0,
    min_contrast: float = 10.0,
    min_sharpness: float = 50.0,
    min_resolution: float = 16.0,
    min_tissue_fraction: float = 0.10,
) -> QualityResult:
    """Assess an image against the quality thresholds.

    Threshold defaults mirror app/config.py; pass explicit values to
    override. Returns a QualityResult with per-check status, score and
    reasons.
    """
    metrics = compute_metrics(image)
    checks: dict[str, str] = {}
    reasons: list[str] = []

    def check(name: str, ok: bool) -> None:
        checks[name] = "pass" if ok else "fail"
        if not ok:
            reasons.append(name)

    check("blur", metrics["sharpness"] >= min_sharpness)
    check("brightness", min_brightness <= metrics["brightness"] <= max_brightness)
    check("contrast", metrics["contrast"] >= min_contrast)
    check("resolution", min(metrics["width"], metrics["height"]) >= min_resolution)

    # Tissue availability (only meaningful for RGBA/alpha images).
    tissue = None
    if isinstance(image, Image.Image) and "A" in image.getbands():
        tissue = tissue_coverage(image)
        metrics["tissue_fraction"] = tissue
        check("tissue", tissue >= min_tissue_fraction)

    score = 1.0 - sum(CHECK_PENALTIES.get(name, 0.0) for name in reasons)
    score = round(float(max(0.0, min(1.0, score))), 4)

    return QualityResult(
        passed=len(reasons) == 0,
        checks=checks,
        reasons=reasons,
        score=score,
        metrics=metrics,
    )


def tissue_coverage(image: Image.Image) -> float:
    """Fraction of non-transparent pixels (alpha > 10) in a (possibly RGBA) image.

    Low values mean the crop contains very little actual conjunctiva tissue.
    """
    rgba = image.convert("RGBA")
    arr = np.asarray(rgba)
    return float((arr[..., 3] > 10).mean())
