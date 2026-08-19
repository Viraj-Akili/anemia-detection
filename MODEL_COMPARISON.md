# MODEL_COMPARISON.md

**PRAHARI — Person 1 (AI/CV) · Random Forest vs MobileNetV2 CNN (Hour 4)**

Both models were evaluated on the **same held-out test split** (113 images,
Hour-2 leakage-safe split, seed 42). All values are measured
(`data/results/model_comparison.json`). Screening research prototype —
no clinical validity claimed.

## Test metrics

| metric | Random Forest | CNN (MobileNetV2) |
| --- | --- | --- |
| accuracy | **0.876** | 0.752 |
| anemic precision | **0.914** | 0.814 |
| anemic recall | **0.889** | 0.792 |
| anemic F1 | **0.901** | 0.803 |
| non-anemic F1 | **0.833** | 0.667 |
| ROC-AUC | **0.924** | 0.821 |

## Inference latency (per image, excludes model load)

| | Random Forest | CNN |
| --- | --- | --- |
| CPU mean / median / p95 | 55.6 / 53.4 / 66.6 ms | **16.5 / 16.0 / 21.8 ms** |
| GPU mean | — | 8.6 ms |

## Model size

| | Random Forest | CNN |
| --- | --- | --- |
| size on disk | 5.13 MB (joblib) | 9.15 MB (state dict) |
| parameters | 19 features → 500 trees | 2,225,153 |

## Test-set evaluation history (transparency)

- **Random Forest:** evaluated **once** — the test set is untouched w.r.t.
  the baseline.
- **CNN:** evaluated **once per training run** (2 runs; run 2 with early
  stopping is the final CNN). Test was used only for final reporting, never
  for model selection (selection = validation anemic-class F1). After the
  first CNN test evaluation, training was continued purely based on
  validation curves; the test set can no longer be called *completely*
  untouched for the CNN.

## Verdict

**Random Forest is the better screening model on this dataset**
(accuracy, anemic recall/F1, ROC-AUC all higher). The CNN's advantages are
speed (3.4× faster on CPU, GPU-capable) and representational headroom —
but with 498 training images it converges to a lower plateau.

**Recommendation:** ship the **Random Forest** as the Person-1 screening
model for the API (Hour 5+). Keep the CNN checkpoint for experimentation;
revisit CNN training only if more labeled data arrives. A hybrid option
(CNN features + RF head) is a possible future experiment, but should not be
pursued within this hackathon's time budget.
