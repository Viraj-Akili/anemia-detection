"""Tests for app/ai/features.py (Hour 3)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from app.ai.features import FEATURE_NAMES, ColorFeatureExtractor, extract_color_features


@pytest.fixture()
def opaque_rgba(tmp_path: Path) -> Path:
    """Small RGBA crop with fully opaque reddish pixels (conjunctiva-like)."""
    p = tmp_path / "img.png"
    arr = np.zeros((40, 80, 4), dtype=np.uint8)
    arr[..., 0] = 200  # R
    arr[..., 1] = 100  # G
    arr[..., 2] = 100  # B
    arr[..., 3] = 255  # alpha
    Image.fromarray(arr, mode="RGBA").save(p)
    return p


@pytest.fixture()
def transparent_bg(tmp_path: Path) -> Path:
    """RGBA crop where the background is transparent, tissue in the middle."""
    p = tmp_path / "img2.png"
    arr = np.zeros((50, 50, 4), dtype=np.uint8)
    arr[..., 3] = 0                      # transparent everywhere
    arr[10:40, 10:40, :3] = (180, 120, 110)
    arr[10:40, 10:40, 3] = 255           # opaque tissue block
    Image.fromarray(arr, mode="RGBA").save(p)
    return p


def test_feature_names_length():
    assert len(FEATURE_NAMES) == 19
    assert len(set(FEATURE_NAMES)) == 19


def test_extract_shape(opaque_rgba):
    feats = extract_color_features(opaque_rgba)
    assert feats.shape == (19,)
    assert feats.dtype == np.float64


def test_extract_deterministic(opaque_rgba):
    a = extract_color_features(opaque_rgba)
    b = extract_color_features(opaque_rgba)
    np.testing.assert_array_equal(a, b)


def test_no_nan(opaque_rgba, transparent_bg):
    for p in (opaque_rgba, transparent_bg):
        assert not np.isnan(extract_color_features(p)).any()


def test_tissue_masking_ignores_transparent_background(transparent_bg):
    # Background is transparent; features must reflect the tissue block only.
    feats = extract_color_features(transparent_bg)
    # Tissue is reddish: R mean should exceed B mean.
    assert feats[FEATURE_NAMES.index("r_mean")] > feats[FEATURE_NAMES.index("b_mean")]


def test_reddish_tissue_scores_higher_on_redness(transparent_bg):
    red = extract_color_features(transparent_bg)
    # a* (LAB red-green axis) should be positive for reddish tissue.
    assert red[FEATURE_NAMES.index("a_mean")] > 120  # LAB a* of (180,120,110) > 120


def test_transformer_shape(opaque_rgba, transparent_bg):
    t = ColorFeatureExtractor()
    X = t.fit_transform([str(opaque_rgba), str(transparent_bg)])
    assert X.shape == (2, 19)
    assert not np.isnan(X).any()


def test_transformer_deterministic(opaque_rgba):
    t = ColorFeatureExtractor()
    X1 = t.fit_transform([str(opaque_rgba)])
    X2 = t.fit_transform([str(opaque_rgba)])
    np.testing.assert_array_equal(X1, X2)
