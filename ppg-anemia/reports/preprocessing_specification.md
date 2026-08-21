# Preprocessing Specification — PRAHARI PPG Pipeline

## 1. Overview & Architecture
This document specifies the technical design, mathematical foundation, and implementation parameters for **STEP 2: PPG Preprocessing & Signal Filtering** within the **PRAHARI** non-invasive anemia screening project.

The preprocessing pipeline is implemented in the reusable package `src/ppg/` and is designed to operate identically on:
1. **Offline dataset recordings** from `data/raw/`.
2. **Live real-time streaming buffers** received from teammate Arya's ESP32 microcontroller and MAX30102 sensor.

---

## 2. Distinction: Verified Facts vs. Design Choices

| Dimension | Aspect | Classification | Rationale / Justification |
|---|---|---|---|
| **Sensor & Hardware** | MAX30102 Optical Sensor | `[VERIFIED FACT]` | Primary dataset documentation (Mendeley Data DOI: 10.17632/xdrwrh9zbk.2). |
| **Channels** | Red (660 nm) & Infrared (880 nm) | `[VERIFIED FACT]` | Direct optical raw ADC channels in dataset files. |
| **Sampling Rate ($f_s$)** | 25 Hz | `[VERIFIED FACT]` | Primary research publication; verified via FFT cardiac peaks (1.2–1.5 Hz / 72–90 BPM). |
| **Recording Duration** | 10.0 seconds (249–250 samples) | `[VERIFIED FACT]` | Direct empirical row count of CSV files divided by 25 Hz. |
| **Detrending Method** | Linear Detrending | `[DESIGN CHOICE]` | Removes low-frequency baseline drift (respiration, skin temperature) without phase lag. |
| **Filter Topology** | 3rd-Order Butterworth Bandpass | `[DESIGN CHOICE]` | Maximally flat magnitude response in passband; prevents ripple in pulse morphology. |
| **Zero-Phase Implementation** | Bidirectional `scipy.signal.filtfilt` | `[DESIGN CHOICE]` | Eliminates group delay and phase distortion; preserves pulse peak alignment. |
| **Passband Frequencies** | 0.5 Hz to 5.0 Hz | `[DESIGN CHOICE]` | 0.5 Hz (30 BPM) eliminates drift; 5.0 Hz (300 BPM) retains systolic & dicrotic notch harmonics while rejecting high-frequency noise. |
| **Normalization** | Z-Score Standardization | `[DESIGN CHOICE]` | Zero-mean, unit-variance per recording ($x_{norm} = \frac{x - \mu}{\sigma}$); prevents cross-subject data leakage. |
| **Quality Criteria** | Multi-Factor Thresholds (SQI, Corr, Range) | `[DESIGN CHOICE]` | Rejects corrupt/flatline signals while passing clinically usable waveforms. |

---

## 3. Detailed Signal Processing Pipeline

### Step-by-Step Signal Flow:
```
Raw RED & IR PPG Arrays (18-bit ADC Counts)
    │
    ▼
[1. Numeric Conversion & Validation]
    - Verify 1D float64 format
    - Catch and flag any NaNs / Infs
    │
    ▼
[2. Detrending (Baseline Correction)]
    - Remove DC baseline drift and respiratory modulation
    - y[n] = x[n] - (m * n + c)
    │
    ▼
[3. Zero-Phase Bandpass Filtering]
    - 3rd-order Butterworth bandpass (0.5 Hz - 5.0 Hz)
    - Effective 6th-order zero-phase filtfilt
    │
    ▼
[4. Amplitude Normalization]
    - Z-score normalization per channel: (x - mean) / std
    │
    ▼
[5. Multi-Criteria Signal Quality Assessment]
    - Spectral Cardiac Band Ratio (SQI)
    - Red-IR Pearson Cross-Correlation
    - Sample Count & Flatline Checks
    │
    ▼
Clean RED & IR Signals + Structured Quality Metadata
```

---

## 4. Signal Quality Assessment (SQI) & Rejection Criteria

Every signal processed by `assess_signal_quality()` is evaluated across 6 criteria and assigned a status:

1. **`REJECT` (Unusable Signal)**:
   - Contains `NaN` or `Inf` values.
   - Sample count $N < 50$ samples ($<2.0\text{ seconds}$).
   - Flatline / near-constant signal: Standard deviation $\sigma_{raw} < 1.0$ ADC counts or $\sigma_{clean} < 1e-4$.
   - Excessive noise: Mean cardiac spectral power ratio $\text{SQI} < 0.35$.
2. **`WARNING` (Borderline Signal, Retained)**:
   - Sample count between 50 and 150 samples ($2.0\text{s} \le T < 6.0\text{s}$).
   - Borderline cardiac spectral power ratio ($0.35 \le \text{SQI} < 0.55$).
   - Weak or negative cross-channel correlation between Red and IR ($r_{Red, IR} < 0.30$).
   - ADC saturation warning: Peak ADC count $> 262,000$ (near 18-bit ceiling).
3. **`GOOD` (High-Purity Usable Signal)**:
   - $N \ge 150$ samples ($6.0\text{s} - 10.0\text{s}$).
   - High cardiac spectral purity: $\text{SQI} \ge 0.55$.
   - Positive, strong Red-IR cross-correlation ($r_{Red, IR} \ge 0.30$).
   - No clipping or baseline anomalies.

---

## 5. Output Data Schema & Storage

Processed files are saved strictly under `data/processed/`:

### A. Consolidated Dataset (`data/processed/processed_recordings.csv`)
Columns:
- `subject_id` (int, e.g. 1..68)
- `recording_id` (str, e.g. `sub_001_rec_01`)
- `source_file` (str, e.g. `data/raw/1.csv`)
- `sample_index` (int, 0..249)
- `time_sec` (float, `sample_index / 25.0`)
- `raw_red` (float, original ADC count)
- `raw_ir` (float, original ADC count)
- `clean_red` (float, filtered & normalized Z-score)
- `clean_ir` (float, filtered & normalized Z-score)
- `gender` (str, `Male`/`Female`)
- `age` (int)
- `hemoglobin_g_dl` (float)
- `quality_status` (str, `GOOD`/`WARNING`/`REJECT`)

### B. Individual Subject Files (`data/processed/subjects/{subject_id}_processed.csv`)
Per-subject time-series files for modular per-file analysis.

### C. Master Quality Summary (`data/processed/preprocessing_quality_summary.csv`)
Recording-level summary with SQI metrics, Red-IR correlations, warnings, and usability flags.

---

## 6. Live ESP32 Hardware Integration Guide

When teammate Arya's ESP32 is integrated in future steps:
1. The ESP32 collects a FIFO buffer of 250 raw samples at 25 Hz from the MAX30102.
2. The payload is streamed via Serial/WiFi/BLE as raw arrays: `red_buffer`, `ir_buffer`.
3. In Python / PRAHARI API, invoke the exact same preprocessing function:
   ```python
   from src.ppg import preprocess_ppg

   clean_red, clean_ir, quality = preprocess_ppg(
       raw_red=red_buffer,
       raw_ir=ir_buffer,
       fs=25.0
   )

   if quality["is_usable"]:
       # Pass clean_red and clean_ir to downstream feature extractor & ML model
       pass
   else:
       # Prompt user on screen: "Poor finger placement / motion detected, please re-scan"
       pass
   ```
