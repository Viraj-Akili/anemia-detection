"""
src/ppg/features.py

PRAHARI PPG / Hardware ML Pipeline
STEP 3 — Master Feature Extraction API

Unified interface for extracting all time-domain, frequency-domain (FFT), pulse morphology,
and optical cross-channel features from dual-wavelength PPG signals.
Designed for both offline batch dataset extraction and real-time live streaming from ESP32.
"""

from typing import Union, Dict, Any, Optional, List
import numpy as np
import pandas as pd
from pathlib import Path

from .preprocessing import preprocess_ppg, convert_to_numeric
from .time_features import extract_time_domain_stats, extract_pulse_morphology
from .fft_features import extract_fft_features
from .cross_channel_features import extract_cross_channel_features


def extract_ppg_features(
    raw_red: Union[np.ndarray, pd.Series, list],
    raw_ir: Union[np.ndarray, pd.Series, list],
    clean_red: Optional[Union[np.ndarray, pd.Series, list]] = None,
    clean_ir: Optional[Union[np.ndarray, pd.Series, list]] = None,
    fs: float = 25.0
) -> Dict[str, float]:
    """
    Extract comprehensive feature vector from dual-wavelength PPG signals.
    
    If preprocessed signals (clean_red, clean_ir) are not passed, the function
    automatically runs Step 2 zero-phase filtering and detrending on the raw inputs.
    
    Parameters:
        raw_red: Raw optical Red channel ADC counts.
        raw_ir: Raw optical Infrared channel ADC counts.
        clean_red: Optional pre-filtered normalized Red channel.
        clean_ir: Optional pre-filtered normalized Infrared channel.
        fs: Sampling frequency in Hz (25.0 Hz).
    
    Returns:
        Dictionary of flat numeric features (Time, Frequency, Morphology, Optical Ratios).
    """
    r_raw = convert_to_numeric(raw_red)
    i_raw = convert_to_numeric(raw_ir)

    if clean_red is None or clean_ir is None:
        r_clean, i_clean, quality = preprocess_ppg(r_raw, i_raw, fs=fs)
    else:
        r_clean = convert_to_numeric(clean_red)
        i_clean = convert_to_numeric(clean_ir)

    features: Dict[str, float] = {}

    # 1. Time-Domain Statistical Metrics (Red and IR)
    features.update(extract_time_domain_stats(r_clean, prefix="red"))
    features.update(extract_time_domain_stats(i_clean, prefix="ir"))

    # 2. Pulse Morphology Metrics (Red and IR)
    features.update(extract_pulse_morphology(r_clean, fs=fs, prefix="red"))
    features.update(extract_pulse_morphology(i_clean, fs=fs, prefix="ir"))

    # 3. Frequency-Domain (FFT) Metrics (Red and IR)
    features.update(extract_fft_features(r_clean, fs=fs, prefix="red"))
    features.update(extract_fft_features(i_clean, fs=fs, prefix="ir"))

    # 4. Cross-Channel & Optical Ratios
    features.update(extract_cross_channel_features(r_raw, i_raw, r_clean, i_clean))

    return features


def extract_features_from_recording(
    file_path_or_df: Union[str, Path, pd.DataFrame],
    fs: float = 25.0
) -> Dict[str, Any]:
    """
    Extract features from a single recording while preserving subject demographic metadata
    and clinical Hemoglobin ground truth.
    """
    if isinstance(file_path_or_df, (str, Path)):
        df = pd.read_csv(file_path_or_df)
        source_name = Path(file_path_or_df).name
        stem = Path(file_path_or_df).stem
        subject_id = int(stem) if stem.isdigit() else stem
    else:
        df = file_path_or_df
        source_name = "in_memory"
        subject_id = "unknown"

    raw_red = df["Red (a.u)"].to_numpy()
    raw_ir = df["Infra Red (a.u)"].to_numpy()

    # Extract PPG signal features
    sig_features = extract_ppg_features(raw_red, raw_ir, fs=fs)

    # Extract demographic covariates
    gender_str = str(df["Gender"].iloc[0]) if "Gender" in df.columns else "UNKNOWN"
    age_val = int(df["Age"].iloc[0]) if "Age" in df.columns else -1
    hb_val = float(df["Hemoglobin (g/dL)"].iloc[0]) if "Hemoglobin (g/dL)" in df.columns else np.nan

    gender_encoded = 1 if gender_str.strip().lower() == "male" else (0 if gender_str.strip().lower() == "female" else -1)

    recording_row: Dict[str, Any] = {
        "subject_id": subject_id,
        "recording_id": f"sub_{subject_id:03d}_rec_01" if isinstance(subject_id, int) else f"{subject_id}_rec_01",
        "source_file": source_name,
        "age": age_val,
        "gender": gender_str,
        "gender_encoded": gender_encoded,
    }
    recording_row.update(sig_features)
    recording_row["hemoglobin_g_dl"] = hb_val  # Target variable (strictly at the end)

    return recording_row
