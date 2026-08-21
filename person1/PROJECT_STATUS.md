# PROJECT_STATUS.md

**PRAHARI — Person 1 (AI/CV) · Hour 1 of 10**
_All values below were verified on the machine on 2026-08-17. Nothing is assumed or fabricated._

## Environment

| Item | Value |
| --- | --- |
| Current directory | `C:\Users\Viraj Akili\OneDrive\Desktop\person1` (bash: `/c/Users/Viraj Akili/OneDrive/Desktop/person1`) |
| Operating system | Windows 10 (build 10.0.26200), AMD64 |
| CPU | 20 logical cores (`os.cpu_count()` = 20) |
| GPU | NVIDIA GeForce RTX 5050 Laptop GPU — 8151 MiB VRAM (~8 GB) |
| GPU driver | NVIDIA-SMI 595.95 |
| CUDA (driver capability) | 13.2 (reported by `nvidia-smi`) |
| Python | 3.11.9 — `C:\Users\Viraj Akili\AppData\Local\Programs\Python\Python311\python.exe` |
| pip | 26.1.2 (Python 3.11) |

## Git

| Item | Value |
| --- | --- |
| Repository | `C:\Users\Viraj Akili\OneDrive\Desktop\person1` (initialized, no commits yet) |
| Branch | `master` |
| Remote `origin` | `https://github.com/Viraj-Akili/anemia-detection.git` (fetch + push configured, verified) |
| Commit history | none — `git log` reports "no commits yet" |

## Installed packages (verified via `importlib.metadata`)

| Package | Version |
| --- | --- |
| torch | 2.12.1 **+cpu** (CPU-only build) |
| torchvision | 0.27.1 |
| opencv-python | 4.13.0.92 |
| numpy | 1.26.4 |
| fastapi | 0.137.2 |
| uvicorn | 0.49.0 |
| python-multipart | 0.0.32 |
| pydantic | 2.13.4 |
| pillow | 12.2.0 |
| scikit-learn | 1.9.0 |
| pandas | 3.0.3 |
| matplotlib | 3.10.9 |
| python-dotenv | 1.0.1 |
| tqdm | 4.68.3 |
| requests | 2.34.2 |
| pytest | **NOT installed** (needed for tests) |

## CUDA status — IMPORTANT

- A physical NVIDIA GPU **is present** (RTX 5050, 8 GB) and the driver supports CUDA 13.2.
- The installed PyTorch is the **CPU-only build**: `torch.cuda.is_available()` → `False`, `torch.version.cuda` → `None`.
- **Conclusion:** GPU training is *not possible today* with the current torch install. To use the GPU we must reinstall a CUDA-enabled torch build (see `MODEL_PLAN.md` § Training requirements). This is the #1 decision for Hour 2.
- Until then, all torch work runs on CPU (20 cores).

## Project state

| Area | Status |
| --- | --- |
| Code | Pipeline logic implemented (`app/data_pipeline.py`, `app/ai/preprocessing.py`, `app/ai/quality_gate.py`); scripts in `scripts/`; API still placeholder |
| Dataset | **Downloaded, validated, split (Hour 2).** 708 usable images, leakage-safe 70/15/15 split (seed 42) — see `DATASET.md` |
| Model | **Not trained.** Plan documented in `MODEL_PLAN.md` |
| Metrics | None — nothing trained, no fabricated numbers |
| API | Placeholder routes only (`app/api/anemia.py` returns "not implemented") |

## Hour 6 (FASTAPI AI SERVICE = COMPLETE ✅)

- Rewrote `app/main.py` with FastAPI lifespan (model loaded once at startup);
  CORS middleware configurable via `CORS_ORIGINS` env var.
- Rewrote `app/api/anemia.py`: `POST /api/v1/anemia/screen` — thin translation
  layer around `AnemiaInferenceEngine.analyze()`. Upload validation (format,
  size, empty), typed error→HTTP mapping, no stack traces exposed.
- `app/schemas/anemia.py`: Pydantic models for Prediction, ImageQuality,
  InferenceMetadata, ErrorDetail, HealthResponse, ModelInfo.
- `GET /health` — reports model loaded status; `GET /models` — model metadata.
- End-to-end verified: anemic/non-anemic samples → 200 success, missing → 422,
  bad format → 415, empty → 400, poor quality → success=false with error code.
- Docs: `AI_API_CONTRACT.md` (full contract + frontend/Swayam/Arya integration
  examples), `API.md` (setup + endpoints + config).
- Tests: `tests/test_api.py` (12 tests: health, models, valid screen, error
  handling, schema validation, no stack trace leakage) — **70 total passed**.

## Hour 5 (INFERENCE ENGINE = COMPLETE ✅)

- Built `AnemiaInferenceEngine` (`app/ai/inference.py`): load-once, `analyze()`
  (validate → quality gate → alpha-masked features → model → structured result)
  and `predict()`. Uses the saved RF pipeline as-is (features+scaler+clf).
- `app/ai/errors.py`: typed errors with stable codes (INVALID_IMAGE,
  IMAGE_TOO_LARGE, IMAGE_CORRUPTED, UNSUPPORTED_IMAGE, IMAGE_QUALITY_LOW,
  MODEL_NOT_LOADED, MODEL_CONFIG_ERROR).
- Quality gate extended (`app/ai/quality_gate.py`): per-check status + 0-1
  score; RGBA composited over white before metrics (fixed a bug where
  transparent pixels looked black → real crops rejected as too_dark).
- Alpha-mask feature extraction preserved; white-padding-immunity test added.
- Model switch: `AI_MODEL=random_forest` (default) | `cnn` (fallback).
- Fixed RF inference latency: n_jobs=-1 → 1 at load time (killed ~70 ms loky
  per-call overhead on Windows; trees identical).
- CLI: `scripts/test_inference.py <image>` + `--samples` (good/poor/invalid
  all verified). Benchmark: `scripts/benchmark_inference.py` — 113/113 images
  screened, 0 rejected; mean 58.4 ms, median 62.8 ms, p95 123.8 ms
  (`data/results/inference_benchmark.json`).
- Docs: `INFERENCE.md`; README + .env.example updated.
- Model decision: `models/baseline_classifier.joblib` (4.9 MB) **committed**
  (small, no sensitive data; regenerate via train_baseline.py);
  `models/mobilenetv2_best.pth` gitignored (regenerate via train_cnn.py).
- Tests: `tests/test_inference.py` (22) — **58 total passed**.

## Hour 4 (CNN TRAINING = COMPLETE ✅)

- **GPU enabled:** installed official torch 2.12.1+cu130 + torchvision 0.27.1+cu130
  (local wheels, `--no-deps`) → `torch.cuda.is_available() = True`, RTX 5050 (CUDA 13.0).
  Note: a plain `pip install --force-reinstall torchvision` from the index silently
  reinstalled CPU torch — fixed by installing wheels with `--no-deps`.
- Trained **MobileNetV2** (2.2 M params, ImageNet-pretrained) two-stage on GPU:
  head-only (8 ep, lr 1e-3) then features[14:] fine-tune (AdamW lr 1e-4, early
  stop patience 15). Unweighted BCE (anemic = majority + priority class).
- Best checkpoint by validation anemic F1 (0.769 @ epoch 48). Two training runs
  (run 2 converged with early stopping).
- **Test (final CNN):** acc 0.752, anemic recall 0.792, anemic F1 0.803, AUC 0.821.
  **Random Forest remains the better model** (0.876 / 0.889 / 0.901 / 0.924).
  CNN is faster: 16.5 ms CPU / 8.6 ms GPU per image vs 55.6 ms RF.
- Artifacts: `models/mobilenetv2_best.pth` + `mobilenetv2_metadata.json`,
  `data/results/cnn_metrics.json`, `cnn_confusion_matrix.png`, `cnn_latency.json`,
  `cnn_training_history.csv`, `model_comparison.json`; `CNN_RESULTS.md`,
  `MODEL_COMPARISON.md`.
- Tests: `tests/test_cnn.py` (7 passed, 1 GPU test now enabled) — **35 total passed**.

## Hour 3 (CLASSICAL BASELINE = COMPLETE ✅)

- Implemented `app/ai/features.py` (19 RGB/LAB color features over
  alpha-masked tissue pixels, sklearn transformer) and `scripts/train_baseline.py`.
- Trained Logistic Regression + Random Forest (class-balanced) on the Hour-2
  splits; scaler fit on TRAIN only.
- Selected Random Forest on validation anemic F1 (0.791 vs 0.660) / AUC
  (0.920 vs 0.698). Test evaluated ONCE: accuracy 0.876, anemic recall 0.889,
  anemic F1 0.901, non-anemic F1 0.833, ROC-AUC 0.924.
- Saved `models/baseline_classifier.joblib` (loadable via `app/ai/inference.py`).
- Artifacts: `data/results/baseline_metrics.json`, `baseline_confusion_matrix.png`,
  `feature_importance.png`, `baseline_latency.json` (mean 55.6 ms/image, CPU).
- Fixed a metric bug: roc_auc_score was encoding string labels
  alphabetically (anemic→0), inverting AUC — corrected in `train_baseline.py`.
- Tests: `tests/test_features.py` + `tests/test_baseline.py` — **28 passed**.
- GPU: torch remains CPU-only (2.12.1+cpu); CUDA install deferred to Hour 4.

## Hour 2 (DATA PIPELINE = COMPLETE ✅)

- Dataset downloaded from official Mendeley source; sha256 verified
  (`78d7c2ec…d319c`); raw archive preserved at `data/raw/` (immutable, gitignored).
- Every image validated (`data/dataset_validation.json`/`.csv`): 710 total,
  **708 usable**, 2 rejected (label conflict: Image_188/Image_310, recorded
  not deleted). 212 byte-identical duplicate files detected.
- Labels verified from the sheet (REMARK): anemic 423 / non_anemic 285.
  Canonical map `anemic→1`, `non_anemic→0` in `app/data_pipeline.py`.
- Leakage: split unit = md5 content group (identical images never span
  splits — verified 0 cross-split groups); stratified by (label, hospital);
  deterministic seed 42.
- Split (images): train 498 (304/194), val 97 (47/50), test 113 (72/41).
- Preprocessing: RGBA→RGB over white, aspect-preserve + white pad to 224×224
  (`app/ai/preprocessing.py`); augmentation deferred to training time.
- Artifacts: `data/manifest.csv`, `data/dataset_summary.json`,
  `data/samples/sanity_grid.png`, `data/processed/{train,val,test}/…`.
- Tests: `tests/test_data_pipeline.py` — **16 passed** (`pytest`).
- New dependency: `openpyxl` (xlsx metadata). Helper binaries under
  `scripts/tools/` (7-Zip, gitignored).

Hour 2 acceptance: all checklist items complete (dataset source verified;
raw preserved; all images validated; labels verified; invalid documented;
duplicates checked; leakage considered; subject/content-level split;
deterministic split; class distribution documented; preprocessing works;
augmentation separated; manifest + summary exist; sanity visualization
exists; tests pass; README/DATASET/PROJECT_STATUS updated).

## Hour-1 checklist

- [x] repository verified
- [x] Git remote verified (origin → anemia-detection)
- [x] environment inspected (Python, pip, packages, CPU, GPU, CUDA)
- [x] PROJECT_STATUS.md created
- [x] DATASET.md created
- [x] dataset selected (CP-AnemiC)
- [x] MODEL_PLAN.md created
- [x] project structure created
- [x] config created (app/config.py + .env.example)
- [x] requirements.txt created
- [x] .gitignore created
- [x] README.md created

## Medical rule reminder

This component produces a **screening signal only** (anemia / non-anemia from the dataset's own labels). It does **not** diagnose, does **not** estimate clinical severity, and no hemoglobin thresholds beyond the dataset's own definition are invented here. Final risk level and action belong to Swayam's component.
