# PRAHARI — Multimodal Integration Architecture Specification (Step 5B)

**Status:** Implementation Complete & Validated  
**Date:** 2026-08-20  
**Integration Module:** `integration/`  
**Target Modalities:**
1. **Conjunctival Image / Computer Vision Model** (`person1/`)
2. **Optical PPG / Hardware MAX30102 Model** (`ppg-anemia/`)

---

## 1. Executive Summary & Scientific Core Principle

The **PRAHARI Multimodal Integration Layer** coordinates non-invasive anemia screening across two distinct physiological and sensor modalities:
1. **Conjunctival Pallor (Computer Vision):** High-resolution color and pallor feature analysis from photographs of the everted palpebral conjunctiva.
2. **Hemodynamic Pulsatile Signal (Optical PPG):** Dual-wavelength Red and Infrared photoplethysmography captured at 25 Hz via an optical MAX30102 sensor and ESP32 microcontroller.

### Crucial Scientific Constraint: Why Fusion Is NOT Trained
> [!IMPORTANT]
> **No Paired Dataset Exists:** There is currently **no clinical dataset** that contains simultaneously captured conjunctival photographs and MAX30102 PPG recordings from the **same patient cohort**.
>
> In accordance with medical AI best practices:
> - **NO statistical or ML fusion model has been trained.**
> - **NO arbitrary mathematical formula** (such as averaging or weighted summing of normalized Hb and probability) has been invented.
> - **NO synthetic pairing** has been claimed as clinical truth.
> - **Outputs from both models are strictly preserved in their native units** ($P(\text{anemic}) \in [0, 1]$ and $\text{Hb} \in \text{g/dL}$).
> - The fusion status is explicitly reported as **`"NOT_VALIDATED"`**.

---

## 2. Existing Model Interfaces

### A. Image/CV Model Interface (`person1/`)
- **Primary Class:** `app.ai.inference.AnemiaInferenceEngine`
- **Model Checkpoint:** `person1/models/baseline_classifier.joblib` (~5.13 MB)
- **Active Model:** Scikit-Learn Pipeline (`ColorFeatureExtractor` $\to$ `StandardScaler` $\to$ `RandomForestClassifier`)
- **Inference Entry Points:**
  - `engine.load()` — Loads model weights idempotently.
  - `engine.analyze(image)` — Complete pipeline with quality gate, feature extraction, timing breakdown, and structured dictionary output.
  - `engine.predict(image)` — Lightweight path returning `AnemiaPrediction` dataclass.
- **Input Modality:** Photograph of the everted palpebral conjunctiva (PNG, JPEG, WebP, BMP, TIFF).
- **Demographics:** **None required.**
- **Output:**
  - `label`: `"anemic"` or `"non_anemic"`
  - `model_probability`: $P(\text{anemic}) \in [0.0, 1.0]$
  - `model_confidence`: Winning class probability ($[0.5, 1.0]$)
  - `image_quality`: Detailed quality gate assessment (`status`, `score`, `checks`, `reasons`).

### B. Optical PPG Hardware Interface (`ppg-anemia/`)
- **Primary Function:** `src.ppg.esp32.predict_esp32_recording`
- **Model Checkpoint:** `ppg-anemia/models/best_ppg_hb_model.joblib` (Model bundle with scaler & feature schema)
- **Active Model:** Scikit-Learn `Lasso(alpha=0.1)` fitted on 74 extracted features with `StandardScaler`.
- **Inference Entry Points:**
  - `predict_esp32_recording(file_path_or_df, model_bundle_path, age, gender, fs)`
  - CLI: `scripts/predict_esp32.py <path_to_csv> --age <age> --gender <gender>`
- **Input Modality:** 10-second raw dual-wavelength CSV (`timestamp_ms,red,ir`) @ 25 Hz (nominal 250 samples).
- **Demographics:** **Required / Utilized:** `age` (years, float), `gender` (string / encoded float).
- **Output:**
  - `predicted_hb_g_dl`: Predicted total blood Hemoglobin in **$\text{g/dL}$** (e.g. $14.60\text{ g/dL}$).
  - `signal_quality`: `"GOOD"` or `"POOR"`.
  - `sqi_score`: Mean cardiac Signal Quality Index ($[0.0, 1.0]$).
  - `effective_fs_hz`: Measured sampling frequency (must satisfy $25 \pm 2\text{ Hz}$).
  - `sample_count`: Total samples validated.

---

## 3. Unified Input Schema

The integration layer defines a clean, typed request contract via `MultimodalScreeningRequest` in `integration/schemas.py`:

```python
class MultimodalScreeningRequest(BaseModel):
    image_path: Optional[str] = None    # Path or bytes of conjunctival photo
    ppg_csv_path: Optional[str] = None  # Path to ESP32 CSV recording
    age: Optional[float] = 25.0        # Patient age in years (used by PPG)
    gender: Optional[str] = "Male"     # Patient gender (used by PPG)
```

- If `image_path` is provided and `ppg_csv_path` is `None`: **Image-Only Screening**.
- If `ppg_csv_path` is provided and `image_path` is `None`: **PPG-Only Screening**.
- If both are provided: **Complete Multimodal Screening**.
- If neither is provided: Returns `success: false` with `NO_MODALITIES_PROVIDED` error.

---

## 4. Unified Output Schema

The integration layer produces a structured `MultimodalScreeningResponse` conforming to strict JSON schema specifications:

```json
{
  "success": true,
  "patient": {
    "age": 25.0,
    "gender": "Male"
  },
  "image": {
    "available": true,
    "status": "SUCCESS",
    "label": "anemic",
    "probability": 0.988,
    "confidence": 0.988,
    "quality_status": "good",
    "quality_score": 1.0,
    "quality_checks": {
      "blur": "pass",
      "brightness": "pass",
      "contrast": "pass",
      "resolution": "pass",
      "tissue": "pass"
    },
    "quality_reasons": [],
    "model_name": "random_forest_color_baseline",
    "inference_latency_ms": 52.31,
    "error": null
  },
  "ppg": {
    "available": true,
    "status": "SUCCESS",
    "predicted_hb_g_dl": 14.60,
    "signal_quality": "GOOD",
    "sqi": 0.996,
    "sampling_rate_hz": 25.0,
    "samples": 250,
    "duration_sec": 9.96,
    "feature_count": 74,
    "model_name": "Lasso Regression",
    "error": null
  },
  "fusion": {
    "status": "NOT_VALIDATED",
    "method": null,
    "result": null,
    "note": "Statistical multimodal fusion is not performed because no paired dataset (concurrent conjunctival image + MAX30102 PPG on identical subjects) is currently available. Modality outputs are preserved independently without unvalidated weighting or conversion."
  },
  "execution_time_ms": 68.45,
  "error": null
}
```

---

## 5. Modality Quality & Error Isolation Policy

The integration layer enforces strict **modality fault isolation**: a failure or quality rejection in one modality does **not** corrupt or abort the other modality.

| Scenario | Image Status | PPG Status | Overall Success | Response Behavior |
| :--- | :--- | :--- | :--- | :--- |
| **Both Valid** | `SUCCESS` | `SUCCESS` | `true` | Both predictions and quality metrics populated; `fusion.status = "NOT_VALIDATED"`. |
| **Image Only (Valid)** | `SUCCESS` | `NOT_PROVIDED` | `true` | Image prediction returned; PPG fields explicitly marked `null` and `available: false`. |
| **PPG Only (Valid)** | `NOT_PROVIDED` | `SUCCESS` | `true` | PPG prediction returned; Image fields explicitly marked `null` and `available: false`. |
| **Image Blurred / Low Quality** | `REJECTED` | `SUCCESS` | `true` | Image reports `IMAGE_QUALITY_LOW` with failed checks; valid PPG prediction preserved. |
| **PPG Bad Sampling Rate / Noise** | `SUCCESS` | `REJECTED`/`ERROR`| `true` | PPG reports `PPG_VALIDATION_ERROR`; valid Image prediction preserved. |
| **Both Modalities Fail** | `REJECTED`/`ERROR`| `REJECTED`/`ERROR`| `false` | Top-level `success: false` with `ALL_MODALITIES_FAILED` error code. |
| **Neither Modality Provided** | `NOT_PROVIDED` | `NOT_PROVIDED` | `false` | Top-level `success: false` with `NO_MODALITIES_PROVIDED` error code. |

---

## 6. Future Requirements for Validated Multimodal Fusion

To advance from the current software integration layer to a **clinically validated multimodal decision fusion model**, the following empirical prerequisites must be fulfilled:

1. **Paired Clinical Dataset Collection:**
   - Prospective clinical collection of concurrent conjunctival photographs and 10-second MAX30102 PPG recordings on $N \ge 300$ subjects across diverse skin tones and demographic profiles.
   - Synchronized reference ground-truth total blood hemoglobin ($\text{Hb}_{\text{lab}}$) via standard hematology analyzers (e.g. Sysmex or HemoCue).
2. **Late-Fusion Meta-Model Architecture:**
   - Train a calibrated decision-fusion meta-model:
     $$\mathbf{z} = \left[ \widehat{\text{Hb}}_{\text{PPG}}, \text{SQI}_{\text{PPG}}, P(\text{anemic})_{\text{Image}}, Q_{\text{Image}}, \text{Age}, \text{Gender} \right]$$
   - Utilize Bayesian model averaging or an ensemble meta-regressor/classifier with cross-validated calibration.
3. **Discordance & Ambiguity Resolution:**
   - Establish formal decision rules when modalities disagree (e.g. high-quality image indicates anemia, but PPG indicates normal Hb), prioritizing whichever sensor has higher signal quality index / lower uncertainty.
4. **Clinical Threshold Alignment:**
   - Map continuous fused Hemoglobin values against WHO age/gender specific cutoffs ($11.0\text{ g/dL}$ for young children, $12.0\text{ g/dL}$ for adult women, $13.0\text{ g/dL}$ for adult men).

---

## 7. Programmatic Integration Entry Points

### Python API
```python
from integration import run_multimodal_screening, MultimodalScreeningEngine

# Option 1: Convenience top-level function
result = run_multimodal_screening(
    image_path="person1/data/raw/cp-anemic/Anemic/Image_001.png",
    ppg_csv_path="ppg-anemia/tests/data/simulated_esp32_sub1.csv",
    age=25.0,
    gender="Male"
)

# Option 2: Preloaded class instance (for servers / long-running services)
engine = MultimodalScreeningEngine()
engine.load()
result = engine.screen({
    "image_path": "path/to/eye.png",
    "ppg_csv_path": "path/to/esp32.csv",
    "age": 30.0,
    "gender": "Female"
})
```

### Verification & Testing
The complete test suite verifies all 12 operational scenarios and mathematical equivalence:
```bash
pytest tests/test_multimodal_integration.py -v
```
