# Feature Quality Audit Report — PRAHARI PPG Pipeline

## 1. Summary Statistics
- **Total Subject Recordings Evaluated**: 68
- **Total ML Features Extracted**: 74
- **Target Column**: `hemoglobin_g_dl` (Isolated)

### Feature Breakdown by Category:
- **Time-Domain Statistics**: 28 features
- **Frequency-Domain (FFT)**: 20 features
- **Pulse Morphology**: 12 features
- **Cross-Channel & Optical Ratios**: 12 features
- **Demographic**: 2 features

---

## 2. Data Cleanliness & Integrity Audit
- **NaN / Missing Values**: None (0 across all features)
- **Infinite Values**: None (0 across all features)
- **Constant Features (std = 0)**: 9 (red_mean, red_std, red_var, red_rms, ir_mean, ir_std, ir_var, ir_rms, red_ir_amplitude_ratio)
- **Low-Variance Features (std < 1e-4)**: 0 (None)
- **Highly Collinear Feature Pairs (|r| > 0.98)**: 17 pairs identified

### Notes on Constant/Normalized Features:
- `red_std`, `ir_std`, `red_var`, `ir_var` on clean signals have standard deviation 0 across recordings because signals undergo per-recording Z-score normalization ($std=1.0$). These constants are safely handled by standard scalers or tree models.
- Raw optical metrics (`red_raw_dc`, `red_raw_ac`, `ir_raw_dc`, `ir_raw_ac`, `ratio_of_ratios`) retain dynamic unnormalized physical variations.

---

## 3. Sample Highly Correlated Feature Pairs (|r| > 0.98)
| Feature 1 | Feature 2 | Pearson |r| |
|---|---|---|
| `red_n_pulses` | `red_pulse_rate_bpm` | 0.9876 |
| `red_n_pulses` | `ir_n_pulses` | 0.9862 |
| `red_pulse_rate_bpm` | `ir_n_pulses` | 0.9832 |
| `red_mean_pulse_interval_sec` | `ir_mean_pulse_interval_sec` | 0.9809 |
| `red_pulse_rate_bpm` | `ir_pulse_rate_bpm` | 0.9921 |
| `ir_n_pulses` | `ir_pulse_rate_bpm` | 0.9892 |
| `red_fft_dominant_freq_hz` | `red_fft_dominant_freq_bpm` | 1.0000 |
| `red_fft_dominant_freq_magnitude` | `red_fft_peak_to_total_power_ratio` | 0.9927 |
| `red_fft_dominant_freq_hz` | `ir_fft_dominant_freq_hz` | 0.9981 |
| `red_fft_dominant_freq_bpm` | `ir_fft_dominant_freq_hz` | 0.9981 |