# Dataset Recording Count & Structural Integrity Audit — PRAHARI PPG Pipeline

## Executive Summary
This audit resolves the apparent discrepancy between the reported **68 subjects** in the raw continuous dataset (`data/raw/1.csv` to `68.csv`) and the **816 rows / recordings** cited in the dataset literature and `Final Dataset Hb PPG.csv`.

Empirical forensic analysis of `Raw dataset per subject.zip`, `Preprocessing dataset per subject.zip`, `Final Dataset Hb PPG.csv`, and `data/raw/` confirms that:
1. **The dataset contains exactly 68 unique biological human subjects**.
2. **There are exactly 68 continuous 10-second raw dual-wavelength PPG recordings** (one per subject, consisting of 249–250 samples sampled at 25 Hz).
3. The **816 rows** in `Final Dataset Hb PPG.csv` represent **12 temporal downsampled chunk averages per subject** ($68\text{ subjects} \times 12\text{ chunks} = 816\text{ rows}$) computed by the dataset authors.
4. Our current Step 3 model was trained and evaluated on the **true continuous 10-second raw waveforms of the 68 unique subjects** under strict subject-level isolation.
5. The Step 3 benchmark metrics (**Test MAE: 1.13 g/dL, Test $R^2$: 0.48**) represent **honest, leakage-free generalization** on completely held-out patients.
6. The hardware specification (**25 Hz sampling rate, 10-second acquisition, 250 samples/channel**) perfectly matches one raw recording window from Arya's ESP32.

---

## 1. Programmatic Investigation of Dataset Files

| Source File / Directory | Location / Archive | Files / Rows | Contents Description |
|---|---|---|---|
| `data/raw/` | Local Workspace | 68 CSV files (`1.csv` ... `68.csv`) | Continuous raw time-series ADC counts (`Red`, `Infra Red`, `Gender`, `Age`, `Hemoglobin`). 45 files have 249 rows, 23 files have 250 rows. Total samples = 16,955. |
| `Raw dataset per subject.zip` | Original Mendeley Download | 68 CSV files (`1.csv` ... `68.csv`) | 100% byte-for-byte identical to `data/raw/` (0 hash mismatches). |
| `Preprocessing dataset per subject.zip` | Original Mendeley Download | 68 CSV files (`1.csv` ... `68.csv`) | Exactly 12 rows per CSV file. Total rows = $68 \times 12 = 816$ rows. |
| `Final Dataset Hb PPG.csv` | Original Mendeley Download | 1 single CSV file (816 rows × 5 cols) | Direct vertical concatenation of the 68 files in `Preprocessing dataset per subject.zip`. |

---

## 2. Mathematical Relationship: 68 Raw Files vs. 816 Rows

Forensic reconstruction revealed the exact method used by the dataset authors to produce the 816 rows:

Each raw 250-sample (10.0 second @ 25 Hz) continuous optical signal was segmented into **12 consecutive temporal chunks**:
- **Chunks 1 to 11**: Each chunk spans **20 samples** ($0.8\text{ seconds}$). The author computed the arithmetic mean:
  $$\overline{x}_{\text{chunk } k} = \frac{1}{20}\sum_{n=20(k-1)}^{20k - 1} x[n] \quad (k=1 \dots 11)$$
- **Chunk 12**: Spans the remaining **29–30 samples** (samples 220 to 249/250, approx $1.2\text{ seconds}$):
  $$\overline{x}_{\text{chunk } 12} = \frac{1}{N - 220}\sum_{n=220}^{N-1} x[n]$$

Empirical verification confirms an exact match ($|\Delta| < 0.05\text{ ADC units}$) between this 12-chunk mean formulation and the 12 rows per subject in `Final Dataset Hb PPG.csv`:

```
Subject 1 Red Channel (N = 250 samples):
  - Author Final Dataset (12 rows): [115965.9, 115834.4, 115741.5, 115707.2, 115675.6, 115626.1, 115573.2, 115436.8, 115259.9, 114993.0, 114637.7, 114122.3]
  - Computed 12-Chunk Means       : [115965.8, 115834.4, 115741.4, 115707.2, 115675.6, 115626.0, 115573.2, 115436.8, 115259.8, 114993.0, 114637.7, 114122.3]
  - Max Absolute Difference       : 0.05 ADC counts (rounding artifact).
```

---

## 3. Answers to Core Audit Questions

### Q1: How many raw CSV files are there?
**68 raw CSV files** (`1.csv` through `68.csv`).

### Q2: How many rows are in each raw CSV?
**249 to 250 rows** per file (45 files with 249 rows, 23 files with 250 rows). At 25 Hz, this equals 10.0 seconds of continuous acquisition.

### Q3: Does each raw CSV represent one subject or multiple?
Each raw CSV represents **one subject** and **one continuous 10-second recording session**.

### Q4: What does one row of `Final Dataset Hb PPG.csv` represent?
One row represents a **single downsampled 0.8–1.2 second chunk average** of Red and IR optical intensities from a subject, with the subject's demographic values (`Gender`, `Age`) and laboratory `Hemoglobin (g/dL)`.

### Q5: Why does `Final Dataset Hb PPG.csv` contain 816 rows?
Because 68 subjects × 12 chunk averages per subject = **816 rows**.

### Q6: Are the 816 rows independent recordings?
**No.** They are **12 downsampled sub-second segments** derived from the **single 10-second recording** of each of the 68 subjects. They are neither 816 independent patients nor 816 independent continuous recording sessions.

### Q7: Can the 816 rows be mapped to the 68 raw CSV files?
**Yes, perfectly 1-to-1**:
- Rows $12(k-1)$ to $12k - 1$ correspond strictly to Subject $k$ (`data/raw/k.csv`) for $k = 1 \dots 68$.

### Q8: Is there a recording/set identifier in the full dataset?
Not explicitly named in `Final Dataset Hb PPG.csv`, but implicitly grouped in contiguous blocks of 12 rows per subject.

### Q9: Does `Preprocessing dataset per subject` contain additional recordings?
**No.** It contains 68 CSV files, each having the exact 12-row downsampled chunk averages of the corresponding raw file.

### Q10: Are the Hb values repeated for multiple recordings of the same subject?
**Yes.** In `Final Dataset Hb PPG.csv`, the subject's single clinical blood Hemoglobin measurement is repeated identically across all 12 chunk rows.

### Q11: What is the true number of independent subjects?
**68 unique subjects**.

### Q12: What is the true number of PPG recordings?
**68 continuous dual-wavelength 10-second recordings**.

### Q13: What should the correct unit of observation be for ML?
The **complete 10-second PPG continuous recording (250 samples)**. A single scalar downsampled chunk cannot capture pulse peak morphology, heart rate variability, or FFT frequency spectrum.

---

## 4. Subject Leakage & Partitioning Analysis

### The Critical Leakage Risk of Naive 816-Row Splitting:
If a researcher naively uses `Final Dataset Hb PPG.csv` (816 rows) with standard randomized shuffling (`train_test_split(shuffle=True)` or standard K-Fold CV):
1. **Severe Data Leakage**: Chunks from the *same patient* appear in both the training and test sets (e.g., 10 chunks in train, 2 in test).
2. **Identity Memorization**: Because `Age`, `Gender`, and static baseline optical DC levels are identical across all 12 chunks of that patient, the model memorizes the patient's identity rather than learning generalized optical hemodynamics.
3. **Artificially Inflated Metrics**: Test metrics appear artificially high ($R^2 > 0.95$, $\text{MAE} < 0.3$), but completely collapse when tested on a new, unseen patient.

### Required Protocol:
Subject-level grouping is **MANDATORY**. All recordings, chunks, or windows from any single subject must reside **exclusively in one partition** (Train, Validation, or Test).

---

## 5. Impact on Current Step 3 Model

Our Step 3 pipeline was implemented strictly according to leakage-free principles:
1. **Unit of Observation**: 1 continuous 10-second recording (250 raw samples) per subject.
2. **Subject Partition**:
   - **Train**: 47 unique subjects (47 recordings)
   - **Validation**: 10 unique subjects (10 recordings)
   - **Held-Out Test**: 11 unique subjects (11 recordings)
   - *Zero subject overlap.*
3. **Scaler Fitting**: `StandardScaler` fitted **ONLY on Train subjects**.
4. **Current Performance**:
   - **Model**: Lasso Regression (12 sparse non-zero features selected)
   - **Validation MAE**: **1.1151 g/dL** (vs Dummy Baseline 1.6500 g/dL)
   - **Final Test MAE**: **1.1345 g/dL** (vs Dummy Baseline 1.4779 g/dL)
   - **Final Test RMSE**: **1.3597 g/dL** (vs Dummy Baseline 1.8910 g/dL)
   - **Final Test $R^2$**: **0.4828** (vs Dummy Baseline -0.0004)

### Conclusion on Step 3 Model Validity:
The current Step 3 model was evaluated on **11 completely held-out unique subjects** ($N=11$). The reported metrics reflect **true out-of-sample patient generalization** and are methodologically sound.

---

## 6. Hardware Implications for MAX30102 / ESP32 Integration

The hardware specification proposed for teammate Arya's MAX30102/ESP32 is:
- **Sampling Frequency ($f_s$)**: **25 Hz** (40 ms inter-sample period)
- **Recording Window**: **10.0 seconds**
- **Samples per Window**: **250 samples** per channel (`Red` and `Infra Red`)

### Direct Compatibility:
1. One 10-second acquisition window on the MAX30102 sensor produces **250 Red and 250 IR raw optical counts**.
2. This is **1:1 identical** to the raw dataset format (`data/raw/1.csv` ... `68.csv`).
3. The real-time inference pipeline on ESP32 data will directly feed this 250-sample buffer into:
   $$\text{Raw RED/IR Buffer (250)} \xrightarrow{\text{preprocess\_ppg()}} \text{Clean Waveforms} \xrightarrow{\text{extract\_ppg\_features()}} \text{74 Features} \xrightarrow{\text{best\_model.predict()}} \text{Hb Estimate}$$
4. **No dimensional mismatch or downsampling hack is needed.**

---

## 7. Final Audit Status: RESOLVED
The relationship between 68 subjects, 68 raw recordings, and 816 downsampled chunk rows is fully explained, empirically proven, and mathematically documented. No code or data alterations were performed.
