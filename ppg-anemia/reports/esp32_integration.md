# ESP32 / MAX30102 Live Hardware Integration Specification — PRAHARI PPG Pipeline

## 1. Executive Summary & Hardware Interface
This document specifies the hardware integration interface, input schema, temporal validation rules, and inference pipeline connecting teammate **Arya's MAX30102/ESP32 sensor subsystem** to the **PRAHARI Machine Learning pipeline**.

The integration module (`src/ppg/esp32.py` and `scripts/predict_esp32.py`) accepts continuous raw optical ADC counts recorded by the ESP32, performs rigorous data integrity checks, and executes the pre-trained Step 3 Lasso regression model without modifying any ML weights or preprocessing parameters.

```
MAX30102 Sensor (Red: 660nm, IR: 880nm)
           ↓ (I2C Bus @ 400 kHz)
ESP32 Microcontroller (FreeRTOS 25 Hz Timer)
           ↓ (Serial / SD Card / File Transfer)
Raw ESP32 CSV (`timestamp_ms,red,ir`)
           ↓
validate_esp32_dataframe() (Timing & Quality Gate)
           ↓
preprocess_ppg(raw_red, raw_ir, fs=25.0) (Step 2 Zero-Phase Bandpass)
           ↓
extract_ppg_features(fs=25.0) (Step 3 74-Feature Vector)
           ↓
feature_scaler.transform() (Fitted on Train Subjects)
           ↓
best_ppg_hb_model.predict() (Trained Lasso Model)
           ↓
Estimated Hemoglobin Output (g/dL)
```

---

## 2. Expected ESP32 CSV File Specification

### A. Column Structure
The ESP32 firmware must output a standard UTF-8 CSV containing exactly three header columns:

```csv
timestamp_ms,red,ir
0,116394,105863
40,116496,105901
80,116534,105945
120,116440,105795
...
9960,113584,105348
```

| Column Name | Type | Physical Range | Description |
|---|---|---|---|
| `timestamp_ms` | Numeric (Integer/Float) | $\ge 0$ ms | Monotonically increasing millisecond hardware timer ticks. |
| `red` | Numeric (Float/Integer) | $50,000 - 200,000$ ADC | Raw 18-bit optical Red channel intensity counts ($660\text{ nm}$). |
| `ir` | Numeric (Float/Integer) | $50,000 - 200,000$ ADC | Raw 18-bit optical Infrared channel intensity counts ($880\text{ nm}$). |

> [!IMPORTANT]
> **No Pre-calculated Metrics**: The ESP32 must output **RAW uncalibrated ADC counts only**. Do not substitute Heart Rate, SpO2 percentages, or filtered values.

---

## 3. Temporal Validation & Acceptance Criteria

Before any preprocessing or feature extraction occurs, the data stream passes through `validate_esp32_dataframe()`. Recordings that violate any rule are **strictly rejected** without silent data modification.

### A. Sampling Frequency & Tolerances
- **Nominal Sampling Frequency ($f_s$)**: **25.0 Hz**
- **Nominal Inter-Sample Period ($\Delta t$)**: **40.0 ms**
- **Effective Frequency Formula**:
  $$\Delta t_k = \text{timestamp\_ms}[k] - \text{timestamp\_ms}[k-1]$$
  $$f_{\text{eff}} = \frac{1000.0}{\text{median}(\Delta t)}$$
- **Acceptance Tolerance**: $25.0 \pm 2.0\text{ Hz}$ ($23.0\text{ Hz} \le f_{\text{eff}} \le 27.0\text{ Hz}$).

### B. Sample Count & Session Duration
- **Nominal Duration**: $10.0\text{ seconds}$ ($N = 250\text{ samples}$).
- **Allowed Sample Range**: $240 \le N \le 260\text{ samples}$ (tolerates $\pm 400\text{ ms}$ buffer startup/shutdown drift).

### C. Timestamp Monotonicity & Anomaly Checks
1. **Zero-interval (Duplicate) Check**: If any $\Delta t_k == 0$, recording is rejected (`Duplicate timestamps detected`).
2. **Backwards Step Check**: If any $\Delta t_k < 0$, recording is rejected (`Non-monotonic timestamps detected`).
3. **Missing / Corrupt Check**: If any values are `NaN`, `Inf`, or non-numeric strings, recording is rejected.
4. **Non-Positive ADC Check**: If any optical ADC count is $\le 0$, recording is rejected (`Non-positive optical ADC counts detected`).

---

## 4. Pipeline Execution & Reuse Architecture

The integration reuses the exact, frozen Step 2 and Step 3 libraries:

### Step 2: Signal Preprocessing (`src/ppg/preprocessing.py`)
1. **Detrending**: Scipy linear regression detrending removes DC baseline drift.
2. **Zero-Phase Filtering**: 3rd-order Butterworth bandpass filter ($0.5 - 5.0\text{ Hz}$) executed with `scipy.signal.filtfilt` (zero phase distortion).
3. **Z-Score Normalization**: Per-recording standardization ($x_{\text{norm}} = (x - \mu)/\sigma$).
4. **Signal Quality Gate (`src/ppg/quality.py`)**: Multi-criteria SQI evaluating spectral cardiac energy ($0.5-5.0\text{ Hz}$) and Red/IR cross-correlation ($r > 0.30$).

### Step 3: Feature Extraction (`src/ppg/features.py`)
Extracts the exact **74 ML features**:
- **Time-Domain (28 features)**: Red/IR moments, quantiles, range, ZCR.
- **Pulse Morphology (12 features)**: Red/IR peak count, heart rate BPM, pulse amplitude, PRV.
- **FFT Spectral (20 features)**: Red/IR dominant cardiac peak, spectral centroid, bandwidth, entropy, power ratios.
- **Cross-Channel (12 features)**: Red/IR Pearson correlation, AC/DC ratios, **Ratio of Ratios ($R$)**, temporal peak lag.
- **Demographics (2 features)**: Patient `age` and `gender_encoded`.

### ML Model Inference (`models/best_ppg_hb_model.joblib`)
- **Scaler**: `feature_scaler.joblib` (StandardScaler fitted on Train subjects).
- **Model**: Trained Lasso Regression.
- **Prediction Output**: Hemoglobin level in g/dL.

---

## 5. Command-Line Interface (CLI) Usage Guide

Teammate Arya can run predictions directly on any ESP32 CSV log via the terminal:

```bash
# Default prediction (Age 25, Male)
python scripts/predict_esp32.py path/to/esp32_session.csv

# Specifying patient demographic metadata
python scripts/predict_esp32.py path/to/esp32_session.csv --age 21 --gender Male
```

### Example Terminal Output:
```
========================================
ESP32 PPG Recording
----------------------------------------
Source file:             esp32_session_01.csv
Samples:                 250
Duration:                9.96 s
Effective sampling rate: 25.0 Hz (dt median: 40.0 ms)
RED Channel:             OK (mean ADC: 115330.76)
IR Channel:              OK (mean ADC: 105765.44)
Signal quality:          GOOD (SQI: 0.996)
Features Extracted:      74 (100% verified)
Demographics:            Age 21.0 | Gender Male
ML Model:                Lasso Regression
----------------------------------------
Predicted Hb:            14.60 g/dL
========================================
```

---

## 6. Software Validation & Simulation Test

### Transport Format Equivalence Benchmark:
To prove that transitioning from the research dataset schema (`data/raw/1.csv`) to the ESP32 transport schema (`timestamp_ms,red,ir`) introduces zero mathematical distortion:
- Recording `1.csv` was processed via the native dataset pipeline $\rightarrow$ $\hat{y}_{\text{dataset}} = 14.5986\text{ g/dL}$.
- Recording `1.csv` was formatted as an ESP32 CSV (`tests/data/simulated_esp32_sub1.csv`) and passed through `predict_esp32_recording()` $\rightarrow$ $\hat{y}_{\text{esp32}} = 14.5986\text{ g/dL}$.
- **Discrepancy**: $|\Delta \hat{y}| = 0.000000\text{ g/dL}$ (Exact identity).

---

## 7. Status for Teammate Arya
- [x] Parser & validator implemented and verified.
- [x] 25 Hz / 40 ms timestamp telemetry verified.
- [x] 74-feature schema verified.
- [x] End-to-end model execution verified.
- [x] 46 automated unit tests passing.
- [ ] **Awaiting physical hardware recording**: Once Arya generates live CSV files on the ESP32 board, run `python scripts/predict_esp32.py <file>` for physical validation.
