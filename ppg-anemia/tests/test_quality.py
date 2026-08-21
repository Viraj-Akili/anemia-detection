"""
tests/test_quality.py
Unit tests for Signal Quality Assessment (Step 2).
"""

import pytest
import numpy as np
from src.ppg.quality import assess_signal_quality, compute_spectral_cardiac_ratio


def test_assess_signal_quality_good_signal(mock_valid_df):
    raw_red = mock_valid_df["Red (a.u)"].to_numpy()
    raw_ir = mock_valid_df["Infra Red (a.u)"].to_numpy()

    # Preprocessed normalized mock
    t = np.linspace(0, 10, len(raw_red))
    clean_red = np.sin(2 * np.pi * 1.2 * t)
    clean_ir = np.sin(2 * np.pi * 1.2 * t)

    res = assess_signal_quality(raw_red, raw_ir, clean_red, clean_ir, fs=25.0)
    assert res["status"] == "GOOD"
    assert res["is_usable"] is True
    assert len(res["reasons"]) == 0
    assert res["metrics"]["mean_cardiac_sqi"] > 0.60


def test_assess_signal_quality_nan_inf():
    # Signal containing NaNs
    red_nan = np.array([100.0, np.nan, 300.0] * 50)
    ir_nan = np.array([100.0, 200.0, 300.0] * 50)
    res_nan = assess_signal_quality(red_nan, ir_nan, red_nan, ir_nan, fs=25.0)
    assert res_nan["status"] == "REJECT"
    assert res_nan["is_usable"] is False
    assert any("NaN" in r for r in res_nan["reasons"])

    # Signal containing Infinities
    red_inf = np.array([100.0, np.inf, 300.0] * 50)
    ir_inf = np.array([100.0, 200.0, 300.0] * 50)
    res_inf = assess_signal_quality(red_inf, ir_inf, red_inf, ir_inf, fs=25.0)
    assert res_inf["status"] == "REJECT"
    assert res_inf["is_usable"] is False
    assert any("Infinite" in r for r in res_inf["reasons"])


def test_assess_signal_quality_insufficient_samples():
    # Less than 50 samples
    short_red = np.ones(30) * 100000
    short_ir = np.ones(30) * 100000
    res = assess_signal_quality(short_red, short_ir, np.zeros(30), np.zeros(30), fs=25.0)
    assert res["status"] == "REJECT"
    assert res["is_usable"] is False
    assert any("Insufficient samples" in r for r in res["reasons"])


def test_assess_signal_quality_flatline():
    # Constant flatline signal (sensor disconnected)
    flat_red = np.ones(250) * 115000.0
    flat_ir = np.ones(250) * 105000.0
    res = assess_signal_quality(flat_red, flat_ir, np.zeros(250), np.zeros(250), fs=25.0)
    assert res["status"] == "REJECT"
    assert res["is_usable"] is False
    assert any("flatline" in r.lower() for r in res["reasons"])


def test_compute_spectral_cardiac_ratio():
    fs = 25.0
    t = np.linspace(0, 10, 250)

    # Pure 1.25 Hz cardiac tone -> SQI should be close to 1.0
    pure_cardiac = np.sin(2 * np.pi * 1.25 * t)
    sqi_cardiac = compute_spectral_cardiac_ratio(pure_cardiac, fs=fs)
    assert sqi_cardiac > 0.90

    # High frequency 10 Hz noise tone -> SQI in 0.5-5.0 Hz should be near 0.0
    pure_noise = np.sin(2 * np.pi * 10.0 * t)
    sqi_noise = compute_spectral_cardiac_ratio(pure_noise, fs=fs)
    assert sqi_noise < 0.10
