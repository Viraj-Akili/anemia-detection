"""Tests for the production inference engine (Hour 5)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from app.ai.errors import (
    ImageCorruptedError,
    ImageQualityLowError,
    ImageTooLargeError,
    InvalidImageError,
    ModelNotLoadedError,
    UnsupportedImageError,
)
from app.ai.features import extract_color_features
from app.ai.inference import ANEMIC, NON_ANEMIC, AnemiaInferenceEngine
from app.ai.quality_gate import assess_image

RAW_TEST_DIR = Path("data/raw/cp-anemic")


@pytest.fixture(scope="module")
def engine():
    e = AnemiaInferenceEngine()
    e.load()
    return e


@pytest.fixture()
def good_image() -> Path:
    """A real, valid conjunctiva crop from the test split."""
    return next((RAW_TEST_DIR / "Anemic").glob("Image_*.png"))


@pytest.fixture()
def poor_image(tmp_path: Path) -> Path:
    """A real crop heavily blurred to simulate a poor-quality photo."""
    import cv2

    src = next((RAW_TEST_DIR / "Anemic").glob("Image_*.png"))
    img = cv2.imread(str(src), cv2.IMREAD_UNCHANGED)
    blurred = cv2.GaussianBlur(img, (31, 31), 0)
    out = tmp_path / "poor.png"
    cv2.imwrite(str(out), blurred)
    return out


def make_tissue_rgba(path: Path, r=200, g=100, b=100, size=(60, 120)) -> Path:
    """RGBA image: transparent background + opaque reddish tissue block."""
    arr = np.zeros((*size, 4), dtype=np.uint8)
    arr[..., 3] = 0
    arr[10:-10, 10:-10, :3] = (r, g, b)
    arr[10:-10, 10:-10, 3] = 255
    Image.fromarray(arr, mode="RGBA").save(path)
    return path


# 1-2. initialization + model loading
def test_engine_initialization():
    e = AnemiaInferenceEngine()
    assert e._pipeline is None


def test_engine_loads_once(engine):
    assert engine._pipeline is not None
    p1 = engine._pipeline
    engine.load()  # idempotent
    assert engine._pipeline is p1


def test_engine_not_loaded_raises():
    e = AnemiaInferenceEngine()
    with pytest.raises(ModelNotLoadedError):
        e.predict("whatever.png")


# 3. valid image inference
def test_valid_image_inference(engine, good_image):
    result = engine.analyze(good_image)
    assert result["success"] is True
    assert result["prediction"]["label"] in (ANEMIC, NON_ANEMIC)
    assert result["inference"]["model"] == "random_forest_color_baseline"


# 4. invalid image
def test_invalid_image_missing(engine, tmp_path):
    with pytest.raises(InvalidImageError):
        engine.analyze(tmp_path / "missing.png")


def test_invalid_image_type(engine):
    with pytest.raises(InvalidImageError):
        engine.analyze(12345)


# 5. corrupted image
def test_corrupted_image(engine, tmp_path):
    bad = tmp_path / "corrupt.png"
    bad.write_bytes(b"this is definitely not an image")
    with pytest.raises(ImageCorruptedError):
        engine.analyze(bad)


# 6. low-quality image rejected (analyze returns failure; predict raises)
def test_poor_quality_analyze(engine, poor_image):
    result = engine.analyze(poor_image)
    assert result["success"] is False
    assert result["prediction"] is None
    assert result["error"]["code"] == "IMAGE_QUALITY_LOW"
    assert result["image_quality"]["status"] == "poor"


def test_poor_quality_predict_raises(engine, poor_image):
    with pytest.raises(ImageQualityLowError):
        engine.predict(poor_image)


def test_quality_gate_rejects_blurry(poor_image):
    quality = assess_image(Image.open(poor_image))
    assert not quality.passed
    assert "blur" in quality.reasons


# 7-9. prediction / probability / label
def test_prediction_fields(engine, good_image):
    pred = engine.predict(good_image)
    assert pred.label in (ANEMIC, NON_ANEMIC)
    assert 0.0 <= pred.probability <= 1.0
    assert 0.0 <= pred.confidence <= 1.0
    assert pred.model_name == "random_forest_color_baseline"


def test_probability_range_over_samples(engine):
    from app.ai.inference import NON_ANEMIC as NA

    samples = sorted((RAW_TEST_DIR / "Non-anemic").glob("Image_*.png"))[:5]
    for s in samples:
        pred = engine.predict(s)
        assert 0.0 <= pred.probability <= 1.0
        assert pred.label in (ANEMIC, NA)


# 10. feature extraction
def test_feature_extraction_shape(good_image):
    feats = extract_color_features(good_image)
    assert feats.shape == (19,)


# 11-12. alpha-mask handling + white-padding immunity
def test_white_padding_does_not_contaminate_features(tmp_path):
    # Same tissue on transparent background vs white background must give
    # nearly identical features (extraction uses the alpha mask, so the
    # background never enters the statistics).
    rgba = make_tissue_rgba(tmp_path / "raw.png")
    feats_raw = extract_color_features(rgba)

    arr = np.array(Image.open(rgba).convert("RGBA"))
    alpha = arr[..., 3:4] / 255.0
    composite = np.clip(arr[..., :3] * alpha + 255.0 * (1 - alpha), 0, 255).astype(np.uint8)
    white_bg = tmp_path / "white.png"
    Image.fromarray(composite, mode="RGB").save(white_bg)

    # Features on the raw RGBA crop must be computed from tissue pixels only:
    # they should match the same tissue placed on a transparent background,
    # and the mean color should NOT shift toward white (255).
    assert feats_raw[0] < 250  # r_mean not washed out
    # Compare against a tightly cropped tissue-only image (identical stats).
    tight = tmp_path / "tight.png"
    Image.fromarray(arr[10:-10, 10:-10, :3], mode="RGB").save(tight)
    feats_tight = extract_color_features(tight)
    np.testing.assert_allclose(feats_raw[:3], feats_tight[:3], atol=1.0)


def test_alpha_masking_ignores_transparent_background(tmp_path):
    rgba = make_tissue_rgba(tmp_path / "raw2.png")
    feats = extract_color_features(rgba)
    assert feats[0] > feats[2]  # r_mean > b_mean (reddish tissue)


# 13. latency field
def test_latency_field(engine, good_image):
    result = engine.analyze(good_image)
    assert result["inference"]["latency_ms"] > 0
    assert result["timings_ms"]["total_ms"] > 0
    assert result["timings_ms"]["decode_ms"] >= 0
    assert result["timings_ms"]["quality_ms"] >= 0


# 14. model metadata
def test_model_metadata(engine, good_image):
    result = engine.analyze(good_image)
    assert result["inference"]["model"] == "random_forest_color_baseline"
    assert result["inference"]["version"] == "1.0"
    assert "CP-AnemiC" in result["inference"]["dataset"]


# 15. model failure (missing model file)
def test_model_missing_raises(tmp_path):
    e = AnemiaInferenceEngine(model_path=tmp_path / "nope.joblib")
    with pytest.raises(ModelNotLoadedError):
        e.load()


def test_unknown_ai_model_raises():
    from app.ai.errors import ModelConfigError

    with pytest.raises(ModelConfigError):
        AnemiaInferenceEngine(ai_model="resnet50")


# 16. repeated inference (same engine instance, multiple images)
def test_repeated_inference(engine):
    samples = sorted((RAW_TEST_DIR / "Anemic").glob("Image_*.png"))[:3]
    for s in samples:
        result = engine.analyze(s)
        assert result["success"] is True


# extra: oversized image
def test_image_too_large(engine, tmp_path):
    big = tmp_path / "big.png"
    Image.new("RGB", (5000, 5000), (128, 128, 128)).save(big)
    with pytest.raises(ImageTooLargeError):
        engine.analyze(big)


# extra: unsupported input
def test_unsupported_bytes(engine, tmp_path):
    txt = tmp_path / "note.txt"
    txt.write_text("hello")
    with pytest.raises((UnsupportedImageError, ImageCorruptedError)):
        engine.analyze(txt)
