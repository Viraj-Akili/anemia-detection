# PRAHARI — AI/CV Backend

**Person 1 AI/CV component** of the PRAHARI hackathon project.
Repository: https://github.com/Viraj-Akili/anemia-detection

## Purpose

Non-invasive, image-based anemia **screening signal** from conjunctival
photographs, exposed over an API for the rest of the PRAHARI system
(Swayam's multimodal risk engine, Arya's backend/database).

## Pipeline

```
Image
  ↓
Quality Gate        (reject blurry / badly lit / unusable images)
  ↓
ROI                 (locate the palpebral conjunctiva)
  ↓
Preprocessing       (crop → resize → normalize)
  ↓
Anemia Model        (baseline: color features + classifier; strong: MobileNetV2)
  ↓
Prediction + Confidence   (binary anemic / non-anemic + probability)
  ↓
API                 (FastAPI)
```

The API output is a **screening signal only** — it is not a clinical
diagnosis and does not encode severity. Final risk scoring and recommended
actions belong to Swayam's component.

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   |   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # adjust as needed (no secrets exist in this project)

# Run the API (Hour 1 state: skeleton, screening endpoint returns 501)
uvicorn app.main:app --reload
```

> Note: the installed torch is the CPU build. For GPU training (RTX 5050
> present), reinstall the CUDA variant — see `requirements.txt` and
> `MODEL_PLAN.md`.

## Project structure

```
app/
├── main.py              # FastAPI entrypoint, /health
├── config.py            # env-driven configuration (see .env.example)
├── ai/                  # quality_gate, roi, preprocessing, model, inference, explainability
├── api/anemia.py        # POST /api/v1/anemia/screen (placeholder)
└── schemas/anemia.py    # response schema
data/                    # raw/, processed/, samples/ (raw+processed gitignored)
models/                  # trained weights (gitignored for now)
scripts/                 # training / dataset-prep scripts (Hour 2+)
tests/                   # pytest suite (Hour 2+)
notebooks/               # exploration (Hour 2+)
```

## Current development stage

**Hour 6 of 10 — FastAPI AI service complete.**

- Hour 1: foundation, dataset selected (CP-AnemiC), model plan (`PROJECT_STATUS.md`)
- Hour 2: data pipeline — 708 usable images, leakage-safe 70/15/15 split (16 tests)
- Hour 3: classical baseline — Random Forest, test acc 0.876 / anemic recall 0.889
  / F1 0.901 / AUC 0.924 (28 tests)
- Hour 4: CUDA enabled (torch 2.12.1+cu130, RTX 5050); MobileNetV2 fine-tuned
  (test acc 0.752 / recall 0.792 / F1 0.803 / AUC 0.821) (35 tests)
- Hour 5: **AnemiaInferenceEngine** (validate → quality gate → alpha-masked
  features → RF/CNN → structured result); typed errors; CLI + benchmark;
  measured 58.4 ms/image mean, 113/113 screened (58 tests)
- Hour 6: **FastAPI AI service** — `POST /api/v1/anemia/screen`, `/health`, `/models`;
  Pydantic schemas; error mapping; CORS; startup model loading (70 tests)
- Next: Hour 7 — integration with Swayam/Arya or additional features

## Dataset status

Selected: **CP-AnemiC** (DOI 10.17632/m53vz6b7fx.1, Mendeley Data) —
710 palpebral conjunctiva images of children 6–59 months, labeled
anemic/non-anemic by lab hemoglobin (WHO threshold < 11 g/dL).
**Downloaded and prepared (Hour 2).** See `DATASET.md` for details.

### Reproducing the data pipeline (Hour 2)

```bash
# 1. Download + extract the raw archive (sha256-verified; no-op if present)
python scripts/download_dataset.py

# 2. Validate every image -> data/dataset_validation.{json,csv}
python scripts/validate_dataset.py

# 3. Leakage-safe split (content-group level, seed 42) -> processed splits,
#    data/manifest.csv, data/dataset_summary.json
python scripts/prepare_dataset.py

# 4. Visual sanity grid -> data/samples/sanity_grid.png
python scripts/visualize_dataset.py

# 5. Pipeline tests
python -m pytest tests/test_data_pipeline.py
```

Outputs:

- `data/raw/cp-anemic/` — immutable raw dataset (gitignored)
- `data/processed/{train,val,test}/{anemic,non_anemic}/` — 224×224 RGB crops
- `data/manifest.csv` — every image: split, label, subject, content group, metadata
- `data/dataset_summary.json` — split counts, class distribution, leakage notes
- `data/dataset_validation.csv` — per-file validation status + quality metrics

## Model status

**Hour 3: classical baseline complete.** Random Forest on 19 RGB/LAB color
features (tissue-masked): test accuracy 0.876, anemic-class recall 0.889,
anemic F1 0.901, ROC-AUC 0.924. Full details: `BASELINE_RESULTS.md`.

Train the baseline yourself:

```bash
python scripts/train_baseline.py
# -> models/baseline_classifier.joblib
# -> data/results/baseline_metrics.json, baseline_confusion_matrix.png,
#    feature_importance.png, baseline_latency.json
```

**Hour 4 (complete):** fine-tuned MobileNetV2 on GPU (RTX 5050). The CNN is
faster but less accurate on this small dataset: test acc 0.752 / anemic
recall 0.792 / F1 0.803 / AUC 0.821. **Random Forest remains the best
model.** See `CNN_RESULTS.md` + `MODEL_COMPARISON.md`.

Train the CNN yourself (GPU-enabled):

```bash
python scripts/train_cnn.py --epochs-finetune 60 --patience 15
# -> models/mobilenetv2_best.pth + models/mobilenetv2_metadata.json
# -> data/results/cnn_metrics.json, cnn_confusion_matrix.png, cnn_latency.json
```

## Inference engine (Hour 5)

```python
from app.ai.inference import AnemiaInferenceEngine

engine = AnemiaInferenceEngine()   # AI_MODEL=random_forest (default) | cnn
engine.load()                      # loads the model once
result = engine.analyze(image)     # dict: prediction / image_quality / inference
```

```bash
python scripts/test_inference.py <image_path>   # single image → structured JSON
python scripts/test_inference.py --samples      # self-test: good / poor / invalid
python scripts/benchmark_inference.py           # 113-image benchmark → JSON
```

Details, error codes, and example output: `INFERENCE.md`.

## FastAPI service (Hour 6)

```bash
# Start the server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Open Swagger UI
# http://localhost:8000/docs
```

**Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/models` | Model metadata |
| `POST` | `/api/v1/anemia/screen` | Screening prediction (multipart image) |

**Quick test (curl):**

```bash
curl -X POST -F "image=@path/to/image.png" http://localhost:8000/api/v1/anemia/screen
```

Full API contract: `AI_API_CONTRACT.md`
API documentation: `API.md`

## Medical disclaimer

This project is a hackathon prototype for **research/educational use**. It
performs non-invasive anemia *screening* from photographs and is **not** a
medical device, does **not** provide a clinical diagnosis, and has **not**
been clinically validated. It must not replace blood tests or professional
medical advice. The model only predicts the classes present in its training
dataset (anemia / non-anemia); no severity claims are made.
