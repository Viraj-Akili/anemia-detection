# INFERENCE.md

**PRAHARI — Person 1 (AI/CV) · Production inference engine (Hour 5, 2026-08-17)**

## 1. Inference architecture

```
image (path | PIL | bytes)
  → validate (exists / decodes / format / size)
  → quality gate (blur, brightness, contrast, resolution, tissue)   [REJECT if poor]
  → alpha-masked RGB/LAB tissue features (19)                       [RF model]
  → saved scaler + Random Forest  (or MobileNetV2 fallback)
  → screening signal: label + model probability + model confidence
  → structured result
```

Implemented as `AnemiaInferenceEngine` in `app/ai/inference.py`:

```python
engine = AnemiaInferenceEngine()   # AI_MODEL=random_forest (default)
engine.load()                      # loads the model ONCE
result = engine.analyze(image)     # full pipeline → structured dict
pred = engine.predict(image)       # light path → AnemiaPrediction
```

The saved Random Forest pipeline (`models/baseline_classifier.joblib`)
**already contains** feature extraction + scaler + classifier, so nothing is
duplicated. The engine only adds decode, validation, and the quality gate.

## 2. Preprocessing

No image preprocessing is re-implemented: the model's own
`ColorFeatureExtractor` reads the image path directly.

## 3. Alpha masking (critical)

Features are computed from the **RAW RGBA crop's tissue pixels only**
(alpha > 10), never from the white-padded 224×224 image. This is what the
Hour-3 baseline was trained on; the engine preserves it exactly. Test
`test_white_padding_does_not_contaminate_features` verifies that a white
background does not shift the color statistics.

## 4. Quality gate

`app/ai/quality_gate.py` — runs **before** the model. Checks (with observed
CP-AnemiC ranges, intentionally lenient — arbitrary medical thresholds are
not invented):

| check | threshold | dataset range |
| --- | --- | --- |
| blur (Laplacian var) | ≥ 50 | 70–3492 |
| brightness | 30–250 | 173–249 |
| contrast | ≥ 10 | 15–98 |
| resolution (min side) | ≥ 16 px | — |
| tissue (alpha coverage) | ≥ 0.10 | 0.08–0.48 |

RGBA images are alpha-composited over white **before** metric computation
(fixed in Hour 5: dropping alpha counted transparent pixels as black and
wrongly rejected real crops as `too_dark`).

Score = 1.0 − Σ penalties of failed checks (blur .35, dark .25, bright .15,
contrast .15, resolution .20, tissue .15), clamped to [0,1]. Engineering
score for retake prioritization — not a clinical measure.

If quality is poor, the model is **not run**: `analyze` returns
`success: false` with code `IMAGE_QUALITY_LOW`; `predict` raises
`ImageQualityLowError`.

## 5. Model

- Primary: **random_forest_color_baseline** (v1.0, `AI_MODEL=random_forest`)
- Fallback: **mobilenet_v2_cnn** (v1.0, `AI_MODEL=cnn`, faster but less
  accurate — never the default)
- Model metadata: name, version, dataset (CP-AnemiC), feature pipeline,
  training seed 42, model path — returned in every successful result.

## 6. Confidence

`model_probability` = RF `predict_proba` for the anemic class.
`model_confidence` = probability of the predicted class.
These are **model probabilities for the predicted class**, not clinical
probability, not a diagnosis, and not a risk level. Swayam's multimodal
engine computes final risk.

## 7. Errors

Typed exceptions in `app/ai/errors.py` (API layer will map to HTTP):

| code | status | when |
| --- | --- | --- |
| INVALID_IMAGE | 400 | missing file, bad input type, too small |
| IMAGE_TOO_LARGE | 400 | long side > max_image_size (4096 px) |
| IMAGE_CORRUPTED | 400 | cannot decode |
| UNSUPPORTED_IMAGE | 415 | unsupported format/mode |
| IMAGE_QUALITY_LOW | 422 | quality gate rejected (analyze returns it; predict raises) |
| MODEL_NOT_LOADED | 503 | engine used before load() |
| MODEL_CONFIG_ERROR | 500 | unknown AI_MODEL |

## 8. Latency (measured, `data/results/inference_benchmark.json`)

RF engine over the 113-image test split (model load 1.2 s one-time,
excluded):

| | mean | median | p95 |
| --- | --- | --- | --- |
| total per image | 58.4 ms | 62.8 ms | 123.8 ms |

Breakdown: decode ~3–7 ms, quality gate ~1–3 ms, features+predict ~30–60 ms.
~20 ms of the predict cost is sklearn single-sample RF call overhead
(fixed: `n_jobs=-1`→1 cut ~70 ms of loky overhead). Well below typical API
budgets; the CNN path is ~16 ms CPU / ~9 ms GPU if ever needed.

## 9. Example output

```json
{
  "success": true,
  "prediction": {
    "label": "anemic",
    "model_probability": 0.912,
    "model_confidence": 0.912
  },
  "image_quality": {"status": "good", "score": 0.85, "checks": {"blur": "pass", "brightness": "pass", "contrast": "pass", "resolution": "pass", "tissue": "pass"}, "reasons": []},
  "inference": {
    "model": "random_forest_color_baseline",
    "version": "1.0",
    "model_path": "models/baseline_classifier.joblib",
    "dataset": "CP-AnemiC (Mendeley 10.17632/m53vz6b7fx.1)",
    "latency_ms": 58.4
  },
  "timings_ms": {"decode_ms": 3.7, "quality_ms": 1.6, "features_ms": 45.0, "predict_ms": 45.0, "total_ms": 58.4}
}
```

Quality-rejected:

```json
{"success": false, "prediction": null,
 "image_quality": {"status": "poor", "score": 0.65, "checks": {"blur": "fail", ...}, "reasons": ["blur"]},
 "inference": null,
 "error": {"code": "IMAGE_QUALITY_LOW", "message": "Image quality is insufficient. Please retake the image."}}
```

## 10. Boundary with Swayam

The engine returns an **image-based anemia screening signal only**. It does
not compute final risk, nutrition risk, severity, WHO rules, or referrals.

## 11. CLI + benchmark

```bash
python scripts/test_inference.py <image_path>   # single image (readable JSON)
python scripts/test_inference.py --samples      # self-test: good / poor / invalid
python scripts/benchmark_inference.py           # 113-image benchmark → JSON
```

## 12. Model file decision (Phase 18)

- `models/baseline_classifier.joblib` (4.9 MB) — **committed to the repo**:
  small, no sensitive data, lets teammates run inference immediately
  without retraining. Regenerate with `python scripts/train_baseline.py`.
- `models/mobilenetv2_best.pth` (8.8 MB) — **gitignored** (`models/*.pth`);
  regenerate with `python scripts/train_cnn.py`.
- Raw/processed datasets, `.env`, downloaded tools — gitignored.
