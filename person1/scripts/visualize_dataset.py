#!/usr/bin/env python
"""Visual sanity check for the prepared dataset.

Renders a grid of representative samples to data/samples/sanity_grid.png:
- raw ROI crops from both classes (train split)
- preprocessed 224x224 crops (same images)
- augmentation examples (train-time transforms, shown for verification only)

Purpose: visually confirm orientation, ROI sanity, that preprocessing
preserves the clinical signal, and that labels look correct.

Usage:
    python scripts/visualize_dataset.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.ai.preprocessing import preprocess_image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = PROJECT_ROOT / "data" / "manifest.csv"
OUT_PATH = PROJECT_ROOT / "data" / "samples" / "sanity_grid.png"
IMAGE_SIZE = 224
CELL = 112  # thumbnail cell size


def _augment_variants(arr: np.ndarray) -> list[np.ndarray]:
    """Small train-time-style augmentations (flip, rotation, brightness/contrast)."""
    from PIL import ImageEnhance

    img = Image.fromarray(arr, mode="RGB")
    variants = [
        img.transpose(Image.Transpose.FLIP_LEFT_RIGHT),
        img.rotate(5, resample=Image.Resampling.BILINEAR, fillcolor=(255, 255, 255)),
        ImageEnhance.Brightness(img).enhance(1.1),
        ImageEnhance.Contrast(img).enhance(1.1),
    ]
    return [np.asarray(v, dtype=np.uint8) for v in variants]


def main() -> int:
    if not MANIFEST_PATH.exists():
        print("data/manifest.csv missing — run scripts/prepare_dataset.py first.", file=sys.stderr)
        return 1

    manifest = pd.read_csv(MANIFEST_PATH)
    train = manifest[manifest.split == "train"]
    samples = train.groupby("label").head(4)  # 4 per class

    # 2 rows (raw + preprocessed) x 8 columns; plus an augmentation strip.
    cols = len(samples)
    rows = 3
    grid = Image.new("RGB", (cols * CELL, rows * CELL), (245, 245, 245))
    draw = ImageDraw.Draw(grid)
    for c, (_, row) in enumerate(samples.iterrows()):
        raw = Image.open(PROJECT_ROOT / row["raw_path"]).convert("RGB")
        raw.thumbnail((CELL, CELL), Image.Resampling.LANCZOS)
        grid.paste(raw, (c * CELL + (CELL - raw.width) // 2, (CELL - raw.height) // 2))

        pre = Image.fromarray(preprocess_image(PROJECT_ROOT / row["raw_path"], size=IMAGE_SIZE))
        pre.thumbnail((CELL, CELL), Image.Resampling.LANCZOS)
        grid.paste(pre, (c * CELL + (CELL - pre.width) // 2, CELL + (CELL - pre.height) // 2))

        aug = _augment_variants(preprocess_image(PROJECT_ROOT / row["raw_path"], size=IMAGE_SIZE))[0]
        a = Image.fromarray(aug)
        a.thumbnail((CELL, CELL), Image.Resampling.LANCZOS)
        grid.paste(a, (c * CELL + (CELL - a.width) // 2, 2 * CELL + (CELL - a.height) // 2))

        draw.text((c * CELL + 2, 2), f"{row['label'][:4]} {row['subject_id']}", fill=(0, 0, 0))

    draw.text((4, 0 * CELL + CELL - 14), "RAW", fill=(200, 0, 0))
    draw.text((4, 1 * CELL + CELL - 14), "PRE", fill=(0, 120, 0))
    draw.text((4, 2 * CELL + CELL - 14), "AUG", fill=(0, 0, 200))
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    grid.save(OUT_PATH)
    print(f"Wrote {OUT_PATH} ({cols} samples x 3 rows: raw / preprocessed / augmented)")
    print(f"Classes shown: {sorted(samples['label'].unique())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
