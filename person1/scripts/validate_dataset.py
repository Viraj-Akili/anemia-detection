#!/usr/bin/env python
"""Validate the CP-AnemiC raw dataset.

Checks every image: existence, openability, format, dimensions, channels,
label presence/validity, duplicates (byte-identical content), quality
metrics and tissue coverage. Writes:

- data/dataset_validation.csv   (per-file rows: status, reasons, metrics)
- data/dataset_validation.json  (aggregate summary)

Rejected samples are RECORDED, never deleted. The raw dataset is immutable.

Usage:
    python scripts/validate_dataset.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.data_pipeline import RawLayout, validate_dataset, validation_summary, save_json

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "cp-anemic"
VALIDATION_CSV = PROJECT_ROOT / "data" / "dataset_validation.csv"
VALIDATION_JSON = PROJECT_ROOT / "data" / "dataset_validation.json"


def main() -> int:
    if not (RAW_DIR / "Anemia_Data_Collection_Sheet.xlsx").exists():
        print(f"Raw dataset not found at {RAW_DIR}. Run scripts/download_dataset.py first.", file=sys.stderr)
        return 1

    records, meta = validate_dataset(RAW_DIR)
    summary = validation_summary(records)

    rows = [
        {
            "image_id": r.image_id,
            "image_path": r.image_path,
            "label": r.label,
            "status": r.status,
            "reasons": "; ".join(r.reasons),
            "width": r.width,
            "height": r.height,
            "channels": r.channels,
            "size_bytes": r.size_bytes,
            "md5": r.md5,
            "content_group": r.content_group,
            "brightness": round(r.brightness, 2) if r.brightness is not None else None,
            "contrast": round(r.contrast, 2) if r.contrast is not None else None,
            "sharpness": round(r.sharpness, 2) if r.sharpness is not None else None,
            "tissue_fraction": round(r.tissue_fraction, 3) if r.tissue_fraction is not None else None,
        }
        for r in records
    ]
    df = pd.DataFrame(rows).sort_values("image_id")
    df.to_csv(VALIDATION_CSV, index=False)

    dims = df[df.status == "ok"].groupby(["width", "height"]).size().reset_index(name="count")
    summary["image_dimensions"] = {
        "unique": int(dims.shape[0]),
        "most_common": [
            {"width": int(w), "height": int(h), "count": int(c)}
            for w, h, c in dims.sort_values("count", ascending=False).head(10).itertuples(index=False)
        ],
    }
    summary["channels"] = df[df.status == "ok"]["channels"].value_counts().to_dict()
    summary["class_counts"] = df[df.status == "ok"]["label"].value_counts().to_dict()
    summary["raw_root"] = str(RAW_DIR)

    save_json(VALIDATION_JSON, summary)

    print("Dataset validation report")
    print("=" * 60)
    for k, v in summary.items():
        if k in ("rejected", "image_dimensions"):
            continue
        print(f"  {k}: {v}")
    print(f"  rejected: {len(summary['rejected'])} samples (see {VALIDATION_CSV.name})")
    print(f"  dimensions: {summary['image_dimensions']['unique']} unique sizes")
    print(f"Wrote {VALIDATION_CSV} and {VALIDATION_JSON}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
