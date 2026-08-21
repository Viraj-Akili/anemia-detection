#!/usr/bin/env python
"""Build the processed, leakage-safe CP-AnemiC dataset.

Flow: validate -> group by content hash (duplicates never span splits) ->
deterministic stratified split (70/15/15 by label + hospital, fixed seed) ->
write preprocessed RGB crops into data/processed/{train,val,test}/{class}/ ->
write data/manifest.csv and data/dataset_summary.json.

Preprocessing (see app/ai/preprocessing.py): RGBA -> RGB over white,
aspect-preserving resize + white pad to IMAGE_SIZE (default 224).

Usage:
    python scripts/prepare_dataset.py [--image-size 224] [--seed 42] [--overwrite]
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import pandas as pd
from PIL import Image

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.ai.preprocessing import preprocess_image
from app.data_pipeline import (
    CLASS_NAMES,
    RawLayout,
    build_group_table,
    check_no_leakage,
    label_to_id,
    save_json,
    split_groups,
    validate_dataset,
    validation_summary,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "cp-anemic"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MANIFEST_PATH = PROJECT_ROOT / "data" / "manifest.csv"
SUMMARY_PATH = PROJECT_ROOT / "data" / "dataset_summary.json"
DEFAULT_SEED = 42
DEFAULT_IMAGE_SIZE = 224


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare the processed CP-AnemiC dataset.")
    parser.add_argument("--image-size", type=int, default=DEFAULT_IMAGE_SIZE)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--overwrite", action="store_true", help="rebuild processed dir even if present")
    args = parser.parse_args()

    if not (RAW_DIR / "Anemia_Data_Collection_Sheet.xlsx").exists():
        print(f"Raw dataset not found at {RAW_DIR}. Run scripts/download_dataset.py first.", file=sys.stderr)
        return 1

    print("[prepare] validating raw dataset ...")
    records, meta = validate_dataset(RAW_DIR)
    summary = validation_summary(records)
    usable = [r for r in records if r.status == "ok"]
    print(f"[prepare] {len(usable)} usable images (rejected: {len(records) - len(usable)})")

    print("[prepare] building content groups and leakage-safe split ...")
    groups = build_group_table(usable, meta)
    groups = split_groups(groups, seed=args.seed)
    check_no_leakage(groups)

    split_counts = groups["split"].value_counts()
    print(f"[prepare] group-level split: {dict(split_counts)} (seed={args.seed})")

    # Map each image to its split via its content group.
    split_by_group = dict(zip(groups["content_group"], groups["split"]))
    rec_by_id = {r.image_id: r for r in usable}
    meta_by_id = {r["IMAGE_ID"]: r for _, r in meta.iterrows()}

    rows = []
    n_written = 0
    for rec in usable:
        split = split_by_group.get(rec.content_group)
        if split is None:
            raise RuntimeError(f"no split assigned for {rec.image_id}")
        label = rec.label
        out_dir = PROCESSED_DIR / split / label
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{rec.image_id}.png"
        if args.overwrite or not out_path.exists():
            arr = preprocess_image(rec.image_path, size=args.image_size)
            Image.fromarray(arr, mode="RGB").save(out_path)
            n_written += 1

        row = meta_by_id[rec.image_id]
        rows.append(
            {
                "image_path": str(out_path.relative_to(PROJECT_ROOT)),
                "raw_path": rec.image_path,
                "split": split,
                "label": label,
                "label_id": label_to_id(label),
                "subject_id": rec.image_id,
                "content_group": rec.content_group,
                "width": rec.width,
                "height": rec.height,
                "channels": rec.channels,
                "hb_level": float(row["HB_LEVEL"]),
                "severity": str(row["Severity"]),
                "age_months": int(row["Age(Months)"]),
                "gender": str(row["GENDER"]),
                "hospital": str(row["HOSPITAL"]),
                "region": str(row["REGION"]),
            }
        )

    manifest = pd.DataFrame(rows).sort_values(["split", "label", "subject_id"])
    manifest.to_csv(MANIFEST_PATH, index=False)

    # Class distribution per split
    class_dist = {
        split: {
            cls: int(manifest[(manifest.split == split) & (manifest.label == cls)].shape[0])
            for cls in CLASS_NAMES
        }
        for split in ["train", "val", "test"]
    }

    group_hospital_mixed = int(groups["hospital_mixed"].sum())
    summary.update(
        {
            "seed": args.seed,
            "image_size": args.image_size,
            "split_ratios": {"train": 0.70, "val": 0.15, "test": 0.15},
            "split_strategy": (
                "content-group-level stratified split by (label, hospital); "
                "byte-identical images never span splits"
            ),
            "leakage_prevention": [
                "split unit = md5 content group (identical images stay together)",
                "subject (IMAGE_ID) is unique per image; content groups cover cross-ID duplication",
                "stratification by label and hospital",
                "fixed seed for reproducibility",
            ],
            "class_distribution": class_dist,
            "total_samples": int(len(manifest)),
            "train_samples": int(sum(class_dist["train"].values())),
            "validation_samples": int(sum(class_dist["val"].values())),
            "test_samples": int(sum(class_dist["test"].values())),
            "image_channels": "RGB (alpha composited over white)",
            "preprocessing": [
                "RGBA -> RGB over white background",
                f"aspect-preserving resize + white pad to {args.image_size}x{args.image_size}",
                "no normalization baked in (ImageNet normalize applied in training transforms)",
            ],
            "augmentation": "applied at training time only (Hour 3); validation/test stay deterministic",
            "quality_notes": "quality metrics recorded in data/dataset_validation.csv; only corrupt/label-conflict samples excluded",
            "groups_with_mixed_hospital": group_hospital_mixed,
        }
    )
    save_json(SUMMARY_PATH, summary)

    print("\nClass distribution per split (images):")
    for split in ["train", "val", "test"]:
        print(f"  {split:5s}: " + ", ".join(f"{cls}={n}" for cls, n in class_dist[split].items()))
    print(f"\nWrote {n_written} preprocessed images to {PROCESSED_DIR}")
    print(f"Wrote {MANIFEST_PATH} ({len(manifest)} rows) and {SUMMARY_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
