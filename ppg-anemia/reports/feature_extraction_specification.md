# Feature Extraction & Model Specification — PRAHARI PPG Pipeline

## 1. Overview & Objectives
This document specifies the feature extraction methodology, mathematical formulations, feature categories, and regression modeling protocol developed for **STEP 3** of the **PRAHARI** non-invasive anemia screening pipeline.

The feature engineering module (`src/ppg/`) processes dual-wavelength (Red and Infrared) PPG signals and extracts a total of **74 machine learning features** ($72\text{ optical/signal features} + 2\text{ demographic covariates}$) per 10-second recording window.

---

## 2. Feature Definitions & Mathematical Formulations

### Category 1: Time-Domain Statistical Metrics (28 features: 14 Red + 14 IR)
Extracted independently from preprocessed zero-phase bandpass-filtered signals ($x[n]$):

| Feature Name | Mathematical Definition | Signal Processing Interpretation |
|---|---|---|
| `{ch}_mean` | $\mu = \frac{1}{N}\sum_{n=1}^N x[n]$ | Central tendency (near 0 due to baseline correction). |
| `{ch}_std` | $\sigma = \sqrt{\frac{1}{N}\sum (x[n] - \mu)^2}$ | Standard deviation / AC pulsatile amplitude dispersion. |
| `{ch}_var` | $\sigma^2$ | Signal power / variance. |
| `{ch}_rms` | $\text{RMS} = \sqrt{\frac{1}{N}\sum x[n]^2}$ | Root Mean Square energy. |
| `{ch}_min`, `{ch}_max` | $\min(x)$, $\max(x)$ | Minimum diastolic trough & maximum systolic peak. |
| `{ch}_range` | $\max(x) - \min(x)$ | Peak-to-peak dynamic range. |
| `{ch}_median` | $\text{Median}(x)$ | Robust median amplitude. |
| `{ch}_q25`, `{ch}_q75` | 25th and 75th percentiles | Interquartile boundary values. |
| `{ch}_iqr` | $Q_{75} - Q_{25}$ | Robust non-parametric dispersion. |
| `{ch}_skewness` | $\gamma_1 = \frac{1}{N}\sum (\frac{x[n] - \mu}{\sigma})^3$ | Pulse waveform asymmetry (systolic upstroke vs diastolic decay). |
| `{ch}_kurtosis` | $\gamma_2 = \frac{1}{N}\sum (\frac{x[n] - \mu}{\sigma})^4 - 3$ | Peakedness / sharpness of systolic peaks. |
| `{ch}_zero_crossing_rate` | $\text{ZCR} = \frac{1}{N-1}\sum \mathbb{I}(\text{sign}(x[n]) \ne \text{sign}(x[n-1]))$ | Rate of zero-axis crossings (frequency indicator). |

---

### Category 2: Pulse Morphology & Heart Rate (12 features: 6 Red + 6 IR)
Derived via peak detection on systolic waves (`scipy.signal.find_peaks` with distance threshold 0.40s / max 150 BPM):

| Feature Name | Definition | Physiological Interpretation |
|---|---|---|
| `{ch}_n_pulses` | $K = \text{count}(\text{peaks})$ | Total cardiac pulse cycles detected in 10.0 seconds. |
| `{ch}_mean_pulse_interval_sec` | $\overline{\text{RR}} = \frac{1}{K-1}\sum (t_{k+1} - t_k)$ | Mean cardiac cycle period (in seconds). |
| `{ch}_pulse_rate_bpm` | $\text{HR} = \frac{60}{\overline{\text{RR}}}$ | Estimated heart rate in beats per minute. |
| `{ch}_pulse_amplitude_mean` | $\overline{A} = \frac{1}{K}\sum x[p_k]$ | Average height of systolic pulse peaks. |
| `{ch}_pulse_amplitude_std` | $\sigma_A = \text{std}(x[p_k])$ | Beat-to-beat stroke volume / amplitude variability. |
| `{ch}_pulse_interval_std` | $\text{SDNN} = \text{std}(\Delta t_k)$ | Pulse rate variability (PRV) metric. |

---

### Category 3: Frequency-Domain (FFT) Metrics (20 features: 10 Red + 10 IR)
Computed using Real Fast Fourier Transform ($f_s = 25\text{ Hz}$, $N = 250$, $\Delta f = 0.1\text{ Hz} \approx 6\text{ BPM}$):

| Feature Name | Definition | Interpretation |
|---|---|---|
| `{ch}_fft_dominant_freq_hz` | $f_{dom} = \arg\max_{f \in [0.5, 5]} |X(f)|$ | Fundamental cardiac frequency ($f_{dom}$). |
| `{ch}_fft_dominant_freq_bpm` | $f_{dom} \times 60$ | Spectral heart rate (Resolution: $\pm 6\text{ BPM}$). |
| `{ch}_fft_dominant_freq_magnitude` | $|X(f_{dom})|$ | Magnitude of the primary systolic harmonic. |
| `{ch}_fft_total_spectral_power` | $P_{tot} = \sum_{f=0}^{f_{nyq}} |X(f)|^2$ | Total broadband signal energy. |
| `{ch}_fft_cardiac_band_power` | $P_{cardiac} = \sum_{f=0.5}^{5.0} |X(f)|^2$ | Energy in physiological cardiac band ($0.5 - 5.0\text{ Hz}$). |
| `{ch}_fft_cardiac_power_ratio` | $\text{SQI} = P_{cardiac} / P_{tot}$ | Signal Quality Index (Spectral purity). |
| `{ch}_fft_spectral_centroid` | $f_c = \frac{\sum f |X(f)|^2}{P_{tot}}$ | Center of mass of the power spectrum. |
| `{ch}_fft_spectral_bandwidth` | $\sigma_f = \sqrt{\frac{\sum (f - f_c)^2 |X(f)|^2}{P_{tot}}}$ | Spectral spread around the centroid. |
| `{ch}_fft_spectral_entropy` | $H = -\frac{1}{\log_2 K}\sum p_k \log_2 p_k$ | Spectral complexity / randomness of waveform. |
| `{ch}_fft_peak_to_total_power_ratio` | $|X(f_{dom})|^2 / P_{tot}$ | Concentration of energy in fundamental pulse. |

---

### Category 4: Cross-Channel & Optical Extinction Ratios (12 features)
Exploiting differential optical absorption of oxygenated ($HbO_2$) and deoxygenated ($Hb$) hemoglobin:

| Feature Name | Mathematical Definition | Clinical / Optical Significance |
|---|---|---|
| `red_ir_pearson_corr` | $r = \frac{\text{cov}(x_{red}, x_{ir})}{\sigma_{red}\sigma_{ir}}$ | Synchronicity between Red and IR pulsatile absorption. |
| `red_ir_amplitude_ratio` | $\sigma_{clean, red} / \sigma_{clean, ir}$ | Relative AC pulsatile amplitude ratio. |
| `red_raw_dc`, `ir_raw_dc` | $\mu_{raw, red}$, $\mu_{raw, ir}$ | Transmitted DC light baseline (tissue/bone absorption). |
| `red_raw_ac`, `ir_raw_ac` | $\sigma_{raw, red}$, $\sigma_{raw, ir}$ | Arterial pulsatile AC modulation depth. |
| `red_ac_dc_ratio` | $\text{AC}_{red} / \text{DC}_{red}$ | Normalized Red optical modulation depth. |
| `ir_ac_dc_ratio` | $\text{AC}_{ir} / \text{DC}_{ir}$ | Normalized IR optical modulation depth. |
| `ratio_of_ratios` ($R$) | $R = \frac{\text{AC}_{red}/\text{DC}_{red}}{\text{AC}_{ir}/\text{DC}_{ir}}$ | **Spectrophotometric Ratio of Ratios**: Fundamental pulse oximeter optical extinction ratio directly related to blood hemoglobin concentration. |
| `clean_red_ir_ratio_mean`, `_std` | $\text{mean}(x_{red} / x_{ir})$, $\text{std}$ | Pointwise instantaneous optical quotient statistics. |
| `red_ir_peak_lag_samples` | $\arg\max_\tau (x_{red} \star x_{ir})[\tau]$ | Inter-wavelength optical phase/pulse transit lag. |

---

### Category 5: Demographic Covariates (2 features)
- `age`: Subject age in years ($18 - 64$).
- `gender_encoded`: Biological sex (1 = Male, 0 = Female).

---

## 3. Strict Subject-Level Machine Learning Protocol

```
68 Unique Subjects
    ├── Train Set (47 Subjects, ~69.1%) ──> Fit StandardScaler & Fit ML Models
    ├── Validation Set (10 Subjects, ~14.7%) ──> Apply Train Scaler & Model Selection / Tuning
    └── Test Set (11 Subjects, ~16.2%) ──> Apply Train Scaler & ONE-TIME Final Benchmark
```

### Safety & Integrity Rules:
- **Zero Leakage**: Strict subject-level partitioning ensures no subject's recording appears in multiple partitions.
- **Scaler Isolation**: `StandardScaler` is fitted **EXCLUSIVELY on Train data** and saved to `models/feature_scaler.joblib`.
- **Target Isolation**: `hemoglobin_g_dl` is strictly separated and never used as a predictor.

---

## 4. Hardware Streaming Deployment Guide

When streaming live data from teammate Arya's ESP32:
```python
from src.ppg import extract_ppg_features
import joblib

# 1. Load fitted model and scaler
model_bundle = joblib.load("models/best_ppg_hb_model.joblib")
scaler = model_bundle["scaler"]
model = model_bundle["model"]
feature_cols = model_bundle["feature_cols"]

# 2. Extract features from 250-sample FIFO buffer (25 Hz)
sig_features = extract_ppg_features(raw_red_buffer, raw_ir_buffer, fs=25.0)
sig_features["age"] = patient_age
sig_features["gender_encoded"] = 1 if patient_gender == "Male" else 0

# 3. Scale and predict Hb
x_vec = np.array([[sig_features[c] for c in feature_cols]])
x_scaled = scaler.transform(x_vec)
predicted_hb = float(model.predict(x_scaled)[0])
```
