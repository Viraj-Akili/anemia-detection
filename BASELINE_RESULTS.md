# BASELINE_RESULTS.md

**PRAHARI — Person 1 (AI/CV) · Classical CV baseline (Hour 3, 2026-08-17)**

All numbers below are **measured** on the leakage-safe Hour-2 splits
(train 498 / val 97 / test 113; content-group level, seed 42). Nothing is
fabricated. This is a screening **research prototype** — no clinical
validity is claimed.

## 1. Feature design

19 interpretable color features, extracted from the **raw ROI crops** using
the alpha channel as a tissue mask (transparent background excluded, so the
signal is conjunctiva color, not padding):

- RGB tissue pixels: R/G/B mean, R/G/B std (6)
- LAB tissue pixels: L/a*/b* mean, L/a*/b* std (6)
- Color ratios: R/(R+G+B), R−G, R−B (3) — redness proxies for pallor
- Distribution tails: R p10/p90, a* p10/p90 (4)

Deterministic; no NaN on the full dataset. Implementation:
`app/ai/features.py` (`ColorFeatureExtractor`, a sklearn transformer).

## 2. Logistic Regression (validation)

class_weight="balanced", max_iter 3000, features + StandardScaler (fit on train only)

| metric | value |
| --- | --- |
| accuracy | 0.660 |
| precision (anemic) | 0.640 |
| recall (anemic) | 0.681 |
| F1 (anemic) | 0.660 |
| ROC-AUC | 0.698 |

## 3. Random Forest (validation)

n_estimators=500, class_weight="balanced", seed 42

| metric | value |
| --- | --- |
| accuracy | 0.814 |
| precision (anemic) | 0.872 |
| recall (anemic) | 0.723 |
| F1 (anemic) | 0.791 |
| ROC-AUC | 0.920 |

## 4. Selected baseline

**Random Forest** — selected on **validation anemic-class F1** (0.791 vs
0.660 for LR) with a much better validation ROC-AUC (0.920 vs 0.698).
No test data used for selection.

## 5. Validation results (selected model)

accuracy 0.814 · anemic precision 0.872 / recall 0.723 / F1 0.791 ·
non-anemic F1 0.833 · ROC-AUC 0.920.
Confusion (val, rows=true, cols=pred, [non_anemic, anemic]):
`[[45, 5], [13, 34]]` — 5 false positives, 13 missed anemic (of 47).

## 6. Test results (final, evaluated ONCE)

accuracy **0.876** · anemic precision **0.914** / recall **0.889** / F1 **0.901** ·
non-anemic precision 0.814 / recall 0.854 / F1 0.833 · ROC-AUC **0.924** (n=113)

Confusion matrix (test):

```
              predicted
              non_anemic  anemic
true non_anemic    35        6
true anemic         8       64
```

## 7. Confusion matrix interpretation

- **8 of 72 anemic cases missed (recall 0.889)** — the screening signal
  would fail to flag 11% of anemic samples. For a screening prototype this
  is the number to watch; the CNN (Hour 4) should aim to reduce it.
- **6 of 41 non-anemic flagged as anemic** — false positives are less
  harmful for screening (they route to confirmatory testing) but still noisy.

## 8. Latency

Per-image pipeline latency (feature extraction + prediction, excluding
one-time model load; 339 measurements = 113 test images × 3 repeats):

| statistic | ms |
| --- | --- |
| mean | 55.6 |
| median | 53.4 |
| p95 | 66.6 |

## 9. Feature importance (engineering interpretation only)

Random Forest feature importances are **flat** (top feature a_std ≈ 0.069;
all 19 features between ~0.03 and 0.07) — the predictive signal is spread
across many color statistics rather than one channel. Top features:
a_std, b_lab_std, r_p90, b_mean, r_minus_g, r_mean, b_lab_mean, a_mean.

These are **features associated with model prediction** for engineering
interpretation. They are NOT claimed to be medical causes of anemia.

## 10. Limitations

- Prototype screening signal, not a diagnosis; not clinically validated.
- Color features cannot capture texture/anatomy; the CNN should do better
  or confirm the ceiling.
- Duplication in the dataset (212 redundant copies) inflates effective
  training size — mitigated by content-group splits.
- Latency measured on CPU (no GPU used); ~55 ms/image is already
  real-time for screening.
- Threshold was NOT tuned after the test evaluation; the test set remains
  untouched by model selection.

## Artifacts

- `models/baseline_classifier.joblib` — full pipeline (features + scaler + RF)
- `data/results/baseline_metrics.json` — validation + test metrics
- `data/results/baseline_confusion_matrix.png`
- `data/results/feature_importance.png`
- `data/results/baseline_latency.json`
