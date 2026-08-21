"""
src/ppg package initialization
PRAHARI PPG / Hardware ML Pipeline
"""

from .preprocessing import (
    preprocess_ppg,
    preprocess_recording,
    bandpass_filter,
    detrend_signal,
    normalize_signal,
    convert_to_numeric,
)
from .quality import (
    assess_signal_quality,
    compute_spectral_cardiac_ratio,
)
from .features import (
    extract_ppg_features,
    extract_features_from_recording,
)
from .time_features import (
    extract_time_domain_stats,
    extract_pulse_morphology,
)
from .fft_features import (
    extract_fft_features,
)
from .cross_channel_features import (
    extract_cross_channel_features,
)
from .esp32 import (
    load_esp32_csv,
    validate_esp32_dataframe,
    predict_esp32_recording,
)

__all__ = [
    "preprocess_ppg",
    "preprocess_recording",
    "bandpass_filter",
    "detrend_signal",
    "normalize_signal",
    "convert_to_numeric",
    "assess_signal_quality",
    "compute_spectral_cardiac_ratio",
    "extract_ppg_features",
    "extract_features_from_recording",
    "extract_time_domain_stats",
    "extract_pulse_morphology",
    "extract_fft_features",
    "extract_cross_channel_features",
    "load_esp32_csv",
    "validate_esp32_dataframe",
    "predict_esp32_recording",
]
