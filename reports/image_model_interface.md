# PRAHARI — Image/CV Model Interface Inspection & Multimodal Integration Audit (Step 5A)

**Status:** Completed Inspection & Architecture Audit  
**Date:** 2026-08-20  
**Inspection Target:** `person1/` (AI/CV Backend & Image-Based Anemia Screening Pipeline)  
**Reference Target:** `ppg-anemia/` (Optical PPG / Hardware MAX30102 ML Pipeline)  

---

## 1. Image Model Location & Project Structure

The image-based anemia screening subsystem is housed in the `person1/` directory.

### Directory Layout
- **Core AI & Inference Engine:** `person1/app/ai/`
  - `inference.py` — Production inference coordinator (`AnemiaInferenceEngine`, `BaselineClassifier`).
  - `features.py` — Color feature extraction over tissue-masked pixels (`ColorFeatureExtractor`, `extract_color_features`).
  - `quality_gate.py` — Image usability assessment (`assess_image`, `compute_metrics`, `tissue_coverage`).
  - `preprocessing.py` — Image loading, alpha compositing, aspect-preserving resizing (`load_rgb`, `preprocess_image`, `normalize`).
  - `cnn_model.py` — MobileNetV2 deep learning architecture (`AnemiaCNN`, checkpoint loaders).
  - `errors.py` — Structured typed error definitions (`InferenceError`, `ImageQualityLowError`, etc.).
  - `dataset.py` — Dataset loaders & PyTorch transforms for CNN training.
  - `roi.py` — Region of interest placeholder (pass-through since raw dataset images are pre-cropped).
  - `explainability.py` — Optional Grad-CAM explanation stub.
- **FastAPI Service:** `person1/app/`
  - `main.py` — FastAPI application entrypoint with lifespan lifecycle management, CORS, `/health`, `/models`.
  - `api/anemia.py` — REST route `POST /api/v1/anemia/screen`.
  - `schemas/anemia.py` — Pydantic request/response schemas.
  - `config.py` — Environment configuration settings.
- **Model Checkpoints:** `person1/models/`
  - `baseline_classifier.joblib` — Primary production model artifact (Random Forest pipeline).
  - `mobilenetv2_best.pth` — Secondary deep learning checkpoint (MobileNetV2).
  - `mobilenetv2_metadata.json` — CNN training & hyperparameter metadata.
- **Scripts & CLI Tools:** `person1/scripts/`
  - `test_inference.py` — CLI for single image inference & self-test suite.
  - `benchmark_inference.py` — Batch latency and throughput benchmarking tool.
  - `train_baseline.py` — Classical baseline training script (RF and Logistic Regression).
  - `train_cnn.py` — MobileNetV2 two-stage GPU training script.
  - `prepare_dataset.py`, `validate_dataset.py`, `visualize_dataset.py` — Dataset preparation and validation suite.

---

## 2. Image Preprocessing & Quality Pipeline

The image model implements a multi-stage preprocessing and validation pipeline:

```
Uploaded Image (File / Path / Bytes / PIL)
    ↓
1. Format & Decode Validation (_load_image in inference.py)
   - Decodes to PIL Image; checks formats (PNG, JPEG, WEBP, BMP, TIFF)
   - Verifies dimensions: min side >= 8 px, max side <= 4096 px
    ↓
2. Quality Gate (assess_image in quality_gate.py)
   - Alpha compositing over white canvas (to avoid transparent pixels darkening metrics)
   - Sharpness / Blur: Laplacian variance >= 50.0 (CP-AnemiC observed: 70–3492)
   - Brightness: Mean grayscale 30.0 <= mu <= 250.0 (observed: 173–249)
   - Contrast: Grayscale std >= 10.0 (observed: 15–98)
   - Resolution: Min side >= 16 px
   - Tissue Availability: Alpha coverage fraction >= 0.10 (for RGBA)
   - Score: Starts at 1.0, penalties subtracted per failure; if any check fails -> REJECT (IMAGE_QUALITY_LOW)
    ↓
3A. Primary Model Preprocessing (Random Forest):
   - ColorFeatureExtractor (app/ai/features.py)
   - Reads image as RGBA; creates tissue mask where alpha > 10 (or all pixels if no mask)
   - Converts masked RGB pixels to CIELAB space
   - Computes 19 hand-crafted color features:
     * RGB tissue: R mean, G mean, B mean, R std, G std, B std (6)
     * LAB tissue: L* mean, a* mean, b* mean, L* std, a* std, b* std (6)
     * Redness ratios: R/(R+G+B), R-G, R-B (3)
     * Distribution tails: R p10, R p90, a* p10, a* p90 (4)
   - StandardScaler: Zero-mean, unit-variance scaling (fitted on train split)
    ↓
3B. Secondary Fallback Preprocessing (MobileNetV2 CNN):
   - Alpha compositing over white background
   - Aspect-preserving thumbnail resize and white pad to 224x224x3 RGB canvas
   - ImageNet normalization: Mean [0.485, 0.456, 0.406], Std [0.229, 0.224, 0.225]
```

---

## 3. Model Architecture

### A. Primary Production Model: Random Forest Color Baseline (`random_forest`)
- **Type:** Scikit-Learn `Pipeline` (`ColorFeatureExtractor` -> `StandardScaler` -> `RandomForestClassifier`).
- **Hyperparameters:** `n_estimators=500`, `class_weight='balanced'`, `random_state=42`, `n_jobs=1` (set to 1 at inference to eliminate Windows multi-process overhead).
- **Features:** 19 deterministic color and pallor statistics extracted from tissue-masked pixels.
- **Decision:** Selected over Logistic Regression based on validation anemic-class F1 score (0.791 vs 0.660).

### B. Secondary Fallback Model: MobileNetV2 CNN (`cnn`)
- **Type:** Deep Convolutional Neural Network (`torchvision.models.mobilenet_v2` with ImageNet-1K pretrained weights).
- **Head:** Classifier head replaced with `nn.Sequential(nn.Dropout(p=0.2), nn.Linear(1280, 1))`.
- **Total Parameters:** 2,225,153 (~2.2 M parameters).
- **Output Activation:** Single raw logit mapped via Sigmoid to $P(\text{anemic})$.
- **Training Strategy:** 2-stage GPU training (Stage 1: Head-only 8 epochs; Stage 2: Fine-tune `features[14:]` for 60 epochs with early stopping on validation F1).

---

## 4. Training Data & Ground Truth

- **Dataset Name:** **CP-AnemiC** (A Conjunctival Pallor Dataset from Ghana).
- **Source:** Mendeley Data (DOI: 10.17632/m53vz6b7fx.1, Justice Williams Asare et al., 2023).
- **Subject Population:** 710 children aged **6–59 months** in Ghana (collected across 10 healthcare facilities in 6 regions).
- **Image Modality:** Photographs of everted palpebral conjunctiva captured with a 12 MP Samsung Galaxy Tab A7 camera in ambient natural lighting (flash off). Pre-cropped into RGBA PNG conjunctiva strips with alpha channel masking.
- **Usable Dataset Size:** **708 images** (2 images excluded due to cross-class label conflict on byte-identical content: `Image_310` and `Image_188`).
- **Ground Truth Criteria:** Binary anemia classification derived from **laboratory-measured blood hemoglobin**:
  - $\text{Hb} < 11.0\text{ g/dL}$ $\to$ **`anemic`** (WHO pediatric cutoff for 6–59 months).
  - $\text{Hb} \ge 11.0\text{ g/dL}$ $\to$ **`non_anemic`**.
- **Data Splitting Strategy:**
  - Leakage-safe splitting by **MD5 content group** (prevents byte-identical duplicate images from crossing splits).
  - Stratified by `(label, hospital)` with `seed=42`.
  - **Train split:** 498 images (304 anemic, 194 non-anemic; 348 content groups).
  - **Validation split:** 97 images (47 anemic, 50 non-anemic; 74 content groups).
  - **Held-out Test split:** 113 images (72 anemic, 41 non-anemic; 75 content groups).

---

## 5. Input Schema

The image model accepts input through three programmatic interfaces:

### 1. Python Engine (`AnemiaInferenceEngine.analyze(image)` or `.predict(image)`)
- **Input Type:** `str | Path | PIL.Image.Image | bytes | bytearray`
- **Supported Encodings:** PNG, JPEG, WEBP, BMP, TIFF.
- **Supported Modes:** RGB, RGBA, L, LA, P.
- **Size Bounds:** Min dimension $\ge 8\text{ px}$, Max dimension $\le 4096\text{ px}$.

### 2. FastAPI REST Endpoint (`POST /api/v1/anemia/screen`)
- **Content-Type:** `multipart/form-data`
- **Form Field:** `image` (binary file upload)
- **Allowed MIME Types:** `image/png`, `image/jpeg`, `image/webp`, `image/bmp`, `image/tiff`
- **Max File Size:** 4 MB (configured by `MAX_IMAGE_SIZE_MB`)

### 3. CLI Script (`scripts/test_inference.py`)
- **Argument:** `python scripts/test_inference.py <path_to_image>`

---

## 6. Output Schema & Data Types

The image model predicts **binary screening status and model probabilities**. It does **NOT** output a numerical Hemoglobin (Hb) value.

### Exact JSON Response Structure (`POST /api/v1/anemia/screen`)

#### Success Response (HTTP 200)
```json
{
  "success": true,
  "prediction": {
    "label": "anemic",
    "model_probability": 0.912,
    "model_confidence": 0.912
  },
  "image_quality": {
    "status": "good",
    "score": 1.0,
    "checks": {
      "blur": "pass",
      "brightness": "pass",
      "contrast": "pass",
      "resolution": "pass",
      "tissue": "pass"
    },
    "reasons": []
  },
  "inference": {
    "model": "random_forest_color_baseline",
    "version": "1.0",
    "dataset": "CP-AnemiC (Mendeley 10.17632/m53vz6b7fx.1)",
    "latency_ms": 58.4
  },
  "api_latency_ms": 59.1
}
```

#### Quality Gate Rejection (HTTP 200, `success=false`)
```json
{
  "success": false,
  "prediction": null,
  "image_quality": {
    "status": "poor",
    "score": 0.35,
    "checks": {
      "blur": "fail",
      "brightness": "pass",
      "contrast": "pass",
      "resolution": "pass",
      "tissue": "pass"
    },
    "reasons": ["blur"]
  },
  "inference": null,
  "error": {
    "code": "IMAGE_QUALITY_LOW",
    "message": "Image quality is insufficient. Please retake the image."
  },
  "api_latency_ms": 5.2
}
```

### Python Data Types & Fields
- `prediction.label`: `str` — `"anemic"` or `"non_anemic"` (decision threshold: $P(\text{anemic}) \ge 0.50$).
- `prediction.model_probability`: `float` ($0.0 \le p \le 1.0$) — Model probability for the `anemic` class.
- `prediction.model_confidence`: `float` ($0.5 \le c \le 1.0$) — Model probability for the winning class ($\max(p, 1-p)$).
- `image_quality.status`: `str` — `"good"` or `"poor"`.
- `image_quality.score`: `float` ($0.0 \le s \le 1.0$) — Usability score.
- `image_quality.checks`: `dict[str, str]` — Individual pass/fail flags for `blur`, `brightness`, `contrast`, `resolution`, `tissue`.
- `image_quality.reasons`: `list[str]` — List of failed check names.
- `inference.latency_ms`: `float` — Execution latency.

---

## 7. Demographic Inputs

- **Required Demographics:** **NONE.**
- **Does it require Age?** **NO.**
- **Does it require Gender?** **NO.**
- **Does it require any other patient information?** **NO.**
- The image model operates exclusively on raw pixel data. Patient age, gender, anthropometry, and clinical history are not accepted by `AnemiaInferenceEngine` or the API endpoint.

---

## 8. Inference Entry Point & Function Signatures

### Python Entry Point
```python
from app.ai.inference import AnemiaInferenceEngine

# 1. Initialize engine
engine = AnemiaInferenceEngine()  # Loads settings.ai_model ('random_forest' by default)

# 2. Load model into memory (idempotent, loads once)
engine.load()

# 3. Perform analysis
# Option A: Full structured dictionary analysis (recommended)
result = engine.analyze("data/raw/cp-anemic/Anemic/Image_001.png")

# Option B: Direct prediction dataclass
prediction = engine.predict("data/raw/cp-anemic/Anemic/Image_001.png")
```

### Key Functions
- `AnemiaInferenceEngine.load() -> AnemiaInferenceEngine` (`person1/app/ai/inference.py#L145`)
- `AnemiaInferenceEngine.analyze(image) -> dict` (`person1/app/ai/inference.py#L279`)
- `AnemiaInferenceEngine.predict(image) -> AnemiaPrediction` (`person1/app/ai/inference.py#L245`)
- `assess_image(image, ...) -> QualityResult` (`person1/app/ai/quality_gate.py#L97`)
- `extract_color_features(path) -> np.ndarray` (`person1/app/ai/features.py#L61`)
- `screen_anemia(image: UploadFile) -> dict` (`person1/app/api/anemia.py#L70`)

---

## 9. Model Artifact Locations

1. **Random Forest Classifier (Active Production Model):**
   - File path: `person1/models/baseline_classifier.joblib`
   - File size: 5,130,482 bytes (~5.13 MB)
   - Contents: Scikit-learn Pipeline (`ColorFeatureExtractor` + `StandardScaler` + `RandomForestClassifier`)
2. **MobileNetV2 CNN (Secondary Model):**
   - File path: `person1/models/mobilenetv2_best.pth`
   - File size: 9,153,035 bytes (~9.15 MB)
   - Metadata path: `person1/models/mobilenetv2_metadata.json` (1,210 bytes)

---

## 10. Current Validation & Test Performance Metrics

Metrics reported directly from `person1/data/results/baseline_metrics.json` and `person1/data/results/cnn_metrics.json`:

### Primary Model: Random Forest Classifier (Selected Model)
- **Selection Criterion:** Best validation anemic-class F1 score (`0.791`) on Train/Val split.
- **Validation Split ($n = 97$):**
  - Accuracy: **81.44%** (0.8144)
  - Anemic Precision: **0.8718**
  - Anemic Recall: **0.7234** (34 of 47 detected)
  - Anemic F1-Score: **0.7907**
  - Non-Anemic F1-Score: **0.8333**
  - ROC-AUC: **0.9202**
  - Confusion Matrix ($[\text{Non-Anemic}, \text{Anemic}]$): `[[45, 5], [13, 34]]`
- **Held-Out Test Split ($n = 113$, Evaluated Once):**
  - Accuracy: **87.61%** (0.8761)
  - Anemic Precision: **0.9143**
  - Anemic Recall: **0.8889** (64 of 72 detected; 8 false negatives)
  - Anemic F1-Score: **0.9014**
  - Non-Anemic Precision: **0.8140**
  - Non-Anemic Recall: **0.8537** (35 of 41 detected; 6 false positives)
  - Non-Anemic F1-Score: **0.8333**
  - ROC-AUC: **0.9238**
  - Confusion Matrix ($[\text{Non-Anemic}, \text{Anemic}]$): `[[35, 6], [8, 64]]`
- **Latency (CPU single-sample):** Mean **55.58 ms**, Median **53.41 ms**, P95 **66.63 ms**.

### Secondary Model: MobileNetV2 CNN (Deep Learning Fallback)
- **Validation Split ($n = 97$, Best Epoch 48):**
  - Accuracy: **75.26%** (0.7526)
  - Anemic Precision: **0.7018**
  - Anemic Recall: **0.8511**
  - Anemic F1-Score: **0.7692**
  - ROC-AUC: **0.7498**
- **Held-Out Test Split ($n = 113$):**
  - Accuracy: **75.22%** (0.7522)
  - Anemic Precision: **0.8143**
  - Anemic Recall: **0.7917** (57 of 72 detected; 15 false negatives)
  - Anemic F1-Score: **0.8028**
  - Non-Anemic F1-Score: **0.6667**
  - ROC-AUC: **0.8211**
  - Confusion Matrix ($[\text{Non-Anemic}, \text{Anemic}]$): `[[28, 13], [15, 57]]`
- **Latency:** GPU mean **8.58 ms**; CPU mean **16.52 ms**.

---

## 11. Python Dependencies

From `person1/requirements.txt`:
- **Web API Framework:** `fastapi` (>=0.110), `uvicorn[standard]` (>=0.29), `python-multipart` (>=0.0.9), `pydantic` (>=2.6), `python-dotenv` (>=1.0).
- **Computer Vision & Image Processing:** `opencv-python` (>=4.9), `pillow` (>=10.0), `numpy` (>=1.26,<2.0), `matplotlib` (>=3.8).
- **Classical Machine Learning:** `scikit-learn` (>=1.4), `joblib`, `pandas` (>=2.0), `openpyxl` (>=3.1).
- **Deep Learning:** `torch` (==2.12.1), `torchvision` (==0.27.1).
- **Development & Testing:** `pytest` (>=8.0), `tqdm` (>=4.66).

---

## 12. Concrete End-to-End Example

### Concrete Input
- **Image File:** `data/raw/cp-anemic/Anemic/Image_001.png` (224x109 RGBA PNG)
- **Demographics:** None (not accepted)

### Concrete Output Object (`engine.analyze()`)
```json
{
  "success": true,
  "prediction": {
    "label": "anemic",
    "model_probability": 0.912,
    "model_confidence": 0.912
  },
  "image_quality": {
    "status": "good",
    "score": 1.0,
    "checks": {
      "blur": "pass",
      "brightness": "pass",
      "contrast": "pass",
      "resolution": "pass",
      "tissue": "pass"
    },
    "reasons": []
  },
  "inference": {
    "model": "random_forest_color_baseline",
    "version": "1.0",
    "model_path": "models/baseline_classifier.joblib",
    "dataset": "CP-AnemiC (Mendeley 10.17632/m53vz6b7fx.1)",
    "latency_ms": 58.42
  },
  "timings_ms": {
    "decode_ms": 3.71,
    "quality_ms": 1.62,
    "features_ms": 45.03,
    "predict_ms": 45.03,
    "total_ms": 58.42
  }
}
```

---

## 13. Comprehensive Project Comparison: PPG Model vs. Image Model

| Dimension | PROJECT 2: PPG Model (`ppg-anemia/`) | PROJECT 1: Image Model (`person1/`) |
| :--- | :--- | :--- |
| **Input Modality** | 10-second Dual-Wavelength Optical PPG CSV (`timestamp_ms, red, ir`) @ 25 Hz (250 Red + 250 IR samples) | Photograph of everted palpebral conjunctiva (PNG, JPEG, WEBP, BMP, TIFF) |
| **Preprocessing Pipeline** | Monotonicity/timestamp validation $\to$ Linear detrending $\to$ Zero-phase 3rd-order Butterworth bandpass (0.5–5.0 Hz) $\to$ SQI signal quality check $\to$ Z-score normalization | Image validation $\to$ Quality Gate (Laplacian blur, brightness, contrast, tissue mask) $\to$ Alpha tissue masking $\to$ StandardScaler |
| **Extracted Features** | **74 hand-crafted PPG features** (Time domain, FFT spectral, pulse morphology, Red/IR optical ratios, age, gender) | **19 hand-crafted color features** (RGB tissue stats, LAB tissue stats, pallor color ratios, distribution tails) |
| **Active ML Model** | **Lasso Regression** (`Lasso(alpha=0.1)`) | **Random Forest Classifier** (`RandomForestClassifier(n_estimators=500, balanced)`) |
| **Output Target** | **Continuous Hemoglobin Concentration** ($Hb$) | **Binary Anemia Screening Signal** (`"anemic"` vs `"non_anemic"`) + Model Probability |
| **Output Units** | **$\text{g/dL}$** (e.g. $14.60\text{ g/dL}$) | **Probability / Label** ($P \in [0.0, 1.0]$, Label $\in \{\text{"anemic"}, \text{"non\_anemic"}\}$) |
| **Demographic Inputs** | **Required / Used:** `age` (years, float), `gender` (string / encoded float) | **None:** Does not accept age, gender, or patient metadata |
| **Inference Entry Point** | `src.ppg.esp32.predict_esp32_recording()` & `scripts/predict_esp32.py` | `app.ai.inference.AnemiaInferenceEngine.analyze()` & `POST /api/v1/anemia/screen` |
| **Primary Model Artifact** | `ppg-anemia/models/best_ppg_hb_model.joblib` (Bundle: model, scaler, feature columns) | `person1/models/baseline_classifier.joblib` (Pipeline: extractor, scaler, classifier) |
| **Key Dependencies** | `numpy`, `scipy`, `pandas`, `scikit-learn`, `joblib` | `fastapi`, `uvicorn`, `pydantic`, `torch`, `torchvision`, `opencv-python`, `pillow`, `scikit-learn` |
| **Current Performance Metrics** | **Test ($n=11$):** $\text{MAE} = 1.13\text{ g/dL}$, $\text{RMSE} = 1.36\text{ g/dL}$, $R^2 = 0.4828$ | **Test ($n=113$):** $\text{Accuracy} = 87.61\%$, $\text{Recall}_{\text{anemic}} = 88.89\%$, $\text{F1}_{\text{anemic}} = 0.9014$, $\text{AUC} = 0.9238$ |

---

## 14. Target Compatibility & Fusion Strategy Analysis

### Are the two outputs directly compatible?
**NO.** The two models predict fundamentally different physical/mathematical quantities:
- **PPG Model:** Continuous physical regression estimate: $\widehat{\text{Hb}}_{\text{PPG}} \in \mathbb{R}^+$ in **$\text{g/dL}$**.
- **Image Model:** Binary classification screening risk signal: $P(\text{anemic}|\text{Image}) \in [0, 1]$ and $\text{Label} \in \{\text{"anemic"}, \text{"non\_anemic"}\}$.

### Why simple averaging is invalid:
A continuous concentration in $\text{g/dL}$ (e.g., $14.60\text{ g/dL}$) and a probability score (e.g., $0.912$) have different dimensionalities, scales, and clinical meanings. They cannot be averaged or directly added.

### Available Information for a Future Multimodal Fusion Layer:
A future fusion layer will have access to rich, complementary signals from both modalities:

1. **From PPG Modality:**
   - Predicted Hemoglobin: $\widehat{\text{Hb}}_{\text{PPG}}$ ($\text{g/dL}$)
   - PPG Signal Quality Index: $\text{SQI}_{\text{PPG}} \in [0, 1]$
   - Signal Quality Status: `"GOOD"` / `"POOR"`
   - 74 Extracted Optical & Hemodynamic Features (AC/DC ratios, pulse width, cardiac frequency)
   - Patient Demographics: `age`, `gender`
2. **From Conjunctival Image Modality:**
   - Predicted Class: $\text{Label}_{\text{Image}} \in \{\text{"anemic"}, \text{"non\_anemic"}\}$
   - Image Anemia Probability: $P(\text{anemic}|\text{Image}) \in [0, 1]$
   - Image Prediction Confidence: $C_{\text{Image}} \in [0.5, 1.0]$
   - Image Quality Score: $Q_{\text{Image}} \in [0, 1]$
   - Image Quality Status: `"good"` / `"poor"`
   - Per-check image metrics (blur, brightness, contrast, tissue coverage)
   - 19 Color & Pallor Features ($R, G, B, L^*, a^*, b^*$ statistics)

### Prospective Fusion Methods for Future Implementation:
1. **Clinical Decision Threshold Rules:**
   - Apply WHO age/gender specific Hemoglobin thresholds to $\widehat{\text{Hb}}_{\text{PPG}}$ to derive a PPG anemia classification $\text{Anemic}_{\text{PPG}} = (\widehat{\text{Hb}} < \text{Threshold})$.
   - Cross-evaluate against Image $P(\text{anemic})$ with quality-weighted discordance resolution.
2. **Quality-Weighted Risk Scoring (Meta-Classifier):**
   - Train a lightweight late-fusion classifier (e.g., Logistic Regression or Random Forest meta-learner) on the combined feature representation:
     $$\mathbf{z} = \left[ \widehat{\text{Hb}}_{\text{PPG}}, \text{SQI}_{\text{PPG}}, P(\text{anemic})_{\text{Image}}, Q_{\text{Image}}, \text{Age}, \text{Gender} \right]$$
3. **Probabilistic / Bayesian Evidence Fusion:**
   - Transform $\widehat{\text{Hb}}_{\text{PPG}}$ into a likelihood $P(\text{anemic}|\widehat{\text{Hb}}, \sigma_{\text{MAE}})$ using Gaussian error distribution and combine with $P(\text{anemic}|\text{Image})$ weighted by respective sensor quality indices.

---

## 15. Recommended Future Integration Architecture

The future PRAHARI multimodal system can be architected as a clean orchestration layer on top of the two frozen subsystems:

```
                          Patient Encounter
                                  │
         ┌────────────────────────┴────────────────────────┐
         │                                                 │
   Eye Photograph                                   ESP32 MAX30102 CSV
   (PNG/JPEG/WEBP)                                 (timestamp_ms,red,ir)
   + Quality Check                                  + Age & Gender
         │                                                 │
         ▼                                                 ▼
┌────────────────────────────────┐               ┌────────────────────────────────┐
│   PROJECT 1: IMAGE SUBSYSTEM   │               │    PROJECT 2: PPG SUBSYSTEM    │
│   (person1/app/ai/inference)   │               │     (ppg-anemia/src/ppg)       │
│                                │               │                                │
│ • Quality Gate (blur, light)   │               │ • Telemetry & 25 Hz validation │
│ • 19 Color/Pallor Features     │               │ • Butterworth Filter & SQI     │
│ • StandardScaler + RF Model    │               │ • 74 Optical/FFT/Demo Features │
│                                │               │ • StandardScaler + Lasso Model │
└────────────────┬───────────────┘               └────────────────┬───────────────┘
                 │                                                │
                 ▼                                                ▼
       Image Screening Result                            PPG Hemoglobin Result
     - label: "anemic"                                 - predicted_hb: 14.60 g/dL
     - model_probability: 0.912                        - signal_quality: "GOOD"
     - quality_status: "good"                          - sqi_score: 0.996
     - quality_score: 1.0                              - patient_age: 21
                 │                                     - patient_gender: "Male"
                 │                                                │
                 └───────────────────────┬────────────────────────┘
                                         │
                                         ▼
                     ┌───────────────────────────────────────┐
                     │         FUTURE FUSION LAYER           │
                     │    (Decision / Meta-Model / Rule)     │
                     │                                       │
                     │ • Signal Quality Validation           │
                     │ • Modality Concordance Check          │
                     │ • Fused Anemia Risk Level             │
                     │ • Calibrated Fused Hemoglobin (g/dL)  │
                     │ • Clinical Action Recommendation      │
                     └───────────────────┬───────────────────┘
                                         │
                                         ▼
                     ┌───────────────────────────────────────┐
                     │          PRAHARI UNIFIED API          │
                     │       Clinician / Mobile Client       │
                     └───────────────────────────────────────┘
```

---

## 16. Unknowns & Unresolved Issues

1. **Adult Generalization of Image Model:**
   - *Observation:* The image model was trained exclusively on the pediatric **CP-AnemiC** dataset (children aged 6–59 months in Ghana).
   - *Status:* `UNRESOLVED — evidence not found in current project for adult conjunctival pallor performance.`
2. **Adult WHO Hemoglobin Cutoffs in Image Ground Truth:**
   - *Observation:* Ground truth labels for the image dataset used the pediatric cutoff ($\text{Hb} < 11.0\text{ g/dL}$). Adult normal Hb ranges are higher ($12.0\text{ g/dL}$ for non-pregnant women, $13.0\text{ g/dL}$ for men).
   - *Status:* `UNRESOLVED — image model does not natively account for adult gender-specific WHO thresholds.`
3. **Paired Multimodal Training Dataset:**
   - *Observation:* No combined dataset containing *simultaneous* conjunctival photographs and MAX30102 PPG recordings from the *same* patient cohort exists in either repository.
   - *Status:* `UNRESOLVED — multimodal late fusion parameters must be derived using synthetic pairing, cross-validation rules, or clinical benchmark ranges.`
4. **ROI Localization on Uncropped Full-Eye Images:**
   - *Observation:* `person1/app/ai/roi.py` is a pass-through stub because CP-AnemiC contains pre-cropped conjunctiva strips. If a mobile user uploads an uncropped full-face or full-eye photo, the current quality gate checks tissue coverage, but there is no automatic YOLO or semantic segmentation model to crop the palpebral conjunctiva.
   - *Status:* `UNRESOLVED — automated conjunctival ROI extraction from raw full-eye images is not yet implemented.`
