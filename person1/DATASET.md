# PRAHARI Anemia Dataset

**Status: Hour 2 (2026-08-17) — downloaded, validated, and split. See
"Hour 2 verification" below for the actual numbers.**
Modality decision is driven by what public data actually exists — see "Selected Dataset" below.

---

## Candidate 1

- **Name:** CP-AnemiC — A Conjunctival Pallor Dataset from Ghana
- **Source:** Mendeley Data (original deposition by Justice Williams Asare, Peter Appiahene, Emmanuel Donkoh); peer-reviewed dataset paper: "CP-AnemiC: A conjunctival pallor dataset and benchmark for anemia detection in children", *Medicine in Novel Technology and Devices* (2023)
- **URL:** https://data.mendeley.com/datasets/m53vz6b7fx/1 (DOI: 10.17632/m53vz6b7fx.1)
- **Modality:** Photographs of the **palpebral conjunctiva** (lower eyelid everted), captured with a 12 MP camera on a Samsung Galaxy Tab 7A tablet in ambient natural light (camera spotlight off). ROI of the conjunctiva pre-extracted via triangle thresholding + entropy grayscale.
- **Images:** **710**
- **Subjects:** 710 children aged **6–59 months** (dataset table reports patients = images, i.e. 1 image per child — verify at download)
- **Labels:** Anemic / non-anemic (binary), derived from **lab-measured hemoglobin** (Hb < 11 g/dL per WHO threshold for 6–59 months → anemic). Each record also carries Hb level, age, gender, collection site, and laboratory remark.
- **Class balance:** 424 anemic (60%) / 286 non-anemic (40%)
- **Demographics:** mean age 31.58 months; 306 female (43%) / 404 male (57%); collected from 10 healthcare facilities in Ghana, Jan–Jun 2022
- **License:** "academic purpose only"; must be cited. Not restricted to any particular use beyond academia; free download (Mendeley account required).
- **Advantages:** Largest public conjunctival pallor dataset; exactly the modality PRAHARI wants (smartphone/tablet-captured, non-invasive); **explicit binary anemia labels** matching our prediction target; published baselines exist (MobileNet ≈ 90–93% accuracy) to compare against; captured in realistic field lighting (not a controlled studio setup).
- **Limitations:** Pediatric only (6–59 months); single country (Ghana); tablet capture rather than a modern phone; class imbalance 60/40; exact file structure must be verified at download (whether ROI-cropped images are shipped or full-eye images + ROIs).

## Candidate 2

- **Name:** EYES-DEFY-ANEMIA — Eye conjunctiva photos of Indian and Italian patients
- **Source:** IEEE DataPort (original deposition by G. Dimauro, R. Maglietta, T. Bai, S. Kasiviswanathan); Kaggle mirror by harshwardhanfartale
- **URL:** https://ieee-dataport.org/documents/eyes-defy-anemia (DOI: 10.21227/t5s2-4j73) · Kaggle: https://www.kaggle.com/datasets/harshwardhanfartale/eyes-defy-anemia
- **Modality:** Eye / conjunctiva photographs (palpebral and forniceal), captured with a Samsung S6 smartphone fitted with a magnifying + standardized-white-LED lighting attachment (controlled conditions). Includes **manual segmentations** of palpebral / forniceal / palpebral+forniceal conjunctiva (1067×800 RGB) per image.
- **Images:** **218** (123 Italian + 95 Indian patients)
- **Subjects:** 218 (one eye image per patient folder)
- **Labels:** Lab-measured **Hb value**, age, and sex per patient in `.xlsx` files (no pre-baked binary label — anemia status must be derived from Hb, e.g. WHO adult thresholds; note the populations are adults, so adult thresholds apply, not the pediatric 11 g/dL cutoff)
- **License:** Free of charge for research; authors request citation of their papers.
- **Advantages:** Contains ground-truth **segmentation masks** (directly useful for ROI training); includes **subject IDs** (folder per patient); two populations (Italy + India); Hb as a continuous target enables regression as an alternative task.
- **Limitations:** Only 218 images (small for CNN training); captured under a **controlled lighting attachment**, which differs from real-world phone photos; no explicit anemia/non-anemia labels shipped; adult-only.

## Other options considered (not selected)

- **Harvard Dataverse — "Dataset for the detection of anaemia using conjunctival images" (2015, DOI 10.7910/DVN/L4MDKC):** oldest conjunctival dataset; access returned HTTP 403 during research; superseded by newer, better-documented datasets. Not usable as primary.
- **Fingernail/skin datasets** (e.g. Yakimov et al., "Dataset of human skin and fingernails images for non-invasive haemoglobin level assessment", Nature Scientific Data 2024, 250 patients; Mendeley "Detection of Anemia using Colour of the Fingernails Image"): real alternative modality, but smaller subject counts, mostly Hb-regression oriented, and no binary anemia labels; conjunctival pallor is better documented and directly matches the PRAHARI direction.

---

## Selected Dataset

**Name:** CP-AnemiC (A Conjunctival Pallor Dataset from Ghana)
**Source:** Mendeley Data — DOI 10.17632/m53vz6b7fx.1
**URL:** https://data.mendeley.com/datasets/m53vz6b7fx/1

### Why selected

1. **Modality matches PRAHARI:** non-invasive, photograph-based conjunctival pallor screening captured with a portable camera — the exact direction PRAHARI describes ("smartphone-based visual screening ... conjunctival/pallor-related images"). The dataset research itself confirmed conjunctival pallor is the viable public modality.
2. **Exact target label exists:** the dataset ships anemic / non-anemic classes (WHO Hb < 11 g/dL for 6–59 months), i.e. **anemia vs non-anemia**, which is precisely what our model must predict. No label conversion or invented thresholds needed.
3. **Size is workable for a 10-hour hackathon:** 710 images is the largest public conjunctival dataset, enough to fine-tune a small CNN with augmentation and 5-fold CV.
4. **Published baselines to compare against:** independent work (Appiahene et al. 2023; Cruz Romero & Lugo Beauchamp 2025) reports MobileNet-family accuracy ~90–93% on this exact dataset, giving us realistic reference points.
5. **Demographics + metadata:** age, gender, Hb, and collection site are provided, enabling subgroup reporting and leakage-aware splits.
6. **Defensible licensing:** free for academic/research use with citation.

### Exact prediction target

**Binary classification: `anemic` vs `non-anemic`**, where the dataset's own labels are defined by lab-measured hemoglobin < 11 g/dL (WHO threshold for children 6–59 months).

- The model predicts one of the two classes the dataset defines. It does **not** output severity levels (low/moderate/high) — the dataset does not provide those classes.
- The model does **not** emit a clinical diagnosis; the output is a **screening signal** for the PRAHARI multimodal engine (Swayam's component), and the confidence score accompanies it.

### Important limitations

- **Pediatric population (6–59 months, Ghana).** A model trained here should not be claimed to generalize to adults or other regions.
- **Capture device is a tablet, not a modern phone**, and images were taken in ambient natural light with the camera flash off. PRAHARI's eventual phone app should mimic these conditions.
- **Class imbalance:** 60% anemic / 40% non-anemic — use stratified splits and report precision/recall/F1, not just accuracy.
- **Single-eye, single-image-per-child structure must be verified** at download (see leakage below).
- Whether the shipped images are already ROI-cropped conjunctiva or full-eye images with separate ROIs must be verified at download; this affects the ROI stage design.
- No separate held-out test set is provided — we must reserve our own.

### Data leakage considerations

- **Subject-level splitting:** if any child has more than one image (e.g. left + right eye), all images of the same subject must stay in the same split. Verify at download; if 1 image/child, splits are naturally subject-level.
- **Stratified splits:** stratify by class, and ideally by collection site, so one hospital does not dominate a single fold.
- **No augmentation leakage:** all augmentation must be applied inside the training loop, never to validation/test images.
- **Model selection discipline:** if hyperparameters are tuned on a validation set, the final reported metrics must come from a held-out test set that was never touched during tuning (5-fold CV for development + one reserved test split, or strict nested CV).
- **Citation of prior work baselines is for reference only:** we will not report their numbers as our own.

---

## Hour 2 verification (actual downloaded data)

All numbers below are from the actual downloaded archive
(sha256 `78d7c2ec…d319c`, Mendeley) — verified 2026-08-17.

### Raw structure

- `data/raw/cp-anemic/` — `Anemia_Data_Collection_Sheet.xlsx` + `Anemic/`
  (424 PNG) + `Non-anemic/` (286 PNG) = **710 images, 710 metadata rows**.
- Images are **already ROI-cropped palpebral conjunctiva crops**: RGBA PNGs,
  451 unique sizes (e.g. 301×109, 430×225), all with an alpha channel.
- Metadata per row: IMAGE_ID, HB_LEVEL, Severity (Non-Anemic/Mild/Moderate/
  Severe), Age(Months), GENDER, REMARK (Anemic/Non-anemic), HOSPITAL,
  CITY/TOWN, MUNICIPALITY/DISTRICT, REGION, COUNTRY. No nulls.

### Validation results (`data/dataset_validation.json`)

- Total files: **710** — usable: **708** — rejected: **2**
- Rejected (recorded, not deleted): `Image_310` (anemic) and `Image_188`
  (non-anemic) — **byte-identical content with contradictory labels**
  (label_conflict).
- **Duplicates:** 91 content groups contain 303 files; 212 files are
  redundant byte-identical copies. Near-duplicates (perceptual aHash
  hamming ≤ 2) also exist: 630 pairs — see limitations.
- No corrupt files, no missing labels, no unknown labels.
- **85 duplicate groups carry mixed hospital metadata** for the same photo
  (metadata for duplicated images is not fully reliable).

### Label distribution (usable set, sheet REMARK = canonical)

| class | images |
| --- | --- |
| anemic | 423 |
| non_anemic | 285 |
| **total** | **708** |

Hb range 3.1–15.0 g/dL (mean 10.4). Severity exists as extra metadata
(Non-Anemic 286 / Moderate 232 / Mild 144 / Severe 48) but is **not** a
prediction target — the model predicts binary anemia status only.

### Leakage-safe split (`data/manifest.csv`, `data/dataset_summary.json`)

- **Split unit = md5 content group**, so byte-identical images can never
  span splits (verified: 0 groups cross splits). Subject (IMAGE_ID) is
  unique per image; content groups cover cross-ID duplication.
- Stratified by **(label, hospital)**; deterministic with `seed=42`.
- Group counts: train 348 / val 74 / test 75.
- Image counts: **train 498** (anemic 304, non-anemic 194), **val 97**
  (47/50), **test 113** (72/41). Class mix in each split ≈ overall 60/40.

### Preprocessing (as written into `data/processed/`)

RGBA → RGB over white → aspect-preserving resize + white pad to
**224×224** (no distortion of the thin conjunctiva strip). Color is kept.
ImageNet normalization is applied later in training transforms, never
baked into stored images. See `app/ai/preprocessing.py`.

### Augmentation

Training-time only (Hour 3): random horizontal flip (conjunctiva is
approximately left-right symmetric), small rotation, small shift/scale,
small brightness/contrast jitter. Validation/test stay deterministic.

### Updated limitations

- **Duplication is heavy:** 212 redundant copies (30% of files). Splitting
  by content group fixes leakage, but repeated content inflates effective
  sample size during training — monitor validation metrics for optimism.
  A deduplicated variant (1 image per content group) is an option.
- **1 cross-class label conflict** excluded (2 images).
- **Mixed hospital metadata on duplicated photos** — treat per-photo
  hospital fields as approximate for duplicates.
- Pediatric (6–59 months), Ghana only; tablet capture; prototype-level.
