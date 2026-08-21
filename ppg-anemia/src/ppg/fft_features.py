"""
src/ppg/fft_features.py

PRAHARI PPG / Hardware ML Pipeline
STEP 3 — Frequency-Domain (FFT) Feature Extraction

Extracts spectral power distributions, dominant cardiac frequency, spectral centroid,
bandwidth, and entropy from PPG signals.

NOTE ON FREQUENCY RESOLUTION:
At sampling rate fs = 25 Hz and recording length N = 250 samples,
the theoretical frequency bin resolution is df = fs / N = 0.1 Hz (~6.0 BPM).
"""

from typing import Dict, Any
import numpy as np


def extract_fft_features(
    signal: np.ndarray,
    fs: float = 25.0,
    prefix: str = "red",
    cardiac_low: float = 0.5,
    cardiac_high: float = 5.0
) -> Dict[str, float]:
    """
    Extract frequency-domain features using real FFT on the preprocessed PPG signal.
    
    Parameters:
        signal: 1D numpy array of preprocessed signal samples.
        fs: Sampling frequency in Hz (25 Hz).
        prefix: Channel prefix ('red' or 'ir').
        cardiac_low: Lower cardiac band cutoff (0.5 Hz / 30 BPM).
        cardiac_high: Upper cardiac band cutoff (5.0 Hz / 300 BPM).
    
    Features extracted:
        - dominant_freq_hz: Peak frequency in cardiac band.
        - dominant_freq_magnitude: Magnitude of dominant peak.
        - dominant_freq_bpm: Peak frequency converted to BPM.
        - total_spectral_power: Total power across all frequencies.
        - cardiac_band_power: Power within the 0.5 - 5.0 Hz band.
        - cardiac_power_ratio: Cardiac power / total power (SQI).
        - spectral_centroid: Center of spectral mass.
        - spectral_bandwidth: Spectral spread around centroid.
        - spectral_entropy: Normalized Shannon spectral entropy.
        - peak_to_total_power_ratio: Dominant peak power relative to total power.
    """
    if len(signal) < 10:
        return {
            f"{prefix}_fft_dominant_freq_hz": 0.0,
            f"{prefix}_fft_dominant_freq_magnitude": 0.0,
            f"{prefix}_fft_dominant_freq_bpm": 0.0,
            f"{prefix}_fft_total_spectral_power": 0.0,
            f"{prefix}_fft_cardiac_band_power": 0.0,
            f"{prefix}_fft_cardiac_power_ratio": 0.0,
            f"{prefix}_fft_spectral_centroid": 0.0,
            f"{prefix}_fft_spectral_bandwidth": 0.0,
            f"{prefix}_fft_spectral_entropy": 0.0,
            f"{prefix}_fft_peak_to_total_power_ratio": 0.0,
        }

    # Center signal before FFT to eliminate DC component
    sig_centered = signal - np.mean(signal)
    n = len(sig_centered)
    fft_complex = np.fft.rfft(sig_centered)
    fft_mag = np.abs(fft_complex)
    fft_power = fft_mag ** 2
    freqs = np.fft.rfftfreq(n, d=1.0 / fs)

    total_power = float(np.sum(fft_power))
    if total_power < 1e-12:
        return {
            f"{prefix}_fft_dominant_freq_hz": 0.0,
            f"{prefix}_fft_dominant_freq_magnitude": 0.0,
            f"{prefix}_fft_dominant_freq_bpm": 0.0,
            f"{prefix}_fft_total_spectral_power": 0.0,
            f"{prefix}_fft_cardiac_band_power": 0.0,
            f"{prefix}_fft_cardiac_power_ratio": 0.0,
            f"{prefix}_fft_spectral_centroid": 0.0,
            f"{prefix}_fft_spectral_bandwidth": 0.0,
            f"{prefix}_fft_spectral_entropy": 0.0,
            f"{prefix}_fft_peak_to_total_power_ratio": 0.0,
        }

    # Cardiac band mask (0.5 to 5.0 Hz)
    cardiac_mask = (freqs >= cardiac_low) & (freqs <= cardiac_high)
    cardiac_power = float(np.sum(fft_power[cardiac_mask]))
    cardiac_ratio = float(cardiac_power / total_power)

    # Dominant peak within cardiac band
    if np.any(cardiac_mask) and np.max(fft_mag[cardiac_mask]) > 1e-6:
        cardiac_freqs = freqs[cardiac_mask]
        cardiac_mags = fft_mag[cardiac_mask]
        cardiac_powers = fft_power[cardiac_mask]
        peak_idx = int(np.argmax(cardiac_mags))
        dom_freq = float(cardiac_freqs[peak_idx])
        dom_mag = float(cardiac_mags[peak_idx])
        dom_power = float(cardiac_powers[peak_idx])
    else:
        dom_freq = 0.0
        dom_mag = 0.0
        dom_power = 0.0

    dom_bpm = float(dom_freq * 60.0)
    peak_to_total = float(dom_power / total_power)

    # Spectral Centroid: sum(f * P(f)) / sum(P(f))
    spectral_centroid = float(np.sum(freqs * fft_power) / total_power)

    # Spectral Bandwidth: sqrt(sum((f - centroid)^2 * P(f)) / sum(P(f)))
    spectral_bandwidth = float(np.sqrt(np.sum(((freqs - spectral_centroid) ** 2) * fft_power) / total_power))

    # Normalized Spectral Entropy: -sum(p * log2(p)) / log2(K)
    psd_norm = fft_power / total_power
    psd_norm_nonzero = psd_norm[psd_norm > 1e-12]
    k_bins = len(freqs)
    if k_bins > 1:
        entropy = float(-np.sum(psd_norm_nonzero * np.log2(psd_norm_nonzero)) / np.log2(k_bins))
    else:
        entropy = 0.0

    return {
        f"{prefix}_fft_dominant_freq_hz": round(dom_freq, 3),
        f"{prefix}_fft_dominant_freq_magnitude": round(dom_mag, 4),
        f"{prefix}_fft_dominant_freq_bpm": round(dom_bpm, 1),
        f"{prefix}_fft_total_spectral_power": round(total_power, 4),
        f"{prefix}_fft_cardiac_band_power": round(cardiac_power, 4),
        f"{prefix}_fft_cardiac_power_ratio": round(cardiac_ratio, 4),
        f"{prefix}_fft_spectral_centroid": round(spectral_centroid, 3),
        f"{prefix}_fft_spectral_bandwidth": round(spectral_bandwidth, 3),
        f"{prefix}_fft_spectral_entropy": round(entropy, 4),
        f"{prefix}_fft_peak_to_total_power_ratio": round(peak_to_total, 4),
    }
