# PRAHARI — Multimodal Integration Layer (Step 5B)

This package integrates the **Image/CV Model** (`person1/`) and the **Optical PPG Pipeline** (`ppg-anemia/`) into a single, unified screening interface.

---

## 1. Scientific Principle & Fusion Policy

> [!IMPORTANT]
> **No Paired Dataset Exists:** Because there is currently no paired dataset containing concurrent conjunctival photographs and MAX30102 PPG recordings from the same patient cohort, **no statistical or mathematical fusion model is trained or assumed**.
>
> Outputs from both modalities are preserved independently in the structured result. `fusion.status` is set to `"NOT_VALIDATED"`.

---

## 2. Quick Start & Python API

```python
from integration import run_multimodal_screening

# 1. Full Multimodal Screening (Image + PPG)
response = run_multimodal_screening(
    image_path="person1/data/raw/cp-anemic/Anemic/Image_001.png",
    ppg_csv_path="ppg-anemia/tests/data/simulated_esp32_sub1.csv",
    age=25.0,
    gender="Male"
)

print(response.model_dump_json(indent=2))

# 2. Image-Only Screening (PPG omitted)
image_only_resp = run_multimodal_screening(
    image_path="person1/data/raw/cp-anemic/Anemic/Image_001.png"
)

# 3. PPG-Only Screening (Image omitted)
ppg_only_resp = run_multimodal_screening(
    ppg_csv_path="ppg-anemia/tests/data/simulated_esp32_sub1.csv",
    age=21.0,
    gender="Male"
)
```

---

## 3. Unified Output Structure

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

## 4. Modality Error & Quality Isolation

- If an image fails the quality gate (e.g. heavy blur), `image.status = "REJECTED"` with the specific reasons, while the PPG modality proceeds uninterrupted.
- If a PPG CSV has sampling rate irregularities or corrupt values, `ppg.status = "REJECTED"` / `"ERROR"`, while the image modality proceeds uninterrupted.
- If both modalities succeed, `success = true` with complete data for both.

---

## 5. Running Tests

```bash
pytest tests/test_multimodal_integration.py -v
```
