"""
tests/test_preprocessing.py
Unit tests for PPG preprocessing and filtering (Step 2).
"""

import pytest
import numpy as np
import pandas as pd
import hashlib
from pathlib import Path
from src.ppg.preprocessing import (
    convert_to_numeric,
    detrend_signal,
    bandpass_filter,
    normalize_signal,
    preprocess_ppg,
    preprocess_recording
)


def test_convert_to_numeric():
    # List input
    arr_list = convert_to_numeric([100, 200, 300])
    assert isinstance(arr_list, np.ndarray)
    assert arr_list.dtype == np.float64
    assert len(arr_list) == 3

    # Pandas series with string representation of numbers
    series = pd.Series(["1000", "2000", "3000"])
    arr_series = convert_to_numeric(series)
    assert np.allclose(arr_series, [1000.0, 2000.0, 3000.0])


def test_detrend_signal():
    t = np.linspace(0, 10, 250)
    # Signal with linear DC drift: y = 500*t + sine
    linear_drift = 500 * t
    sine_wave = 100 * np.sin(2 * np.pi * 1.2 * t)
    raw = 100000 + linear_drift + sine_wave

    detrended = detrend_signal(raw, method="linear")
    # Mean of detrended signal should be approximately 0
    assert abs(np.mean(detrended)) < 1e-3
    assert len(detrended) == len(raw)


def test_bandpass_filter_preserves_length():
    fs = 25.0
    t = np.linspace(0, 10, 250)
    sig = 110000 + 1000 * np.sin(2 * np.pi * 1.2 * t)

    filtered = bandpass_filter(sig, fs=fs, low_cutoff=0.5, high_cutoff=5.0, order=3)
    assert len(filtered) == 250
    assert not np.isnan(filtered).any()
    assert not np.isinf(filtered).any()


def test_bandpass_filter_zero_phase():
    """Verify zero phase lag on a synthetic cardiac sine wave via cross-correlation."""
    fs = 25.0
    t = np.arange(250) / fs
    freq = 1.25  # 1.25 Hz cardiac fundamental (75 BPM)
    pure_sine = np.sin(2 * np.pi * freq * t)

    filtered = bandpass_filter(pure_sine, fs=fs, low_cutoff=0.5, high_cutoff=5.0, order=3)

    # In a zero-phase filter, the cross-correlation peak between input and output must be at lag 0
    corr = np.correlate(pure_sine - np.mean(pure_sine), filtered - np.mean(filtered), mode="full")
    lags = np.arange(-len(pure_sine) + 1, len(pure_sine))
    best_lag = lags[np.argmax(corr)]

    assert best_lag == 0, f"Expected 0 sample lag for zero-phase filter, got {best_lag}"


def test_normalize_signal_zscore():
    data = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
    norm = normalize_signal(data, method="zscore")
    assert abs(np.mean(norm)) < 1e-6
    assert abs(np.std(norm) - 1.0) < 1e-6


def test_preprocess_ppg_sample_counts_and_channels(mock_valid_df):
    red = mock_valid_df["Red (a.u)"]
    ir = mock_valid_df["Infra Red (a.u)"]

    # Test 250-sample recording
    clean_red_250, clean_ir_250, q250 = preprocess_ppg(red, ir, fs=25.0)
    assert len(clean_red_250) == 250
    assert len(clean_ir_250) == 250
    assert not np.isnan(clean_red_250).any()
    assert not np.isnan(clean_ir_250).any()
    assert q250["status"] == "GOOD"

    # Test 249-sample recording (length preservation)
    clean_red_249, clean_ir_249, q249 = preprocess_ppg(red.iloc[:249], ir.iloc[:249], fs=25.0)
    assert len(clean_red_249) == 249
    assert len(clean_ir_249) == 249


def test_preprocess_ppg_hardware_api_compatibility():
    """Verify that preprocess_ppg accepts plain python lists, numpy arrays, and pandas Series."""
    raw_list_red = [115000 + int(200 * np.sin(i * 0.3)) for i in range(250)]
    raw_list_ir = [105000 + int(250 * np.sin(i * 0.3)) for i in range(250)]

    c_red, c_ir, q = preprocess_ppg(raw_list_red, raw_list_ir, fs=25.0)
    assert isinstance(c_red, np.ndarray)
    assert isinstance(c_ir, np.ndarray)
    assert len(c_red) == 250
    assert q["is_usable"] is True


def test_preprocessing_determinism(mock_valid_df):
    """Verify that preprocessing is 100% deterministic."""
    red = mock_valid_df["Red (a.u)"]
    ir = mock_valid_df["Infra Red (a.u)"]

    r1, i1, q1 = preprocess_ppg(red, ir, fs=25.0)
    r2, i2, q2 = preprocess_ppg(red, ir, fs=25.0)

    np.testing.assert_array_equal(r1, r2)
    np.testing.assert_array_equal(i1, i2)
    assert q1["status"] == q2["status"]


def test_raw_data_immutability(tmp_path, mock_valid_df):
    """Verify that calling preprocess_recording on a raw CSV does not modify the raw file on disk."""
    raw_file = tmp_path / "1.csv"
    mock_valid_df.to_csv(raw_file, index=False)

    with open(raw_file, "rb") as f:
        before_hash = hashlib.sha256(f.read()).hexdigest()

    result = preprocess_recording(str(raw_file), fs=25.0)
    assert result["n_samples"] == 250

    with open(raw_file, "rb") as f:
        after_hash = hashlib.sha256(f.read()).hexdigest()

    assert before_hash == after_hash, "Raw file was modified during preprocessing!"
