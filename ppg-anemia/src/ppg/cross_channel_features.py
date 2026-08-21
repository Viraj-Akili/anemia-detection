"""
src/ppg/cross_channel_features.py

PRAHARI PPG / Hardware ML Pipeline
STEP 3 — Red/Infrared Cross-Channel & Optical Relationship Features

Extracts optical extinction ratios, AC/DC modulation depths, Pearson cross-correlation,
and spectrophotometric Ratio-of-Ratios (R) from raw and preprocessed dual-wavelength signals.
"""

from typing import Dict, Any
import numpy as np


def extract_cross_channel_features(
    raw_red: np.ndarray,
    raw_ir: np.ndarray,
    clean_red: np.ndarray,
    clean_ir: np.ndarray
) -> Dict[str, float]:
    """
    Extract dual-wavelength optical relationship features.
    
    Features extracted:
        - red_ir_pearson_corr: Pearson correlation between clean Red and IR.
        - red_ir_amplitude_ratio: Ratio of clean Red std to clean IR std.
        - red_raw_dc, red_raw_ac, red_ac_dc_ratio: Red optical modulation depth.
        - ir_raw_dc, ir_raw_ac, ir_ac_dc_ratio: IR optical modulation depth.
        - ratio_of_ratios: Spectrophotometric ratio R = (AC_red/DC_red) / (AC_ir/DC_ir).
        - clean_red_ir_ratio_mean: Mean of clean Red / (clean IR + epsilon).
        - clean_red_ir_ratio_std: Std of clean Red / (clean IR + epsilon).
        - red_ir_peak_lag_samples: Temporal lag (in samples) of maximum cross-correlation.
    """
    if len(clean_red) == 0 or len(clean_ir) == 0:
        return {}

    # 1. Pearson Correlation between clean signals
    std_r = np.std(clean_red)
    std_i = np.std(clean_ir)
    if std_r > 1e-6 and std_i > 1e-6:
        r_matrix = np.corrcoef(clean_red, clean_ir)
        pearson_corr = float(r_matrix[0, 1])
    else:
        pearson_corr = 0.0

    # 2. Clean Amplitude Ratio
    amp_ratio = float(std_r / std_i) if std_i > 1e-6 else 0.0

    # 3. Raw AC/DC Metrics
    red_dc = float(np.mean(raw_red))
    red_ac = float(np.std(raw_red))
    red_ac_dc = float(red_ac / red_dc) if red_dc > 1e-6 else 0.0

    ir_dc = float(np.mean(raw_ir))
    ir_ac = float(np.std(raw_ir))
    ir_ac_dc = float(ir_ac / ir_dc) if ir_dc > 1e-6 else 0.0

    # 4. Classical Spectrophotometric Ratio of Ratios (R)
    ratio_of_ratios = float(red_ac_dc / ir_ac_dc) if ir_ac_dc > 1e-8 else 0.0

    # 5. Pointwise clean ratio (with safe epsilon denominator)
    safe_ir = clean_ir + np.sign(clean_ir) * 1e-4 + 1e-4
    pointwise_ratio = clean_red / safe_ir
    clean_ratio_mean = float(np.mean(pointwise_ratio))
    clean_ratio_std = float(np.std(pointwise_ratio))

    # 6. Cross-Correlation Lag
    corr = np.correlate(clean_red - np.mean(clean_red), clean_ir - np.mean(clean_ir), mode="full")
    lags = np.arange(-len(clean_red) + 1, len(clean_red))
    peak_lag = int(lags[np.argmax(corr)])

    return {
        "red_ir_pearson_corr": round(pearson_corr, 4),
        "red_ir_amplitude_ratio": round(amp_ratio, 4),
        "red_raw_dc": round(red_dc, 2),
        "red_raw_ac": round(red_ac, 4),
        "red_ac_dc_ratio": round(red_ac_dc, 6),
        "ir_raw_dc": round(ir_dc, 2),
        "ir_raw_ac": round(ir_ac, 4),
        "ir_ac_dc_ratio": round(ir_ac_dc, 6),
        "ratio_of_ratios": round(ratio_of_ratios, 4),
        "clean_red_ir_ratio_mean": round(clean_ratio_mean, 4),
        "clean_red_ir_ratio_std": round(clean_ratio_std, 4),
        "red_ir_peak_lag_samples": peak_lag,
    }
