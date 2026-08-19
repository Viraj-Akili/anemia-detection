"""Region-of-interest extraction: locate the palpebral conjunctiva in an eye image.

Hour 1: skeleton only. Approach depends on what the dataset ships at download
(DATASET.md / MODEL_PLAN.md):
  - If CP-AnemiC ships ROI-cropped conjunctiva images, ROI is a pass-through.
  - If it ships full-eye images, use the dataset's segmentation masks or a
    simple heuristic (red/pink tissue detection) as a first cut.
"""

# TODO(Hour 2+): implement extract_roi() based on verified dataset file structure.
