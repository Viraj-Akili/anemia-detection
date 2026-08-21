"""
src/ppg/esp32.py

PRAHARI PPG / Hardware ML Pipeline
STEP 4 — Live ESP32 / MAX30102 Hardware Parser, Telemetry Validator & Predictor

Consumes raw CSV output from teammate Arya's ESP32 microcontroller:
    timestamp_ms,red,ir

Performs rigorous temporal, monotonic, and sampling rate validation (25 Hz +/- 2 Hz),
then feeds the validated signals through the existing Step 2 preprocessing,
Step 3 feature extraction, and trained Step 3 Lasso regression model.
"""

from typing import Union, Dict, Any, Tuple, Optional, List
from pathlib import Path
import pandas as pd
import numpy as np
import joblib

from .preprocessing import preprocess_ppg, convert_to_numeric
from .features import extract_ppg_features


def validate_esp32_dataframe(
    df: pd.DataFrame,
    expected_fs: float = 25.0,
    fs_tolerance_hz: float = 2.0,
    min_samples: int = 240,
    max_samples: int = 260
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Perform strict validation on raw ESP32 MAX30102 dataframe.
    
    Checks:
        1. Required columns: ['timestamp_ms', 'red', 'ir']
        2. Numeric datatypes without NaNs or Infs
        3. Strictly positive optical ADC counts (Red > 0, IR > 0)
        4. Strictly monotonic timestamps (no backwards steps, no duplicates: dt > 0)
        5. Sample count within bounds [min_samples, max_samples] (nominal 250)
        6. Effective sampling rate within tolerance (expected_fs +/- fs_tolerance_hz)
    
    Returns:
        (is_valid, error_message, telemetry_dict)
    """
    telemetry: Dict[str, Any] = {
        "sample_count": 0,
        "duration_sec": 0.0,
        "median_dt_ms": 0.0,
        "effective_fs_hz": 0.0,
        "min_dt_ms": 0.0,
        "max_dt_ms": 0.0,
        "dt_std_ms": 0.0,
        "red_mean_raw": 0.0,
        "ir_mean_raw": 0.0,
    }

    # 1. Check required columns
    required_cols = {"timestamp_ms", "red", "ir"}
    df_cols_lower = {c.strip().lower(): c for c in df.columns}
    if not required_cols.issubset(df_cols_lower.keys()):
        missing = required_cols - df_cols_lower.keys()
        return False, f"Missing required ESP32 columns: {sorted(list(missing))}", telemetry

    # Standardize column mapping
    ts_col = df_cols_lower["timestamp_ms"]
    red_col = df_cols_lower["red"]
    ir_col = df_cols_lower["ir"]

    # 2. Check sample count
    n_samples = len(df)
    telemetry["sample_count"] = n_samples
    if n_samples < min_samples or n_samples > max_samples:
        return False, f"Invalid sample count: {n_samples} (Expected between {min_samples} and {max_samples})", telemetry

    # 3. Validate numeric conversion
    try:
        ts = pd.to_numeric(df[ts_col], errors="raise").to_numpy(dtype=np.float64)
        red = pd.to_numeric(df[red_col], errors="raise").to_numpy(dtype=np.float64)
        ir = pd.to_numeric(df[ir_col], errors="raise").to_numpy(dtype=np.float64)
    except Exception as e:
        return False, f"Non-numeric values found in ESP32 data: {e}", telemetry

    # 4. Check NaN / Inf
    if np.isnan(ts).any() or np.isnan(red).any() or np.isnan(ir).any():
        return False, "NaN values detected in ESP32 recording", telemetry
    if np.isinf(ts).any() or np.isinf(red).any() or np.isinf(ir).any():
        return False, "Infinite values detected in ESP32 recording", telemetry

    # 5. Check positive optical ADC counts
    if np.any(red <= 0) or np.any(ir <= 0):
        return False, "Non-positive optical ADC counts detected (Red or IR <= 0)", telemetry

    # 6. Validate Timestamps & Monotonicity
    if np.any(ts < 0):
        return False, "Negative timestamps detected", telemetry

    dt = np.diff(ts)
    if len(dt) == 0:
        return False, "Insufficient timestamp data", telemetry

    if np.any(dt == 0):
        dup_count = int(np.sum(dt == 0))
        return False, f"Duplicate timestamps detected ({dup_count} zero-intervals)", telemetry

    if np.any(dt < 0):
        neg_count = int(np.sum(dt < 0))
        return False, f"Non-monotonic timestamps detected ({neg_count} backwards steps)", telemetry

    # 7. Compute Timing Telemetry
    median_dt = float(np.median(dt))
    min_dt = float(np.min(dt))
    max_dt = float(np.max(dt))
    dt_std = float(np.std(dt))
    duration = float((ts[-1] - ts[0]) / 1000.0)

    if median_dt <= 0:
        return False, f"Invalid median timestamp delta: {median_dt} ms", telemetry

    effective_fs = float(1000.0 / median_dt)

    telemetry.update({
        "duration_sec": round(duration, 3),
        "median_dt_ms": round(median_dt, 2),
        "effective_fs_hz": round(effective_fs, 2),
        "min_dt_ms": round(min_dt, 2),
        "max_dt_ms": round(max_dt, 2),
        "dt_std_ms": round(dt_std, 2),
        "red_mean_raw": round(float(np.mean(red)), 2),
        "ir_mean_raw": round(float(np.mean(ir)), 2),
    })

    # 8. Check Effective Sampling Rate Tolerance
    fs_diff = abs(effective_fs - expected_fs)
    if fs_diff > fs_tolerance_hz:
        return (
            False,
            f"Effective sampling rate {effective_fs:.2f} Hz deviates from expected {expected_fs:.1f} Hz by {fs_diff:.2f} Hz (tolerance: +/-{fs_tolerance_hz:.1f} Hz)",
            telemetry
        )

    return True, "OK", telemetry


def load_esp32_csv(
    file_path: Union[str, Path],
    expected_fs: float = 25.0,
    fs_tolerance_hz: float = 2.0
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    Load, parse, and validate an ESP32 PPG CSV file from disk.
    
    Returns:
        (raw_red, raw_ir, telemetry_dict)
    
    Raises:
        ValueError: If file is missing or fails validation.
    """
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"ESP32 CSV file not found: {p}")

    try:
        df = pd.read_csv(p)
    except Exception as e:
        raise ValueError(f"Failed to read ESP32 CSV file: {e}")

    is_valid, msg, telemetry = validate_esp32_dataframe(
        df,
        expected_fs=expected_fs,
        fs_tolerance_hz=fs_tolerance_hz
    )

    if not is_valid:
        raise ValueError(f"ESP32 Validation Error: {msg}")

    # Standardize column mapping
    df_cols_lower = {c.strip().lower(): c for c in df.columns}
    raw_red = df[df_cols_lower["red"]].to_numpy(dtype=np.float64)
    raw_ir = df[df_cols_lower["ir"]].to_numpy(dtype=np.float64)

    return raw_red, raw_ir, telemetry


def predict_esp32_recording(
    file_path_or_df: Union[str, Path, pd.DataFrame],
    model_bundle_path: Union[str, Path] = "models/best_ppg_hb_model.joblib",
    age: float = 25.0,
    gender: str = "Male",
    fs: float = 25.0
) -> Dict[str, Any]:
    """
    Execute full inference pipeline on an ESP32 recording.
    
    Pipeline:
        1. Validate ESP32 recording format & sampling rate (25 Hz)
        2. Step 2 zero-phase bandpass filtering & SQI assessment
        3. Step 3 74-feature extraction (Time, Frequency, Morphology, Optical Ratios, Demographics)
        4. Strict feature schema verification against trained model bundle
        5. StandardScaler transformation (fitted on Train set)
        6. Model inference (Lasso Regression)
    
    Returns:
        Complete dictionary with prediction, signal quality, and telemetry.
    """
    # 1. Load Model Bundle
    model_p = Path(model_bundle_path)
    if not model_p.exists():
        raise FileNotFoundError(f"Model artifact not found at {model_p}. Train model first.")

    bundle = joblib.load(model_p)
    model = bundle["model"]
    scaler = bundle["scaler"]
    feature_cols: List[str] = bundle["feature_cols"]
    model_name = bundle.get("model_name", "Trained Model")

    # 2. Parse & Validate ESP32 Inputs
    if isinstance(file_path_or_df, (str, Path)):
        raw_red, raw_ir, telemetry = load_esp32_csv(file_path_or_df, expected_fs=fs)
        source_name = Path(file_path_or_df).name
    else:
        is_valid, msg, telemetry = validate_esp32_dataframe(file_path_or_df, expected_fs=fs)
        if not is_valid:
            raise ValueError(f"ESP32 Validation Error: {msg}")
        df_cols_lower = {c.strip().lower(): c for c in file_path_or_df.columns}
        raw_red = file_path_or_df[df_cols_lower["red"]].to_numpy(dtype=np.float64)
        raw_ir = file_path_or_df[df_cols_lower["ir"]].to_numpy(dtype=np.float64)
        source_name = "in_memory_dataframe"

    # 3. Step 2 Preprocessing & Signal Quality
    clean_red, clean_ir, quality = preprocess_ppg(raw_red, raw_ir, fs=fs)

    # 4. Step 3 Feature Extraction
    sig_features = extract_ppg_features(raw_red, raw_ir, clean_red, clean_ir, fs=fs)

    # Incorporate Demographics
    sig_features["age"] = float(age)
    g_str = str(gender).strip().lower()
    sig_features["gender_encoded"] = 1.0 if g_str == "male" else (0.0 if g_str == "female" else 0.5)

    # 5. Strict Feature Schema Check
    missing_feats = [f for f in feature_cols if f not in sig_features]
    if missing_feats:
        raise ValueError(f"Feature Schema Mismatch: Missing expected features {missing_feats}")

    # Build exact ordered feature vector
    feat_vector = np.array([[sig_features[col] for col in feature_cols]], dtype=np.float64)

    if np.isnan(feat_vector).any():
        raise ValueError("Feature vector contains NaN values.")
    if np.isinf(feat_vector).any():
        raise ValueError("Feature vector contains Infinite values.")

    # 6. Scale & Predict
    feat_vector_scaled = scaler.transform(feat_vector)
    predicted_hb = float(model.predict(feat_vector_scaled)[0])

    return {
        "source": source_name,
        "sample_count": telemetry["sample_count"],
        "duration_sec": telemetry["duration_sec"],
        "effective_fs_hz": telemetry["effective_fs_hz"],
        "median_dt_ms": telemetry["median_dt_ms"],
        "preprocessing_status": "SUCCESS",
        "signal_quality": quality["status"],
        "sqi_score": quality["metrics"]["mean_cardiac_sqi"],
        "feature_count": len(feature_cols),
        "model_name": model_name,
        "patient_age": age,
        "patient_gender": gender,
        "predicted_hb_g_dl": round(predicted_hb, 2),
        "telemetry": telemetry,
        "quality_details": quality
    }
