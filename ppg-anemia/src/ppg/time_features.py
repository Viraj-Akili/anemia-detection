"""
src/ppg/time_features.py

PRAHARI PPG / Hardware ML Pipeline
STEP 3 — Time-Domain & Pulse Morphology Feature Extraction

Extracts statistical moments, amplitude extremes, and physiological pulse
morphology metrics from preprocessed 1D PPG signals.
"""

from typing import Dict, Any
import numpy as np
import scipy.stats
import scipy.signal


def extract_time_domain_stats(signal: np.ndarray, prefix: str = "red") -> Dict[str, float]:
    """
    Extract statistical moments and amplitude distribution metrics from a 1D PPG signal.
    
    Features extracted:
        - mean, std, var, rms
        - min, max, peak_to_peak_range
        - median, q25, q75, iqr
        - skewness, kurtosis
        - zero_crossing_rate
    """
    if len(signal) == 0:
        return {}

    mean_val = float(np.mean(signal))
    std_val = float(np.std(signal))
    var_val = float(np.var(signal))
    rms_val = float(np.sqrt(np.mean(signal ** 2)))
    min_val = float(np.min(signal))
    max_val = float(np.max(signal))
    range_val = max_val - min_val

    median_val = float(np.median(signal))
    q25 = float(np.percentile(signal, 25))
    q75 = float(np.percentile(signal, 75))
    iqr_val = q75 - q25

    # Higher-order statistical moments
    skew_val = float(scipy.stats.skew(signal)) if std_val > 1e-6 else 0.0
    kurt_val = float(scipy.stats.kurtosis(signal)) if std_val > 1e-6 else 0.0

    # Zero crossings (centered around mean)
    centered = signal - mean_val
    zero_crossings = int(np.sum(np.diff(np.signbit(centered)) != 0))
    zcr = float(zero_crossings / (len(signal) - 1)) if len(signal) > 1 else 0.0

    return {
        f"{prefix}_mean": round(mean_val, 6),
        f"{prefix}_std": round(std_val, 6),
        f"{prefix}_var": round(var_val, 6),
        f"{prefix}_rms": round(rms_val, 6),
        f"{prefix}_min": round(min_val, 6),
        f"{prefix}_max": round(max_val, 6),
        f"{prefix}_range": round(range_val, 6),
        f"{prefix}_median": round(median_val, 6),
        f"{prefix}_q25": round(q25, 6),
        f"{prefix}_q75": round(q75, 6),
        f"{prefix}_iqr": round(iqr_val, 6),
        f"{prefix}_skewness": round(skew_val, 6),
        f"{prefix}_kurtosis": round(kurt_val, 6),
        f"{prefix}_zero_crossing_rate": round(zcr, 6),
    }


def extract_pulse_morphology(
    signal: np.ndarray,
    fs: float = 25.0,
    prefix: str = "red"
) -> Dict[str, float]:
    """
    Detect individual systolic peaks and compute cardiac pulse morphological metrics.
    
    Parameters:
        signal: Clean normalized PPG signal.
        fs: Sampling frequency in Hz (25 Hz).
        prefix: Channel prefix ('red' or 'ir').
    
    Features extracted:
        - n_pulses: Number of detected systolic peaks.
        - mean_pulse_interval_sec: Mean RR interval in seconds.
        - pulse_rate_bpm: Heart rate derived from peak intervals.
        - pulse_amplitude_mean: Mean peak height relative to adjacent baseline.
        - pulse_amplitude_std: Variability of systolic peak amplitudes.
        - pulse_interval_std: Standard deviation of inter-beat intervals (PRV indicator).
    """
    if len(signal) < 20:
        return {
            f"{prefix}_n_pulses": 0.0,
            f"{prefix}_mean_pulse_interval_sec": 0.0,
            f"{prefix}_pulse_rate_bpm": 0.0,
            f"{prefix}_pulse_amplitude_mean": 0.0,
            f"{prefix}_pulse_amplitude_std": 0.0,
            f"{prefix}_pulse_interval_std": 0.0,
        }

    # Minimum distance between heartbeats: 0.40 seconds = 10 samples @ 25 Hz (max 150 BPM)
    min_distance = max(4, int(fs * 0.40))
    peaks, properties = scipy.signal.find_peaks(
        signal,
        distance=min_distance,
        prominence=0.5
    )

    n_peaks = len(peaks)
    if n_peaks >= 2:
        intervals_sec = np.diff(peaks) / fs
        mean_interval = float(np.mean(intervals_sec))
        std_interval = float(np.std(intervals_sec))
        hr_bpm = float(60.0 / mean_interval) if mean_interval > 0.1 else 0.0

        # Peak amplitudes
        peak_heights = signal[peaks]
        mean_amp = float(np.mean(peak_heights))
        std_amp = float(np.std(peak_heights))
    elif n_peaks == 1:
        mean_interval = float(len(signal) / fs)
        std_interval = 0.0
        hr_bpm = float(60.0 / mean_interval)
        mean_amp = float(signal[peaks[0]])
        std_amp = 0.0
    else:
        mean_interval = 0.0
        std_interval = 0.0
        hr_bpm = 0.0
        mean_amp = 0.0
        std_amp = 0.0

    return {
        f"{prefix}_n_pulses": float(n_peaks),
        f"{prefix}_mean_pulse_interval_sec": round(mean_interval, 4),
        f"{prefix}_pulse_rate_bpm": round(hr_bpm, 2),
        f"{prefix}_pulse_amplitude_mean": round(mean_amp, 4),
        f"{prefix}_pulse_amplitude_std": round(std_amp, 4),
        f"{prefix}_pulse_interval_std": round(std_interval, 4),
    }
