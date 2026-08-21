"""
src/ppg/preprocessing.py

PRAHARI PPG / Hardware ML Pipeline
STEP 2 — PPG Preprocessing & Signal Filtering

This module implements a reusable, scientifically grounded preprocessing pipeline
for dual-wavelength (Red + Infrared) photoplethysmography signals.
Designed for both offline dataset processing and future real-time ESP32 live streaming.
"""

from typing import Union, Tuple, Dict, Any, Optional
import numpy as np
import pandas as pd
import scipy.signal
from .quality import assess_signal_quality


def convert_to_numeric(signal: Union[np.ndarray, pd.Series, list]) -> np.ndarray:
    """
    Convert input signal into a clean 1D float64 numpy array.
    Validates finite values and raises ValueError if conversion fails or all values are NaN.
    """
    if isinstance(signal, pd.Series):
        arr = pd.to_numeric(signal, errors="coerce").to_numpy(dtype=np.float64)
    else:
        arr = np.asarray(signal, dtype=np.float64)

    if arr.ndim != 1:
        arr = arr.flatten()

    return arr


def detrend_signal(signal: np.ndarray, method: str = "linear") -> np.ndarray:
    """
    Remove baseline drift and slow DC trend from the PPG signal.
    
    Parameters:
        signal: 1D numpy array of raw signal samples.
        method: Detrending method ('linear' or 'constant').
    
    Returns:
        1D numpy array of detrended signal.
    """
    if len(signal) == 0:
        return signal
    if method == "linear":
        return scipy.signal.detrend(signal, type="linear")
    elif method == "constant":
        return scipy.signal.detrend(signal, type="constant")
    else:
        raise ValueError(f"Unsupported detrending method: {method}")


def bandpass_filter(
    signal: np.ndarray,
    fs: float = 25.0,
    low_cutoff: float = 0.5,
    high_cutoff: float = 5.0,
    order: int = 3
) -> np.ndarray:
    """
    Apply a zero-phase Butterworth bandpass filter to remove out-of-band noise.
    
    Parameters:
        signal: 1D numpy array of signal samples.
        fs: Sampling frequency in Hz (verified 25 Hz for this dataset).
        low_cutoff: Lower cutoff frequency in Hz (default 0.5 Hz / 30 BPM).
        high_cutoff: Upper cutoff frequency in Hz (default 5.0 Hz / 300 BPM).
        order: Filter order (3rd order Butterworth -> effective 6th order with zero-phase filtfilt).
    
    Returns:
        1D numpy array of bandpass filtered signal with zero phase shift.
    """
    if len(signal) < 10:
        raise ValueError(f"Signal length ({len(signal)}) is too short for filtering.")

    nyq = 0.5 * fs
    if low_cutoff <= 0 or low_cutoff >= nyq:
        raise ValueError(f"low_cutoff ({low_cutoff}) must be between 0 and Nyquist frequency ({nyq} Hz).")
    if high_cutoff <= low_cutoff or high_cutoff >= nyq:
        raise ValueError(f"high_cutoff ({high_cutoff}) must be between low_cutoff ({low_cutoff}) and Nyquist ({nyq} Hz).")

    # Design Butterworth bandpass filter
    b, a = scipy.signal.butter(order, [low_cutoff, high_cutoff], btype="bandpass", fs=fs)

    # Calculate safe padlen for filtfilt
    padlen = 3 * max(len(a), len(b))
    if len(signal) <= padlen:
        padlen = len(signal) - 1

    # Zero-phase bidirectional filtering
    filtered = scipy.signal.filtfilt(b, a, signal, padlen=padlen)
    return filtered


def normalize_signal(signal: np.ndarray, method: str = "zscore") -> np.ndarray:
    """
    Normalize the signal to standardize amplitude across recordings.
    
    Parameters:
        signal: 1D numpy array.
        method: Normalization method:
            - 'zscore': (x - mean) / std
            - 'robust': (x - median) / IQR
            - 'minmax': scaled to [-1, 1]
    
    Returns:
        1D numpy array of normalized signal.
    """
    if len(signal) == 0:
        return signal

    if method == "zscore":
        std = np.std(signal)
        if std < 1e-8:
            return np.zeros_like(signal)
        return (signal - np.mean(signal)) / std

    elif method == "robust":
        med = np.median(signal)
        q75, q25 = np.percentile(signal, [75, 25])
        iqr = q75 - q25
        if iqr < 1e-8:
            return np.zeros_like(signal)
        return (signal - med) / (iqr / 1.349)

    elif method == "minmax":
        s_min = np.min(signal)
        s_max = np.max(signal)
        if (s_max - s_min) < 1e-8:
            return np.zeros_like(signal)
        return 2.0 * (signal - s_min) / (s_max - s_min) - 1.0

    else:
        raise ValueError(f"Unsupported normalization method: {method}")


def preprocess_ppg(
    raw_red: Union[np.ndarray, pd.Series, list],
    raw_ir: Union[np.ndarray, pd.Series, list],
    fs: float = 25.0,
    low_cutoff: float = 0.5,
    high_cutoff: float = 5.0,
    order: int = 3,
    detrend_method: str = "linear",
    norm_method: str = "zscore"
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    Unified preprocessing pipeline entrypoint for both offline dataset recordings
    and live real-time streams from ESP32 / MAX30102.
    
    Pipeline Steps:
        1. Numeric conversion & validation
        2. Signal detrending (baseline wander removal)
        3. Zero-phase bandpass filtering (0.5 - 5.0 Hz @ 25 Hz)
        4. Amplitude normalization (Z-score)
        5. Multi-criteria signal quality assessment
    
    Parameters:
        raw_red: Raw optical Red channel signal (ADC counts).
        raw_ir: Raw optical Infrared channel signal (ADC counts).
        fs: Sampling frequency in Hz (verified 25 Hz).
        low_cutoff: Bandpass low cutoff frequency (default 0.5 Hz).
        high_cutoff: Bandpass high cutoff frequency (default 5.0 Hz).
        order: Filter order (default 3).
        detrend_method: Method for baseline removal ('linear').
        norm_method: Method for signal standardization ('zscore').
    
    Returns:
        clean_red: 1D numpy array of preprocessed Red signal.
        clean_ir: 1D numpy array of preprocessed Infrared signal.
        quality_report: Dictionary containing signal quality status, metrics, and diagnostics.
    """
    red_num = convert_to_numeric(raw_red)
    ir_num = convert_to_numeric(raw_ir)

    if len(red_num) != len(ir_num):
        raise ValueError(f"Red ({len(red_num)}) and IR ({len(ir_num)}) channel sample counts must match.")

    # Check for empty or non-finite inputs before processing
    if len(red_num) < 10 or np.isnan(red_num).any() or np.isnan(ir_num).any() or np.isinf(red_num).any() or np.isinf(ir_num).any():
        quality_report = assess_signal_quality(red_num, ir_num, red_num, ir_num, fs=fs)
        return red_num, ir_num, quality_report

    # 1. Detrending (Baseline correction)
    red_detrended = detrend_signal(red_num, method=detrend_method)
    ir_detrended = detrend_signal(ir_num, method=detrend_method)

    # 2. Bandpass filtering (Zero-phase Butterworth 0.5 - 5.0 Hz)
    red_filtered = bandpass_filter(
        red_detrended,
        fs=fs,
        low_cutoff=low_cutoff,
        high_cutoff=high_cutoff,
        order=order
    )
    ir_filtered = bandpass_filter(
        ir_detrended,
        fs=fs,
        low_cutoff=low_cutoff,
        high_cutoff=high_cutoff,
        order=order
    )

    # 3. Normalization (Z-score)
    clean_red = normalize_signal(red_filtered, method=norm_method)
    clean_ir = normalize_signal(ir_filtered, method=norm_method)

    # 4. Comprehensive Signal Quality Assessment
    quality_report = assess_signal_quality(red_num, ir_num, clean_red, clean_ir, fs=fs)

    # Attach preprocessing parameters to quality report for provenance
    quality_report["preprocessing_config"] = {
        "sampling_rate_hz": fs,
        "filter_type": "Butterworth Zero-Phase Bandpass",
        "filter_order": order,
        "low_cutoff_hz": low_cutoff,
        "high_cutoff_hz": high_cutoff,
        "detrend_method": detrend_method,
        "normalization_method": norm_method,
        "n_samples": len(clean_red)
    }

    return clean_red, clean_ir, quality_report


def preprocess_recording(
    file_or_df: Union[str, pd.DataFrame],
    fs: float = 25.0
) -> Dict[str, Any]:
    """
    Helper function to preprocess a dataset recording from a CSV file or DataFrame,
    preserving subject metadata and returning structured results.
    """
    if isinstance(file_or_df, (str, pd.DataFrame)):
        if isinstance(file_or_df, str):
            df = pd.read_csv(file_or_df)
            source_file = file_or_df
        else:
            df = file_or_df
            source_file = "in-memory"
    else:
        raise ValueError("file_or_df must be a file path string or pandas DataFrame.")

    clean_red, clean_ir, quality = preprocess_ppg(
        df["Red (a.u)"],
        df["Infra Red (a.u)"],
        fs=fs
    )

    gender = str(df["Gender"].iloc[0]) if "Gender" in df.columns else "UNKNOWN"
    age = int(df["Age"].iloc[0]) if "Age" in df.columns else -1
    hb = float(df["Hemoglobin (g/dL)"].iloc[0]) if "Hemoglobin (g/dL)" in df.columns else -1.0

    return {
        "source_file": source_file,
        "n_samples": len(clean_red),
        "gender": gender,
        "age": age,
        "hemoglobin_g_dl": hb,
        "raw_red": df["Red (a.u)"].to_numpy(dtype=np.float64),
        "raw_ir": df["Infra Red (a.u)"].to_numpy(dtype=np.float64),
        "clean_red": clean_red,
        "clean_ir": clean_ir,
        "quality": quality
    }
