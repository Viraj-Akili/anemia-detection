# MODEL_PLAN.md

**PRAHARI — Person 1 (AI/CV) · Model strategy for the selected dataset (CP-AnemiC)**
_Updated Hour 3 (2026-08-17): classical baseline implemented — see BASELINE_RESULTS.md._
_Plan for the CNN is unchanged; the baseline is the reference point it must beat._

## 1. Input modality

Photograph of the **palpebral conjunctiva** (lower eyelid) of one eye — the modality CP-AnemiC provides and the modality PRAHARI's phone app would capture.

**Open question to resolve at download (Hour 2):** whether the dataset ships ROI-cropped conjunctiva images or full-eye images with separate ROIs. The ROI stage (`app/ai/roi.py`) is designed either way; if full-eye images ship, we crop to the conjunctiva before model input (or use the shipped ROIs if they are part of the package).

## 2. Input dimensions

- Plan A (default): **224 × 224 × 3 RGB** — MobileNet family default, matches published CP-AnemiC work.
- Plan B (if CPU-bound): **160 × 160** or **128 × 128** as a speed test — verify accuracy impact before committing.
- Preprocessing per image: decode → ROI crop → resize to square → normalize with ImageNet mean/std (for transfer learning). Keep color in RGB; no grayscale (pallor is a color signal).

## 3. Target labels

- **Binary:** `anemic` / `non-anemic` — exactly the classes the dataset defines (lab Hb < 11 g/dL for 6–59 months per WHO).
- **No severity classes.** The dataset does not define low/moderate/high; we will not invent them.
- Output of the model: probability of the `anemic` class + confidence. Final risk level is Swayam's job.

## 4. Baseline model (IMPLEMENTED — Hour 3)

- **Features (19, interpretable):** RGB mean/std, LAB mean/std, color ratios
  (R/(R+G+B), R−G, R−B), R and a* percentiles (p10/p90) — computed over
  **tissue pixels** (alpha-masked) of the raw ROI crops (`app/ai/features.py`).
- **Scaling:** StandardScaler fitted on TRAIN only, applied to val/test.
- **Classifiers:** Logistic Regression + Random Forest (both
  class_weight="balanced"), compared on the same leakage-safe splits.
- **Selection:** Random Forest won on validation anemic-class F1 (0.791 vs
  0.660) and ROC-AUC (0.920 vs 0.698).
- **Test (once):** accuracy 0.876, anemic recall 0.889, anemic F1 0.901,
  ROC-AUC 0.924. Mean inference 55.6 ms/image (CPU).
- **Reference for Hour 4:** the CNN should beat these numbers, especially
  **anemic-class recall (currently 0.889)**.
- Saved: `models/baseline_classifier.joblib` (features + scaler + RF).

## 5. CNN architecture (IMPLEMENTED — Hour 4)

- **Primary: MobileNetV2** (torchvision `mobilenet_v2`), ImageNet-pretrained, final layer replaced with `Dropout(0.2) → Linear(1280, 1)` (single logit).
- 2,225,153 params (~2.2 M); input 224×224×3; `app/ai/cnn_model.py` factory with save/load.
- **Result on this dataset: CNN converges to a lower plateau than the classical baseline** — see CNN_RESULTS.md and MODEL_COMPARISON.md. Test: acc 0.752, anemic recall 0.792, F1 0.803, AUC 0.821 (vs RF 0.876 / 0.889 / 0.901 / 0.924). The color-feature Random Forest captures most of the available signal on 498 training images.
- **Verdict:** Random Forest is the deployed screening model; CNN kept as a faster (16.5 ms CPU / 8.6 ms GPU) fallback and for future data. Training: two-stage (head-only then features[14:] fine-tune), AdamW, early stopping on validation anemic F1, unweighted BCE (majority class = priority class).
- Alternatives (EfficientNet-Lite0, MobileNetV3) remain available via the same factory but were not pursued given the RF result and time budget.

## 6. Transfer learning strategy

- Start from ImageNet-pretrained MobileNetV2 weights.
- Replace the classifier head with `Linear(1280, 1)` + sigmoid.
- **End-to-end fine-tuning** of all layers (matches the published CP-AnemiC approach): Adam, lr ≈ 1e-4, Binary Cross-Entropy, batch 32.
- Data augmentation **in the training loop only**: random horizontal flip, small rotation, small shifts, small scaling (same family as the reference paper). Never applied to validation/test.
- Early stopping on validation F1 (patience ~10 epochs, per reference work), save best weights.
- Expected: with 710 images this converges in a small number of epochs (reference: ~26 epochs).

## 7. Evaluation metrics

- **Primary:** Recall (sensitivity) and F1 on the `anemic` class — screening must not miss anemia cases.
- **Also reported:** accuracy, precision, recall, F1, ROC-AUC, per-class confusion matrix, and calibration check (does predicted probability ≈ observed rate?).
- **Protocol:** stratified 5-fold CV for development; reserve a **held-out test split** (~15–20%) that is never used for tuning and is reported once at the end. Splits stratified by class and by collection site; subject-level integrity (see `DATASET.md` leakage notes).
- No fabricated metrics — numbers only after real evaluation.

## 8. Expected training requirements

- **Dataset:** 710 images @ 224×224 — small.
- **GPU is available but torch is CPU-only today.** RTX 5050 (8 GB) present; the installed torch (2.12.1+cpu) cannot use it.
  - **Decision needed in Hour 2:** reinstall CUDA-enabled torch (e.g. `pip install torch torchvision --index-url https://download.pytorch.org/whl/cu130` — verify the right wheel for the driver, CUDA 13.2) → GPU training in minutes/epochs.
  - **CPU fallback (no install):** MobileNetV2 fine-tune on 20 cores is feasible for 710 images but noticeably slower; acceptable if the user prefers to skip the ~2.5 GB torch reinstall.
- Memory: 8 GB VRAM is ample for batch 32 @ 224² on MobileNetV2.

## 9. Expected inference requirements

- Target: **< 100 ms per image on CPU** (well under on a phone GPU/edge device) for MobileNetV2-class models.
- Pipeline latency is dominated by ROI detection + preprocessing; keep both OpenCV-based and vectorized.
- Deployment path (later hours, not Hour 1): export to ONNX (FP32/FP16) for phone integration; the 2025 quantization paper shows FP16 keeps accuracy on this dataset while INT8 degrades it — so prefer FP16, skip INT8 unless needed.
- API returns: `prediction` (anemic/non-anemic), `probability`, `confidence`, plus optional explainability artifact.

## 10. Known limitations

- **Pediatric, Ghana-only dataset** — model does not generalize to adults/other regions without retraining; must be stated in any output.
- Small dataset (710) → risk of overfitting; mitigated by augmentation, CV, early stopping; results are prototype-level, not clinically validated.
- Tablet-capture conditions differ from arbitrary phone photos — the quality gate should reject out-of-distribution images (blurry, poor lighting, wrong anatomy).
- Confidence scores are model probabilities, not calibrated clinical risk; the multimodal engine must not treat them as such.
- No severity classification — only anemia / non-anemia, per dataset labels.
