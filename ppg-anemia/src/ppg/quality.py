"""
src/ppg/quality.py

PRAHARI PPG / Hardware ML Pipeline
STEP 2 — Signal Quality Assessment (SQI)

Evaluates optical Red and Infrared PPG signals across temporal, spectral,
and cross-channel morphological criteria.
Returns a standardized diagnostic dictionary with status: GOOD, WARNING, or REJECT.
"""

from typing import Dict, Any, List
import numpy as np


def compute_spectral_cardiac_ratio(signal: np.ndarray, fs: float = 25.0) -> float:
    """
    Calculate the ratio of spectral power in the physiological cardiac band (0.5 - 5.0 Hz)
    relative to total spectral power (0 - Nyquist Hz).
    """
    if len(signal) < 10:
        return 0.0

    # Detrend to remove DC spike before FFT
    sig_centered = signal - np.mean(signal)
    fft_vals = np.abs(np.fft.rfft(sig_centered)) ** 2
    freqs = np.fft.rfftfreq(len(signal), d=1.0 / fs)

    total_power = np.sum(fft_vals)
    if total_power < 1e-12:
        return 0.0

    in_band_mask = (freqs >= 0.5) & (freqs <= 5.0)
    cardiac_power = np.sum(fft_vals[in_band_mask])

    return float(cardiac_power / total_power)


def assess_signal_quality(
    raw_red: np.ndarray,
    raw_ir: np.ndarray,
    clean_red: np.ndarray,
    clean_ir: np.ndarray,
    fs: float = 25.0
) -> Dict[str, Any]:
    """
    Perform multi-dimensional signal quality assessment on raw and preprocessed PPG signals.
    
    Checks evaluated:
        1. NaN / Infinite values
        2. Sample count sufficiency
        3. Signal flatline / constant values
        4. Dynamic range & ADC clipping (MAX30102 18-bit range: 0 to 262,143)
        5. In-band cardiac spectral power ratio (Signal Quality Index)
        6. Red vs. Infrared cross-channel Pearson correlation
    
    Returns:
        Dictionary with:
            - status: 'GOOD', 'WARNING', or 'REJECT'
            - reasons: List of rejection reasons (if any)
            - warnings: List of non-blocking warnings (if any)
            - metrics: Dict of quantitative SQI metrics
    """
    reasons: List[str] = []
    warnings: List[str] = []

    # 1. NaN and Inf Checks
    has_nan = bool(np.isnan(raw_red).any() or np.isnan(raw_ir).any() or np.isnan(clean_red).any() or np.isnan(clean_ir).any())
    has_inf = bool(np.isinf(raw_red).any() or np.isinf(raw_ir).any() or np.isinf(clean_red).any() or np.isinf(clean_ir).any())

    if has_nan:
        reasons.append("NaN values detected in signal.")
    if has_inf:
        reasons.append("Infinite values detected in signal.")

    if has_nan or has_inf:
        return {
            "status": "REJECT",
            "is_usable": False,
            "reasons": reasons,
            "warnings": warnings,
            "metrics": {
                "n_samples": len(raw_red),
                "has_nan": has_nan,
                "has_inf": has_inf
            }
        }

    n_samples = len(raw_red)

    # 2. Sample Count Sufficiency
    if n_samples < 50:
        reasons.append(f"Insufficient samples ({n_samples} < 50 samples / 2.0 seconds at {fs} Hz).")
    elif n_samples < 150:
        warnings.append(f"Short recording duration ({n_samples} samples < 6.0 seconds).")

    # 3. Flatline / Near-Constant Signal Check
    raw_red_std = float(np.std(raw_red))
    raw_ir_std = float(np.std(raw_ir))
    clean_red_std = float(np.std(clean_red))
    clean_ir_std = float(np.std(clean_ir))

    if raw_red_std < 1.0 or raw_ir_std < 1.0 or clean_red_std < 1e-4 or clean_ir_std < 1e-4:
        reasons.append(f"Near-constant / flatline signal detected (Red std={raw_red_std:.2f}, IR std={raw_ir_std:.2f}).")

    # 4. Clipping / ADC Saturation Check (18-bit ADC limit: 262,143)
    red_max, red_min = float(np.max(raw_red)), float(np.min(raw_red))
    ir_max, ir_min = float(np.max(raw_ir)), float(np.min(raw_ir))

    if red_max >= 262000 or ir_max >= 262000:
        warnings.append("Potential sensor saturation (ADC count near 18-bit ceiling).")
    if red_min <= 100 or ir_min <= 100:
        warnings.append("Potential sensor disconnect / zero clipping (ADC count near floor).")

    # 5. In-Band Spectral Power Ratio (SQI)
    red_cardiac_sqi = compute_spectral_cardiac_ratio(clean_red, fs=fs)
    ir_cardiac_sqi = compute_spectral_cardiac_ratio(clean_ir, fs=fs)
    mean_cardiac_sqi = float((red_cardiac_sqi + ir_cardiac_sqi) / 2.0)

    if mean_cardiac_sqi < 0.35:
        reasons.append(f"Excessive noise: low cardiac band spectral power (mean SQI={mean_cardiac_sqi:.2f} < 0.35).")
    elif mean_cardiac_sqi < 0.55:
        warnings.append(f"Borderline signal noise (mean cardiac SQI={mean_cardiac_sqi:.2f}).")

    # 6. Red vs. Infrared Cross-Channel Correlation
    if clean_red_std > 1e-4 and clean_ir_std > 1e-4:
        corr_matrix = np.corrcoef(clean_red, clean_ir)
        red_ir_corr = float(corr_matrix[0, 1])
    else:
        red_ir_corr = 0.0

    if red_ir_corr < 0.0:
        warnings.append(f"Negative Red-IR cross-correlation (r={red_ir_corr:.2f}); possible optical artifact.")
    elif red_ir_corr < 0.30:
        warnings.append(f"Weak Red-IR cross-correlation (r={red_ir_corr:.2f}).")

    # Final Decision Logic
    if len(reasons) > 0:
        status = "REJECT"
        is_usable = False
    elif len(warnings) > 0:
        status = "WARNING"
        is_usable = True
    else:
        status = "GOOD"
        is_usable = True

    metrics = {
        "n_samples": n_samples,
        "raw_red_mean": float(np.mean(raw_red)),
        "raw_red_std": raw_red_std,
        "raw_ir_mean": float(np.mean(raw_ir)),
        "raw_ir_std": raw_ir_std,
        "red_cardiac_sqi": round(red_cardiac_sqi, 3),
        "ir_cardiac_sqi": round(ir_cardiac_sqi, 3),
        "mean_cardiac_sqi": round(mean_cardiac_sqi, 3),
        "red_ir_cross_correlation": round(red_ir_corr, 3),
        "has_nan": False,
        "has_inf": False
    }

    return {
        "status": status,
        "is_usable": is_usable,
        "reasons": reasons,
        "warnings": warnings,
        "metrics": metrics
    }
