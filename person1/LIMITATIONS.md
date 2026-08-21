# System & Model Limitations — PRAHARI AI/CV Service

**PRAHARI — Person 1 (AI/CV) · Engineering & Clinical Limitations Disclosure**

---

## 1. Research Prototype Disclosure

> [!WARNING]
> The PRAHARI AI/CV anemia screening service is a **non-clinical research prototype**. It is designed solely for automated computer-vision signal extraction and preliminary non-invasive screening. It is **NOT a medical diagnostic device**, has not received regulatory clearance (e.g., FDA, CE-IVD, CDSCO), and must never be used as a standalone basis for clinical diagnosis, treatment decisions, or emergency medical triage.

---

## 2. Dataset Constraints & Demographic Scope

1. **Dataset Size:**
   - The model was trained and evaluated on the **CP-AnemiC** dataset (Mendeley Data `10.17632/m53vz6b7fx.1`), comprising **708 conjunctival photographs** across 354 pediatric subjects (2 images per subject: one per eye).
   - Although partitioned strictly by subject into train/val/test splits (80/20 train-val / held-out test), 708 images is a modest sample size for deep representation learning.

2. **Demographic Homogeneity:**
   - The dataset consists exclusively of pediatric subjects aged **6 to 59 months** in a single geographic cohort in **Ghana**.
   - The model has not been calibrated or validated across:
     - Adult populations, adolescents, or elderly individuals.
     - Pregnant women (a high-risk anemia demographic).
     - Diverse global populations with varying scleral pigmentation, conjunctival vascularization patterns, and skin tones.
     - Subjects with co-morbid ocular conditions (e.g., conjunctivitis, trachoma, pinguecula, pterygium, jaundice/icterus).

---

## 3. False Positives & False Negatives

1. **Error Profile:**
   - The primary Random Forest baseline (`random_forest_color_baseline v1.0`) relies on alpha-masked colorimetry features (RGB, LAB, HSV statistics) from the palpebral conjunctiva.
   - **False Positives:** May occur due to bright flash artifacts, local conjunctival hyper-pigmentation, or ambient lighting shifts that mimic tissue pallor.
   - **False Negatives:** Mild or borderline anemia (Hb 10.0–10.9 g/dL) often presents with minimal visible pallor changes, leading to possible false negative screening.

2. **Lighting and Camera Variations:**
   - Image capture variability across different smartphone camera sensors, automatic white balance (AWB) algorithms, lens flares, and varying ambient color temperatures can shift color values.
   - The engineering Quality Gate filters out extreme underexposure, overexposure, and blur, but subtle color shifts remain an uncalibrated source of variance.

---

## 4. Model Probability vs. Clinical Probability

1. **Statistical vs. Clinical Interpretation:**
   - `prediction.model_probability` is the internal Random Forest ensemble tree vote proportion (0.0 to 1.0) indicating proximity to the "anemic" feature cluster.
   - **It is NOT a clinical probability of disease.**
   - **It is NOT a hemoglobin (Hb) concentration measurement** (e.g., g/dL).
   - High model probability does not imply severe clinical anemia; low model probability does not guarantee absence of micronutrient deficiency.

2. **Multimodal Role:**
   - The AI screening signal is designed strictly as one input to be fused by **Swayam's PRAHARI Multimodal Risk Engine** with:
     - Mid-Upper Arm Circumference (MUAC) and growth metrics.
     - Dietary diversity scores and nutritional recall.
     - Clinical symptoms (fatigue, shortness of breath, pica, dizziness).
     - Previous health center visits and demographic risk factors.

---

## 5. Summary Matrix

| Dimension | Current State | Production / Clinical Target |
|---|---|---|
| **Sample Size** | 708 images (354 patients) | 10,000+ multi-center images |
| **Demographics** | Pediatric (6–59 mo, Ghana) | Multi-age, multi-ethnic cohorts |
| **Device Diversity** | Single smartphone type | Multi-OEM smartphone cameras with color calibration charts |
| **Ground Truth** | Point-of-care HemoCue / CBC | Laboratory auto-analyzer CBC (gold standard) |
| **Regulatory Status** | Hackathon Research Prototype | CDSCO / FDA SaMD clearance |
