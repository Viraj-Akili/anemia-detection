# CNN_RESULTS.md

**PRAHARI — Person 1 (AI/CV) · MobileNetV2 CNN (Hour 4, 2026-08-17)**

All numbers are **measured** on the Hour-2 leakage-safe splits (train 498 /
val 97 / test 113; content-group level, seed 42). Screening **research
prototype** — no clinical validity claimed. The Random Forest baseline
remains the better model for this dataset (see MODEL_COMPARISON.md).

## Architecture

- **MobileNetV2** (torchvision, ImageNet-pretrained), final classifier
  replaced with `Dropout(0.2) → Linear(1280, 1)` (single logit + sigmoid).
- Total parameters: **2,225,153** (~2.2 M). Input 224×224×3 RGB.
- Implementation: `app/ai/cnn_model.py` (factory + checkpoint save/load).

## Training strategy (two-stage, GPU)

- Stage 1 (head-only): backbone frozen, AdamW lr=1e-3, 8 epochs.
- Stage 2 (fine-tune): `backbone.features[14:]` unfrozen, AdamW lr=1e-4,
  up to 60 epochs, **early stopping** (patience 15 on validation anemic F1).
- Loss: unweighted BCEWithLogitsLoss (anemic = majority AND screening-
  priority class; documented strategy — `--pos-weight auto` available).
- Seed 42; best state snapshotted every epoch by **validation anemic F1**.
- Device: **NVIDIA RTX 5050 (CUDA 13.0, torch 2.12.1+cu130)**.

## Augmentation (train only; val/test deterministic)

RandomHorizontalFlip(0.5) · RandomRotation(10°, white fill) ·
RandomAffine(translate 0.05, scale 0.95–1.05, white fill) ·
ColorJitter(brightness 0.15, contrast 0.15 — **no hue/saturation**).

## Training history

Two runs were executed (test never used for selection):

| run | epochs | early stop | best val anemic F1 | best val epoch |
| --- | --- | --- | --- | --- |
| 1 (fixed 8+30) | 38 | no | 0.748 | 38 |
| 2 (early stop) | 55 | yes (patience 15) | **0.769** | 48 |

Run 1 stopped at a fixed epoch budget while validation was still climbing;
run 2 converged (early stop at epoch 55). Full per-epoch history:
`data/results/cnn_training_history.csv`.

## Validation metrics (best checkpoint, run 2)

accuracy **0.753** · anemic precision 0.702 / recall **0.851** / F1 **0.769** ·
non-anemic F1 0.733 · ROC-AUC **0.750**

## Test metrics (final checkpoint, evaluated once per run; run 2 is final)

| metric | value |
| --- | --- |
| accuracy | **0.752** |
| anemic precision | 0.814 |
| anemic recall | **0.792** |
| anemic F1 | **0.803** |
| non-anemic F1 | 0.667 |
| ROC-AUC | **0.821** |
| confusion (rows=true, [non_anemic, anemic]) | [[28, 13], [15, 57]] |

Confusion interpretation: **15 of 72 anemic test samples missed**
(recall 0.792) and 13 non-anemic flagged as anemic.

## Latency

Per-image (decode + transform + forward, batch 1; excludes model load):

| device | mean | median | p95 |
| --- | --- | --- | --- |
| CPU | 16.5 ms | 16.0 ms | 21.8 ms |
| GPU | 8.6 ms | — | — |

## Model size

- Checkpoint `models/mobilenetv2_best.pth`: **9.15 MB** (state dict + metadata)
- Parameters: 2,225,153 (2.2 M) — edge-deployable; ONNX/FP16 export is a
  later-hour option.

## Comparison with Random Forest (summary)

| metric | RF | CNN |
| --- | --- | --- |
| accuracy | 0.876 | 0.752 |
| anemic recall | 0.889 | 0.792 |
| anemic F1 | 0.901 | 0.803 |
| ROC-AUC | 0.924 | 0.821 |
| latency (CPU mean) | 55.6 ms | 16.5 ms |

The CNN is **faster but less accurate** on this small dataset. RF remains
the deployed screening model; the CNN is a viable speed-optimized fallback
or a candidate once more data becomes available.

## Limitations

- Small dataset (498 train images) — CNN plateaus around 0.75 validation
  anemic F1 despite convergence; the color-feature RF captures most of the
  available signal more efficiently.
- Test set was evaluated once per training run (2 CNN evaluations total,
  both after validation-based selection; never used for selection).
- Duplication in the dataset (212 redundant copies) inflates effective
  training size — mitigated by content-group splits.
- Prototype only: no clinical claims, no severity output.
