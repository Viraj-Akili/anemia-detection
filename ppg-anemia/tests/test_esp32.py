"""
tests/test_esp32.py

Unit tests for STEP 4: Live ESP32 / MAX30102 PPG Hardware Integration.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile

from src.ppg.esp32 import validate_esp32_dataframe, load_esp32_csv, predict_esp32_recording
from src.ppg.features import extract_features_from_recording
import joblib


@pytest.fixture
def valid_esp32_df():
    """Generates 250 samples of valid ESP32 data (25 Hz, 40ms interval)."""
    t = np.arange(0, 250 * 40, 40)  # 0, 40, 80, ..., 9960 ms
    red = 115000 + 1000 * np.sin(2 * np.pi * 1.25 * (t / 1000.0))
    ir = 105000 + 1200 * np.sin(2 * np.pi * 1.25 * (t / 1000.0))
    return pd.DataFrame({
        "timestamp_ms": t,
        "red": red,
        "ir": ir
    })


def test_valid_esp32_dataframe(valid_esp32_df):
    is_valid, msg, telemetry = validate_esp32_dataframe(valid_esp32_df)
    assert is_valid is True
    assert msg == "OK"
    assert telemetry["sample_count"] == 250
    assert telemetry["effective_fs_hz"] == 25.0
    assert telemetry["median_dt_ms"] == 40.0
    assert telemetry["duration_sec"] == 9.96


def test_missing_columns():
    df_missing = pd.DataFrame({
        "timestamp_ms": [0, 40, 80],
        "red": [100000, 100000, 100000]
        # missing 'ir'
    })
    is_valid, msg, _ = validate_esp32_dataframe(df_missing)
    assert is_valid is False
    assert "Missing required ESP32 columns" in msg


def test_malformed_red_ir(valid_esp32_df):
    df_bad = valid_esp32_df.copy().astype(object)
    df_bad.loc[10, "red"] = "INVALID_STRING"
    is_valid, msg, _ = validate_esp32_dataframe(df_bad)
    assert is_valid is False
    assert "Non-numeric values found" in msg


def test_nan_inf_values(valid_esp32_df):
    df_nan = valid_esp32_df.copy()
    df_nan.loc[5, "ir"] = np.nan
    is_valid, msg, _ = validate_esp32_dataframe(df_nan)
    assert is_valid is False
    assert "NaN values detected" in msg

    df_inf = valid_esp32_df.copy()
    df_inf["timestamp_ms"] = df_inf["timestamp_ms"].astype(float)
    df_inf.loc[5, "timestamp_ms"] = np.inf
    is_valid, msg, _ = validate_esp32_dataframe(df_inf)
    assert is_valid is False
    assert "Infinite values detected" in msg


def test_duplicate_timestamps(valid_esp32_df):
    df_dup = valid_esp32_df.copy()
    df_dup.loc[15, "timestamp_ms"] = df_dup.loc[14, "timestamp_ms"]  # dt = 0
    is_valid, msg, _ = validate_esp32_dataframe(df_dup)
    assert is_valid is False
    assert "Duplicate timestamps detected" in msg


def test_non_monotonic_timestamps(valid_esp32_df):
    df_back = valid_esp32_df.copy()
    df_back.loc[20, "timestamp_ms"] = df_back.loc[19, "timestamp_ms"] - 50  # dt < 0
    is_valid, msg, _ = validate_esp32_dataframe(df_back)
    assert is_valid is False
    assert "Non-monotonic timestamps detected" in msg


def test_wrong_sample_count(valid_esp32_df):
    # Too few samples (< 240)
    df_short = valid_esp32_df.iloc[:100].copy()
    is_valid, msg, _ = validate_esp32_dataframe(df_short)
    assert is_valid is False
    assert "Invalid sample count: 100" in msg

    # Too many samples (> 260)
    df_long = pd.concat([valid_esp32_df, valid_esp32_df]).reset_index(drop=True)
    is_valid, msg, _ = validate_esp32_dataframe(df_long)
    assert is_valid is False
    assert "Invalid sample count: 500" in msg


def test_incorrect_sampling_rate(valid_esp32_df):
    # 50 Hz (20ms interval instead of 40ms)
    t_50hz = np.arange(0, 250 * 20, 20)
    df_50hz = valid_esp32_df.copy()
    df_50hz["timestamp_ms"] = t_50hz

    is_valid, msg, telemetry = validate_esp32_dataframe(df_50hz)
    assert is_valid is False
    assert "deviates from expected 25.0 Hz" in msg
    assert telemetry["effective_fs_hz"] == 50.0


def test_successful_model_inference(valid_esp32_df):
    model_path = Path("models/best_ppg_hb_model.joblib")
    if not model_path.exists():
        pytest.skip("Model bundle not present on disk.")

    res = predict_esp32_recording(
        file_path_or_df=valid_esp32_df,
        model_bundle_path=model_path,
        age=21,
        gender="Male",
        fs=25.0
    )

    assert res["preprocessing_status"] == "SUCCESS"
    assert res["signal_quality"] in ["GOOD", "WARNING"]
    assert res["feature_count"] == 74
    assert 5.0 <= res["predicted_hb_g_dl"] <= 25.0


def test_transport_format_numerical_equivalence():
    """
    Assert exact mathematical equivalence between dataset schema (raw 1.csv)
    and ESP32 transport schema (timestamp_ms, red, ir).
    """
    raw_path = Path("data/raw/1.csv")
    model_path = Path("models/best_ppg_hb_model.joblib")
    if not raw_path.exists() or not model_path.exists():
        pytest.skip("Prerequisite raw data or model not present.")

    # 1. Dataset schema path
    df_raw = pd.read_csv(raw_path)
    rec_features = extract_features_from_recording(raw_path, fs=25.0)

    bundle = joblib.load(model_path)
    model = bundle["model"]
    scaler = bundle["scaler"]
    feature_cols = bundle["feature_cols"]

    x_raw = np.array([[rec_features[col] for col in feature_cols]], dtype=np.float64)
    x_raw_scaled = scaler.transform(x_raw)
    pred_dataset = float(model.predict(x_raw_scaled)[0])

    # 2. ESP32 transport schema path
    esp_df = pd.DataFrame({
        "timestamp_ms": [i * 40 for i in range(len(df_raw))],
        "red": df_raw["Red (a.u)"],
        "ir": df_raw["Infra Red (a.u)"]
    })

    esp_res = predict_esp32_recording(
        file_path_or_df=esp_df,
        model_bundle_path=model_path,
        age=float(df_raw["Age"].iloc[0]),
        gender=str(df_raw["Gender"].iloc[0]),
        fs=25.0
    )
    pred_esp32 = esp_res["predicted_hb_g_dl"]

    # Difference must be essentially zero (< 0.01 g/dL rounding margin)
    diff = abs(pred_dataset - pred_esp32)
    assert diff < 0.01, f"Numerical discrepancy between dataset and ESP32 path: {diff:.6f} g/dL"
