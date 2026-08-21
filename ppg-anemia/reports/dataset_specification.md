# Dataset Specification — PRAHARI PPG Anemia Pipeline

## Overview & Scope
This document outlines the technical specification of the raw Photoplethysmography (PPG) dataset used in the PPG / Hardware ML component of Project **PRAHARI**.

All statements below are explicitly divided into **[VERIFIED]** (empirically confirmed by programmatic inspection of the raw data files and matched against primary research publication documentation) and **[NOT VERIFIED]** / **[DESIGN CHOICES]**.

---

## 1. Verified Dataset Properties `[VERIFIED]`

| Parameter | Specification / Value | Status | Evidence / Verification Source |
|---|---|---|---|
| **Number of Unique Subjects** | **68 Subjects** | `[VERIFIED]` | 68 unique CSV files (`1.csv` to `68.csv`), each representing a distinct subject with unique demographic/Hb combinations. |
| **Number of Raw Recordings** | **68 continuous recordings** | `[VERIFIED]` | One distinct recording file per subject in `data/raw/`. |
| **Derivative Processed Records** | **816 records** (12 windows per subject across 68 subjects) | `[VERIFIED]` | Present in the benchmark derivative table (`Final Dataset Hb PPG.csv` = 68 × 12). |
| **Signal Channels** | **2 Channels: Red (a.u) and Infra Red (a.u)** | `[VERIFIED]` | Explicit columns `Red (a.u)` and `Infra Red (a.u)` in all raw files. |
| **Demographic Fields** | **Gender** (`Male`, `Female`), **Age** (years: integer) | `[VERIFIED]` | Present as columns in every raw CSV and internally constant per file. |
| **Target Variable** | **Hemoglobin (`Hemoglobin (g/dL)`)** | `[VERIFIED]` | Ground truth clinical hemoglobin concentration measured via Nesco Multicheck 2® Hb meter. |
| **Samples per Recording** | **249 to 250 samples** | `[VERIFIED]` | Programmatic verification reveals: **45 files have 249 samples**, and **23 files have 250 samples**. |
| **Sampling Frequency ($f_s$)** | **25 Hz** | `[VERIFIED]` | Verified from published dataset metadata (Mendeley Data DOI: [10.17632/xdrwrh9zbk.2](https://doi.org/10.17632/xdrwrh9zbk.2)) and confirmed by empirical FFT spectral analysis showing physiological resting cardiac peaks at 1.20–1.51 Hz (72–90 BPM). |
| **Recording Duration** | **10 seconds** (~249–250 samples at 25 Hz) | `[VERIFIED]` | Direct consequence of $T = N / f_s = 250 / 25 = 10.0\text{ s}$. |
| **Sensor Hardware** | **MAX30102 Optical Sensor** (Red: 660 nm, IR: 880 nm) | `[VERIFIED]` | Primary dataset publication specification. |
| **Signal Data Range (Red)** | **~75,000 to ~120,000 ADC counts** | `[VERIFIED]` | Non-negative, zero NaN, zero Inf, 18-bit ADC output profile. |
| **Signal Data Range (IR)** | **~62,000 to ~115,000 ADC counts** | `[VERIFIED]` | Non-negative, zero NaN, zero Inf, 18-bit ADC output profile. |
| **Gender Breakdown** | **38 Female (55.9%), 30 Male (44.1%)** | `[VERIFIED]` | Master metadata calculation across all 68 subjects. |
| **Subject Age Range** | **18 to 64 years** (Mean: 42.87 ± 13.52 years) | `[VERIFIED]` | Master metadata calculation. |
| **Hemoglobin Range** | **9.40 to 17.50 g/dL** (Mean: 12.79 ± 1.78 g/dL) | `[VERIFIED]` | Ground truth distribution covering anemic and non-anemic cohorts. |

---

## 2. Hardware Implications & ESP32 Integration

Now that the sampling rate is verified as **25 Hz** on the MAX30102 sensor:
1. **ESP32 Firmware Configuration**:
   - Set sensor sample rate register: `MAX30102_SAMPLERATE_25` (25 samples per second).
   - LED pulse width: `MAX30102_PULSEWIDTH_411` (18-bit ADC resolution).
   - LED Current: Standard ~6.4 mA to ~12.5 mA for fingertip transmission.
2. **Buffer Sizing for Live Stream**:
   - Collect FIFO buffer of **250 samples** (exactly 10.0 seconds of data).
   - Stream batch to `preprocess_ppg(raw_red, raw_ir, fs=25.0)` for real-time inference.

---

## 3. Summary Table

```
+------------------------------------+-------------------------+-----------------+
| Metric                             | Value                   | Status          |
+------------------------------------+-------------------------+-----------------+
| Subjects                           | 68                      | [VERIFIED]      |
| Recordings                         | 68                      | [VERIFIED]      |
| Samples / Recording                | 249 to 250              | [VERIFIED]      |
| Channels                           | Red (a.u), IR (a.u)     | [VERIFIED]      |
| Target                             | Hemoglobin (g/dL)       | [VERIFIED]      |
| Demographics                       | Gender, Age             | [VERIFIED]      |
| Missing / NaN Values               | 0                       | [VERIFIED]      |
| Negative Signal Values             | 0                       | [VERIFIED]      |
| Sampling Rate                      | 25 Hz                   | [VERIFIED]      |
| Recording Duration                 | 10.0 seconds            | [VERIFIED]      |
| Sensor Model                       | MAX30102 (Red/IR)       | [VERIFIED]      |
+------------------------------------+-------------------------+-----------------+
```
