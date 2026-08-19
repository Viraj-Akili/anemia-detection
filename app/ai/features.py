"""Interpretable color features for the PRAHARI classical baseline.

Features are computed over **tissue pixels only**: CP-AnemiC raw crops are
RGBA with a transparent background, so the alpha channel acts as a tissue
mask. This avoids diluting the color signal with background/white padding.

Compact, interpretable set (19 features):

RGB (tissue pixels):   R/G/B mean, R/G/B std
LAB (tissue pixels):   L/a*/b* mean, L/a*/b* std
Color ratios:          R/(R+G+B), R-G, R-B   (pallor = reduced redness)
Percentiles:           R p10/p90, a* p10/p90 (color distribution tails)

The extractor is a sklearn transformer so it can live inside a serializable
Pipeline (fit = no-op, transform = extract). Deterministic by construction.

NOTE: these are "features associated with model prediction" for engineering
interpretation — they are NOT claimed to be medical causes of anemia.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from sklearn.base import BaseEstimator, TransformerMixin

FEATURE_NAMES: list[str] = [
    "r_mean", "g_mean", "b_mean",
    "r_std", "g_std", "b_std",
    "l_mean", "a_mean", "b_lab_mean",
    "l_std", "a_std", "b_lab_std",
    "r_ratio", "r_minus_g", "r_minus_b",
    "r_p10", "r_p90", "a_p10", "a_p90",
]

ALPHA_THRESHOLD = 10  # alpha > threshold => tissue pixel


def _tissue_rgb_and_lab(path: str | Path) -> tuple[np.ndarray, np.ndarray]:
    """Return (tissue RGB pixels (N,3) uint8, tissue LAB pixels (N,3) uint8)."""
    with Image.open(path) as im:
        im.load()
        rgba = im.convert("RGBA")
        arr = np.asarray(rgba, dtype=np.uint8)

    mask = arr[..., 3] > ALPHA_THRESHOLD
    if not mask.any():
        # Degenerate image with no opaque pixels: use everything.
        mask = np.ones(arr.shape[:2], dtype=bool)

    rgb = arr[..., :3][mask]
    rgb_img = cv2.cvtColor(arr[..., :3], cv2.COLOR_RGB2BGR)
    lab_img = cv2.cvtColor(rgb_img, cv2.COLOR_BGR2LAB)
    lab = lab_img[mask]
    return rgb, lab


def extract_color_features(path: str | Path) -> np.ndarray:
    """Extract the 19 color features from one image path. Returns float64 (19,)."""
    rgb, lab = _tissue_rgb_and_lab(path)

    r, g, b = (rgb[:, i].astype(np.float64) for i in range(3))
    l_ch, a_ch, b_lab = (lab[:, i].astype(np.float64) for i in range(3))

    rgb_sum = r + g + b
    rgb_sum = np.where(rgb_sum == 0, 1.0, rgb_sum)

    features = np.array(
        [
            r.mean(), g.mean(), b.mean(),
            r.std(), g.std(), b.std(),
            l_ch.mean(), a_ch.mean(), b_lab.mean(),
            l_ch.std(), a_ch.std(), b_lab.std(),
            (r / rgb_sum).mean(),
            (r - g).mean(),
            (r - b).mean(),
            np.percentile(r, 10), np.percentile(r, 90),
            np.percentile(a_ch, 10), np.percentile(a_ch, 90),
        ],
        dtype=np.float64,
    )
    return features


class ColorFeatureExtractor(BaseEstimator, TransformerMixin):
    """sklearn transformer: image paths -> (n, 19) feature matrix.

    ``transform`` accepts a list/array of image paths. ``fit`` is a no-op
    (feature extraction is unsupervised and deterministic).
    """

    def __init__(self, alpha_threshold: int = ALPHA_THRESHOLD):
        self.alpha_threshold = alpha_threshold

    def fit(self, X, y=None):  # noqa: N803 - sklearn signature
        return self

    def transform(self, paths) -> np.ndarray:  # noqa: D102
        return np.vstack([extract_color_features(p) for p in paths])

    def get_feature_names_out(self, input_features=None):  # noqa: D102
        return np.asarray(FEATURE_NAMES, dtype=object)
