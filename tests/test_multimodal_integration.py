"""Comprehensive test suite for the PRAHARI Multimodal Integration Layer (Step 5B).

Covers all 12 required test conditions:
1. Image-only inference
2. PPG-only inference
3. Both modalities together
4. Missing image handling (when PPG is provided)
5. Missing PPG handling (when image is provided)
6. Invalid / corrupted image
7. Invalid / malformed PPG CSV
8. Image quality gate failure (blurred image)
9. PPG quality gate / sampling failure
10. Both modalities valid but fusion status remains NOT_VALIDATED
11. PPG prediction matches standalone PPG inference directly
12. Image prediction matches standalone image inference directly
"""

import sys
import tempfile
from pathlib import Path
import cv2
import numpy as np
import pandas as pd
import pytest

# Ensure workspace root and subproject roots are on sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from integration import (
    MultimodalScreeningEngine,
    MultimodalScreeningRequest,
    run_multimodal_screening,
)


@pytest.fixture(scope="session")
def engine():
    """Shared MultimodalScreeningEngine instance."""
    eng = MultimodalScreeningEngine()
    eng.load()
    return eng


@pytest.fixture(scope="session")
def sample_image_path():
    """Path to a verified good conjunctival image."""
    img_path = WORKSPACE_ROOT / "person1" / "data" / "raw" / "cp-anemic" / "Anemic" / "Image_001.png"
    assert img_path.exists(), f"Sample image not found: {img_path}"
    return img_path


@pytest.fixture(scope="session")
def sample_ppg_csv_path():
    """Path to a verified 25 Hz ESP32 PPG CSV."""
    ppg_path = WORKSPACE_ROOT / "ppg-anemia" / "tests" / "data" / "simulated_esp32_sub1.csv"
    assert ppg_path.exists(), f"Sample PPG CSV not found: {ppg_path}"
    return ppg_path


# ==============================================================================
# 1. Image-Only Inference
# ==============================================================================
def test_image_only_inference(engine, sample_image_path):
    """Test inference when only an image is supplied."""
    resp = engine.screen(MultimodalScreeningRequest(
        image_path=str(sample_image_path),
        ppg_csv_path=None
    ))

    assert resp.success is True
    assert resp.image.available is True
    assert resp.image.status == "SUCCESS"
    assert resp.image.label in ("anemic", "non_anemic")
    assert resp.image.probability is not None
    assert 0.0 <= resp.image.probability <= 1.0
    assert resp.image.quality_status == "good"

    # PPG must be marked as not provided
    assert resp.ppg.available is False
    assert resp.ppg.status == "NOT_PROVIDED"
    assert resp.ppg.predicted_hb_g_dl is None

    # Fusion must remain NOT_VALIDATED
    assert resp.fusion.status == "NOT_VALIDATED"
    assert resp.fusion.method is None
    assert resp.fusion.result is None


# ==============================================================================
# 2. PPG-Only Inference
# ==============================================================================
def test_ppg_only_inference(engine, sample_ppg_csv_path):
    """Test inference when only PPG CSV is supplied."""
    resp = engine.screen(MultimodalScreeningRequest(
        image_path=None,
        ppg_csv_path=str(sample_ppg_csv_path),
        age=21.0,
        gender="Male"
    ))

    assert resp.success is True
    assert resp.ppg.available is True
    assert resp.ppg.status == "SUCCESS"
    assert resp.ppg.predicted_hb_g_dl is not None
    assert resp.ppg.predicted_hb_g_dl > 0.0
    assert resp.ppg.signal_quality in ("GOOD", "POOR")
    assert resp.ppg.sampling_rate_hz == pytest.approx(25.0, abs=1.0)
    assert resp.ppg.samples == 250

    # Image must be marked as not provided
    assert resp.image.available is False
    assert resp.image.status == "NOT_PROVIDED"
    assert resp.image.label is None

    # Fusion must remain NOT_VALIDATED
    assert resp.fusion.status == "NOT_VALIDATED"
    assert resp.fusion.method is None
    assert resp.fusion.result is None


# ==============================================================================
# 3. Both Modalities Together
# ==============================================================================
def test_both_modalities_inference(engine, sample_image_path, sample_ppg_csv_path):
    """Test inference when both modalities are supplied."""
    resp = engine.screen(MultimodalScreeningRequest(
        image_path=str(sample_image_path),
        ppg_csv_path=str(sample_ppg_csv_path),
        age=25.0,
        gender="Female"
    ))

    assert resp.success is True
    assert resp.patient.age == 25.0
    assert resp.patient.gender == "Female"

    # Image checks
    assert resp.image.available is True
    assert resp.image.status == "SUCCESS"
    assert resp.image.label in ("anemic", "non_anemic")
    assert resp.image.probability is not None

    # PPG checks
    assert resp.ppg.available is True
    assert resp.ppg.status == "SUCCESS"
    assert resp.ppg.predicted_hb_g_dl is not None
    assert resp.ppg.predicted_hb_g_dl > 0.0

    # Fusion checks
    assert resp.fusion.status == "NOT_VALIDATED"
    assert resp.fusion.method is None
    assert resp.fusion.result is None


# ==============================================================================
# 4. Missing Image Handling
# ==============================================================================
def test_missing_image_handling(engine, sample_ppg_csv_path):
    """Explicitly test that omitting image produces valid PPG output and clear image state."""
    resp = run_multimodal_screening(
        image_path=None,
        ppg_csv_path=sample_ppg_csv_path,
        engine=engine
    )

    assert resp.success is True
    assert resp.image.available is False
    assert resp.image.status == "NOT_PROVIDED"
    assert resp.ppg.available is True
    assert resp.ppg.status == "SUCCESS"


# ==============================================================================
# 5. Missing PPG Handling
# ==============================================================================
def test_missing_ppg_handling(engine, sample_image_path):
    """Explicitly test that omitting PPG produces valid Image output and clear PPG state."""
    resp = run_multimodal_screening(
        image_path=sample_image_path,
        ppg_csv_path=None,
        engine=engine
    )

    assert resp.success is True
    assert resp.image.available is True
    assert resp.image.status == "SUCCESS"
    assert resp.ppg.available is False
    assert resp.ppg.status == "NOT_PROVIDED"


# ==============================================================================
# 6. Invalid / Corrupted Image
# ==============================================================================
def test_invalid_image(engine, sample_ppg_csv_path):
    """Test handling of corrupted or non-image files."""
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"this is plain text, not an image")
        bad_img_path = Path(f.name)

    try:
        resp = engine.screen(MultimodalScreeningRequest(
            image_path=str(bad_img_path),
            ppg_csv_path=str(sample_ppg_csv_path)
        ))

        # Overall success is True because PPG still succeeded
        assert resp.success is True
        assert resp.image.available is True
        assert resp.image.status in ("ERROR", "REJECTED")
        assert resp.image.error is not None
        assert resp.ppg.status == "SUCCESS"
    finally:
        bad_img_path.unlink(missing_ok=True)


# ==============================================================================
# 7. Invalid / Malformed PPG CSV
# ==============================================================================
def test_invalid_ppg_csv(engine, sample_image_path):
    """Test handling of malformed PPG CSV (missing required headers)."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        f.write("wrong_col1,wrong_col2\n1.0,2.0\n3.0,4.0\n")
        bad_csv_path = Path(f.name)

    try:
        resp = engine.screen(MultimodalScreeningRequest(
            image_path=str(sample_image_path),
            ppg_csv_path=str(bad_csv_path)
        ))

        # Overall success is True because Image still succeeded
        assert resp.success is True
        assert resp.image.status == "SUCCESS"
        assert resp.ppg.available is True
        assert resp.ppg.status in ("ERROR", "REJECTED")
        assert resp.ppg.error is not None
        assert "Missing required" in resp.ppg.error.message or "Validation Error" in resp.ppg.error.message
    finally:
        bad_csv_path.unlink(missing_ok=True)


# ==============================================================================
# 8. Image Quality Gate Failure (Blurred Image)
# ==============================================================================
def test_image_quality_failure(engine, sample_image_path, sample_ppg_csv_path):
    """Test that an artificially blurred image is cleanly REJECTED by quality gate."""
    # Create heavily blurred version of sample image
    orig = cv2.imread(str(sample_image_path), cv2.IMREAD_UNCHANGED)
    blurred = cv2.GaussianBlur(orig, (41, 41), 0)

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        blurred_path = Path(f.name)
    cv2.imwrite(str(blurred_path), blurred)

    try:
        resp = engine.screen(MultimodalScreeningRequest(
            image_path=str(blurred_path),
            ppg_csv_path=str(sample_ppg_csv_path)
        ))

        # Image must be REJECTED, but PPG remains SUCCESS
        assert resp.success is True
        assert resp.image.available is True
        assert resp.image.status == "REJECTED"
        assert resp.image.quality_status == "poor"
        assert "blur" in resp.image.quality_reasons
        assert resp.image.error is not None
        assert resp.image.error.code == "IMAGE_QUALITY_LOW"

        # PPG is unaffected
        assert resp.ppg.status == "SUCCESS"
    finally:
        blurred_path.unlink(missing_ok=True)


# ==============================================================================
# 9. PPG Quality Gate / Sampling Failure
# ==============================================================================
def test_ppg_sampling_failure(engine, sample_image_path):
    """Test that a PPG CSV with incorrect sampling rate is cleanly rejected."""
    # Create a CSV with non-monotonic or wildly incorrect dt (e.g. 5 Hz instead of 25 Hz)
    timestamps = np.arange(0, 25000, 200)  # dt = 200ms -> fs = 5 Hz (violates 25 +/- 2 Hz)
    df_bad = pd.DataFrame({
        "timestamp_ms": timestamps,
        "red": np.full(len(timestamps), 100000),
        "ir": np.full(len(timestamps), 100000)
    })

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        bad_ppg_path = Path(f.name)
    df_bad.to_csv(bad_ppg_path, index=False)

    try:
        resp = engine.screen(MultimodalScreeningRequest(
            image_path=str(sample_image_path),
            ppg_csv_path=str(bad_ppg_path)
        ))

        # PPG should be REJECTED / ERROR due to sampling rate deviation
        assert resp.success is True
        assert resp.image.status == "SUCCESS"
        assert resp.ppg.available is True
        assert resp.ppg.status in ("ERROR", "REJECTED")
        assert resp.ppg.error is not None
        assert "deviates from expected" in resp.ppg.error.message or "Validation Error" in resp.ppg.error.message
    finally:
        bad_ppg_path.unlink(missing_ok=True)


# ==============================================================================
# 10. Both Modalities Valid: Fusion Status Remains NOT_VALIDATED
# ==============================================================================
def test_fusion_status_not_validated(engine, sample_image_path, sample_ppg_csv_path):
    """Verify that when both modalities succeed, fusion status is explicitly NOT_VALIDATED."""
    resp = engine.screen(MultimodalScreeningRequest(
        image_path=str(sample_image_path),
        ppg_csv_path=str(sample_ppg_csv_path)
    ))

    assert resp.success is True
    assert resp.image.status == "SUCCESS"
    assert resp.ppg.status == "SUCCESS"

    # Strict check: No unvalidated fusion math or score should be present
    assert resp.fusion.status == "NOT_VALIDATED"
    assert resp.fusion.method is None
    assert resp.fusion.result is None
    assert "not performed because no paired dataset" in resp.fusion.note


# ==============================================================================
# 11. Verify PPG Prediction Matches Standalone PPG Model Directly
# ==============================================================================
def test_ppg_prediction_identical_to_standalone(engine, sample_ppg_csv_path):
    """Verify that the integration layer returns the exact same PPG prediction as direct call."""
    from ppg.esp32 import predict_esp32_recording

    direct_result = predict_esp32_recording(
        file_path_or_df=sample_ppg_csv_path,
        model_bundle_path=engine.ppg_model_path,
        age=25.0,
        gender="Male",
        fs=25.0
    )

    resp = engine.screen(MultimodalScreeningRequest(
        image_path=None,
        ppg_csv_path=str(sample_ppg_csv_path),
        age=25.0,
        gender="Male"
    ))

    assert resp.ppg.status == "SUCCESS"
    assert resp.ppg.predicted_hb_g_dl == pytest.approx(float(direct_result["predicted_hb_g_dl"]), abs=1e-4)
    assert resp.ppg.sqi == pytest.approx(float(direct_result["sqi_score"]), abs=1e-4)
    assert resp.ppg.sampling_rate_hz == pytest.approx(float(direct_result["effective_fs_hz"]), abs=1e-4)
    assert resp.ppg.samples == int(direct_result["sample_count"])


# ==============================================================================
# 12. Verify Image Prediction Matches Standalone Image Model Directly
# ==============================================================================
def test_image_prediction_identical_to_standalone(engine, sample_image_path):
    """Verify that the integration layer returns the exact same Image prediction as direct call."""
    from app.ai.inference import AnemiaInferenceEngine

    standalone_img_engine = AnemiaInferenceEngine(model_path=engine.image_model_path)
    standalone_img_engine.load()
    direct_result = standalone_img_engine.analyze(sample_image_path)

    resp = engine.screen(MultimodalScreeningRequest(
        image_path=str(sample_image_path),
        ppg_csv_path=None
    ))

    assert resp.image.status == "SUCCESS"
    assert resp.image.label == direct_result["prediction"]["label"]
    assert resp.image.probability == pytest.approx(direct_result["prediction"]["model_probability"], abs=1e-4)
    assert resp.image.confidence == pytest.approx(direct_result["prediction"]["model_confidence"], abs=1e-4)
    assert resp.image.quality_status == direct_result["image_quality"]["status"]
    assert resp.image.quality_score == pytest.approx(direct_result["image_quality"]["score"], abs=1e-4)


# ==============================================================================
# 13. Neither Modality Provided
# ==============================================================================
def test_neither_modality_provided(engine):
    """Verify request fails cleanly when neither image nor PPG is provided."""
    resp = engine.screen(MultimodalScreeningRequest(
        image_path=None,
        ppg_csv_path=None
    ))

    assert resp.success is False
    assert resp.image.status == "NOT_PROVIDED"
    assert resp.ppg.status == "NOT_PROVIDED"
    assert resp.error is not None
    assert resp.error.code == "NO_MODALITIES_PROVIDED"
