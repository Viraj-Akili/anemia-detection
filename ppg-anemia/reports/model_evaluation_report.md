# Model Evaluation & Benchmark Report — PRAHARI PPG Pipeline (Step 3)

## 1. Dataset & Subject-Level Partition Overview
- **Total Subjects**: 68
- **Train Subjects (47)**: Hb Mean = 12.76 ± 1.72 g/dL (Range: 9.7 - 17.5)
- **Validation Subjects (10)**: Hb Mean = 13.05 ± 2.06 g/dL (Range: 9.6 - 16.3)
- **Test Subjects (11)**: Hb Mean = 12.72 ± 1.98 g/dL (Range: 9.4 - 16.4)
- **Subject Leakage Check**: Zero subject overlap verified across partitions.

---

## 2. Model Comparison Table
| Model | Val MAE (g/dL) | Val RMSE (g/dL) | Val R² | Test MAE (g/dL) | Test RMSE (g/dL) | Test R² |
|---|---|---|---|---|---|---|
| Dummy (Mean Baseline) | 1.6500 | 1.9779 | -0.0224 | 1.4779 | 1.8910 | -0.0004 |
| Linear Regression | 9.0570 | 11.0802 | -31.0846 | 9.3473 | 12.5236 | -42.8814 |
| Ridge Regression | 1.4454 | 1.8276 | 0.1271 | 1.2813 | 1.5755 | 0.3056 |
| **Lasso Regression** (Selected) | 1.1151 | 1.4875 | 0.4218 | 1.1345 | 1.3597 | 0.4828 |
| Random Forest Regressor | 1.6338 | 1.8163 | 0.1378 | 1.3183 | 1.6151 | 0.2702 |
| Gradient Boosting Regressor | 1.6148 | 1.8171 | 0.1371 | 1.2442 | 1.4813 | 0.3861 |
| Support Vector Regressor (SVR) | 1.5240 | 1.7520 | 0.1978 | 1.4045 | 1.7224 | 0.1700 |

---

## 3. Best Model Performance & Baseline Comparison
- **Selected Model**: `Lasso Regression`
- **Validation MAE**: `1.1151 g/dL` (vs Dummy: `1.6500 g/dL`)
- **Final Test MAE**: `1.1345 g/dL` (vs Dummy: `1.4779 g/dL`)
- **Final Test RMSE**: `1.3597 g/dL` (vs Dummy: `1.8910 g/dL`)
- **Final Test R²**: `0.4828` (vs Dummy: `-0.0004`)

---

## 4. Top 10 Influential Features
| Rank | Feature Name | Category | Gini / MDI Importance |
|---|---|---|---|
| 1 | `ir_pulse_amplitude_mean` | Time/Morphology | 0.1508 |
| 2 | `ir_q75` | Time/Morphology | 0.0916 |
| 3 | `red_fft_spectral_entropy` | FFT | 0.0705 |
| 4 | `red_fft_cardiac_band_power` | FFT | 0.0608 |
| 5 | `ir_median` | Time/Morphology | 0.0381 |
| 6 | `gender_encoded` | Demographic | 0.0381 |
| 7 | `red_q75` | Time/Morphology | 0.0305 |
| 8 | `age` | Demographic | 0.0257 |
| 9 | `clean_red_ir_ratio_std` | Cross-Channel | 0.0256 |
| 10 | `ir_fft_spectral_entropy` | FFT | 0.0252 |

> [!IMPORTANT]
> **Interpretability Notice**: Feature importances reflect tree split frequency and variance reduction within this dataset. They do not denote clinical causality.

---

## 5. Prototype Limitations & Context
1. **Cohort Size**: The current dataset contains 68 unique subjects. While valid for prototyping and establishing an end-to-end pipeline, clinical generalization requires expanded multi-center data collection.
2. **Sensor Hardware**: Calibration against gold-standard laboratory spectrophotometry (e.g. Sysmex / HemoCue) across diverse skin tones and perfusion indices will be required during clinical hardware trials.
3. **Multi-Modal Role**: In the full PRAHARI system, this PPG model output acts as an optical hemodynamic feature vector for multimodal fusion with conjunctival imaging.