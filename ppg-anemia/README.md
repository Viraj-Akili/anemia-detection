# PRAHARI — PPG / Hardware ML Pipeline

## 1. Project Overview
This repository contains the Photoplethysmography (PPG) Machine Learning and Hardware Integration pipeline for project **PRAHARI** (Non-Invasive Anemia Screening System).

In the full PRAHARI architecture, dual-wavelength optical PPG signals (Red and Infra Red) captured via a MAX30102 sensor and an ESP32 microcontroller are preprocessed, features are extracted, and fed into an ML model. Predictions from the PPG model will eventually be fused with conjunctival image anemia predictions via multimodal decision fusion:

```
MAX30102 (Optical Sensor)
    ↓
ESP32 (Embedded MCU)
    ↓
Raw RED + IR PPG Signals (timestamp_ms,red,ir)
    ↓
Hardware Validation & Telemetry (Step 4 — Completed)
    ↓
PPG Preprocessing & Filtering (Step 2 — Completed)
    ↓
PPG Feature Extraction (Step 3 — Completed)
    ↓
PPG ML Model Inference (Step 3/4 — Completed)
    ↓
PPG Anemia / Hb Prediction (MAE: 1.13 g/dL, R²: 0.48)
    +
Conjunctival Image Anemia Model
    ↓
Multimodal Decision Fusion
    ↓
PRAHARI Backend API
    ↓
Clinician / Mobile Frontend
```

---

## 2. Current Project Stage: STEP 4 COMPLETED

### Scope of Completed Stages:
- **STEP 1 — Dataset Understanding & Preparation**: Discovery, validation, metadata generation, verified 25 Hz sampling rate audit, and leakage-free subject split.
- **STEP 2 — PPG Preprocessing & Signal Filtering**: Core library (`src/ppg/`), linear baseline detrending, zero-phase 3rd-order Butterworth bandpass filtering (0.5–5.0 Hz), per-recording Z-score normalization, multi-criteria signal quality assessment (SQI), batch dataset processing, and visualization plots.
- **STEP 3 — Feature Extraction & ML Model**: 74-feature extraction engine (Time-Domain, FFT, Pulse Morphology, Cross-Channel Optical Ratios, Demographics), feature quality audit, strict subject-level train/validation/test benchmark, multi-model regression comparison against baseline, feature importance extraction, and diagnostic visualizations.
- **STEP 4 — Live ESP32/MAX30102 Hardware Integration**: Dedicated hardware parser (`src/ppg/esp32.py`), strict timestamp monotonicity and $25 \pm 2\text{ Hz}$ sampling rate validation, end-to-end inference CLI (`scripts/predict_esp32.py`), 46 passing unit tests, and hardware integration documentation (`reports/esp32_integration.md`).

### What has NOT yet been implemented (Intentionally Out of Scope for Steps 1–4):
- **NO image model or multimodal fusion** components have been built.
- **NO PRAHARI backend integration** has been executed.
- **NO in-place modifications** to raw dataset files.

---

## 3. Live Hardware Inference CLI (Step 4)

Teammate Arya or any clinician can predict Hemoglobin directly from an ESP32 CSV:

```bash
# Default demographic values (Age 25, Male)
python scripts/predict_esp32.py path/to/esp32_recording.csv

# Specifying patient age and gender
python scripts/predict_esp32.py path/to/esp32_recording.csv --age 21 --gender Male
```

### Example Terminal Output:
```
========================================
ESP32 PPG Recording
----------------------------------------
Source file:             simulated_esp32_sub1.csv
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

## 4. Machine Learning Benchmark Summary (Step 3 & 4)

Models were fitted on **Train (47 subjects)**, selected based on **Validation (10 subjects)**, and evaluated on **Held-Out Test (11 subjects)**:

| Model | Val MAE (g/dL) | Val RMSE (g/dL) | Val R² | Test MAE (g/dL) | Test RMSE (g/dL) | Test R² |
|---|---|---|---|---|---|---|
| Dummy (Mean Baseline) | 1.6500 | 1.9779 | -0.0224 | 1.4779 | 1.8910 | -0.0004 |
| Linear Regression | 9.0570 | 11.0802 | -31.0846 | 9.3473 | 12.5236 | -42.8814 |
| Ridge Regression | 1.4454 | 1.8276 | 0.1271 | 1.2813 | 1.5755 | 0.3056 |
| **Lasso Regression (Selected)** | **1.1151** | **1.4875** | **0.4218** | **1.1345** | **1.3597** | **0.4828** |
| Random Forest Regressor | 1.6338 | 1.8163 | 0.1378 | 1.3183 | 1.6151 | 0.2702 |
| Gradient Boosting Regressor | 1.6148 | 1.8171 | 0.1371 | 1.2442 | 1.4813 | 0.3861 |
| Support Vector Regressor (SVR) | 1.5240 | 1.7520 | 0.1978 | 1.4045 | 1.7224 | 0.1700 |

---

## 5. Directory Structure

```
ppg-anemia/
│
├── data/
│   ├── raw/                  # Original raw CSVs (never modified in-place)
│   ├── processed/            # Preprocessed datasets and extracted features
│   └── metadata/             # Master metadata, splits, and feature dictionaries
│
├── src/                      # Core modular signal processing library
│   └── ppg/
│       ├── __init__.py
│       ├── preprocessing.py  # Zero-phase bandpass filtering, detrending, normalization
│       ├── quality.py        # SQI calculation, quality evaluation, rejection
│       ├── time_features.py  # Time-domain stats & pulse morphology
│       ├── fft_features.py   # Spectral power, dominant cardiac frequency, entropy
│       ├── cross_channel_features.py # Red/IR ratios, AC/DC, optical ratio-of-ratios
│       ├── features.py       # Master feature extraction API
│       └── esp32.py          # Step 4 ESP32 parser, validator, and inference pipeline
│
├── models/                   # Saved model artifacts
│   ├── best_ppg_hb_model.joblib # Fitted best model (Lasso)
│   ├── feature_scaler.joblib    # StandardScaler fitted on Train only
│   └── feature_names.json       # Exact feature column order
│
├── scripts/                  # Automation CLI tools
│   ├── inspect_dataset.py    # Step 1A: Dataset discovery & inspection
│   ├── validate_dataset.py   # Step 1B: Data integrity validation
│   ├── build_metadata.py     # Step 1C: Master metadata table generator
│   ├── create_subject_split.py # Step 1F: Leakage-free subject split generator
│   ├── preprocess_dataset.py # Step 2F: Full dataset batch preprocessing
│   ├── visualize_preprocessing.py # Step 2G: Waveform & spectral plots
│   ├── extract_features.py   # Step 3F: Feature extraction & audit
│   ├── train_evaluate_models.py # Step 3G-3M: Model training & evaluation
│   ├── visualize_model_results.py # Step 3N: Performance & feature plots
│   └── predict_esp32.py      # Step 4: Live ESP32 hardware inference CLI
│
├── reports/                  # Validation reports, specifications, and figures
│   ├── dataset_specification.md
│   ├── preprocessing_specification.md
│   ├── feature_extraction_specification.md
│   ├── feature_audit.md
│   ├── model_evaluation_report.md
│   ├── dataset_recording_audit.md
│   ├── esp32_integration.md
│   └── figures/              # Preprocessing & ML diagnostic plots
│
├── tests/                    # Automated pytest test suite (46 unit tests)
│   ├── conftest.py
│   ├── test_dataset_discovery.py
│   ├── test_dataset_validation.py
│   ├── test_metadata_generation.py
│   ├── test_subject_split.py
│   ├── test_preprocessing.py
│   ├── test_quality.py
│   ├── test_features.py
│   ├── test_models.py
│   └── test_esp32.py
│
├── requirements.txt          # Minimal project dependencies
├── README.md                 # Project documentation
└── .gitignore                # Git ignore rules
```

---

## 6. Execution Guide

### 1. Run Complete Automated Unit Tests (46 Tests)
```bash
pytest tests/ -v
```

### 2. Predict on Live ESP32 CSV Recording
```bash
python scripts/predict_esp32.py tests/data/simulated_esp32_sub1.csv --age 21 --gender Male
```
