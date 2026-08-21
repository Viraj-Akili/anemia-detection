"""
tests/test_features.py
Unit tests for PPG Feature Extraction (Step 3).
"""

import pytest
import numpy as np
import pandas as pd
from src.ppg.features import extract_ppg_features, extract_features_from_recording
from src.ppg.time_features import extract_time_domain_stats, extract_pulse_morphology
from src.ppg.fft_features import extract_fft_features
from src.ppg.cross_channel_features import extract_cross_channel_features


def test_extract_time_domain_stats(mock_valid_df):
    clean_red = mock_valid_df["Red (a.u)"].to_numpy(dtype=np.float64)
    stats = extract_time_domain_stats(clean_red, prefix="red")

    expected_keys = [
        "red_mean", "red_std", "red_var", "red_rms", "red_min", "red_max",
        "red_range", "red_median", "red_q25", "red_q75", "red_iqr",
        "red_skewness", "red_kurtosis", "red_zero_crossing_rate"
    ]
    for k in expected_keys:
        assert k in stats
        assert isinstance(stats[k], float)
        assert not np.isnan(stats[k])


def test_extract_pulse_morphology(mock_valid_df):
    # Create clean synthetic wave with 12 pulses in 10s (1.2 Hz)
    t = np.linspace(0, 10, 250)
    sig = np.sin(2 * np.pi * 1.2 * t)
    morph = extract_pulse_morphology(sig, fs=25.0, prefix="red")

    assert morph["red_n_pulses"] >= 10
    assert 60.0 <= morph["red_pulse_rate_bpm"] <= 85.0
    assert morph["red_mean_pulse_interval_sec"] > 0.5


def test_extract_fft_features():
    fs = 25.0
    t = np.linspace(0, 10, 250)
    freq = 1.30  # 1.30 Hz (78 BPM)
    sig = np.sin(2 * np.pi * freq * t)

    fft_feat = extract_fft_features(sig, fs=fs, prefix="red")

    assert abs(fft_feat["red_fft_dominant_freq_hz"] - 1.30) < 0.15
    assert abs(fft_feat["red_fft_dominant_freq_bpm"] - 78.0) < 10.0
    assert fft_feat["red_fft_cardiac_power_ratio"] > 0.85
    assert not np.isnan(fft_feat["red_fft_spectral_entropy"])


def test_extract_cross_channel_features():
    # Synthetic Red and IR signals
    raw_red = np.array([115000 + 500 * np.sin(i * 0.3) for i in range(250)], dtype=np.float64)
    raw_ir = np.array([105000 + 600 * np.sin(i * 0.3) for i in range(250)], dtype=np.float64)

    clean_red = np.sin(np.arange(250) * 0.3)
    clean_ir = np.sin(np.arange(250) * 0.3)

    cross = extract_cross_channel_features(raw_red, raw_ir, clean_red, clean_ir)

    assert "ratio_of_ratios" in cross
    assert cross["red_ir_pearson_corr"] > 0.99
    assert cross["ratio_of_ratios"] > 0.0
    assert not np.isnan(cross["ratio_of_ratios"])


def test_extract_ppg_features_master(mock_valid_df):
    raw_red = mock_valid_df["Red (a.u)"]
    raw_ir = mock_valid_df["Infra Red (a.u)"]

    features = extract_ppg_features(raw_red, raw_ir, fs=25.0)

    assert isinstance(features, dict)
    assert len(features) == 72  # 72 optical signal features
    assert all(not np.isnan(v) for v in features.values())
    assert all(not np.isinf(v) for v in features.values())


def test_extract_ppg_features_determinism(mock_valid_df):
    raw_red = mock_valid_df["Red (a.u)"]
    raw_ir = mock_valid_df["Infra Red (a.u)"]

    f1 = extract_ppg_features(raw_red, raw_ir, fs=25.0)
    f2 = extract_ppg_features(raw_red, raw_ir, fs=25.0)

    for k in f1:
        assert f1[k] == f2[k], f"Mismatch in feature {k}"
