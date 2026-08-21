"""
scripts/build_metadata.py

STEP 1C — MASTER METADATA TABLE BUILDER
PRAHARI PPG / Hardware ML Pipeline

SAFETY NOTICE:
This script performs read-only parsing of raw CSV files.
It NEVER modifies raw dataset files.
Output is saved to data/metadata/recordings_metadata.csv.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd

REQUIRED_COLUMNS = [
    "Red (a.u)",
    "Infra Red (a.u)",
    "Gender",
    "Age",
    "Hemoglobin (g/dL)"
]


def extract_recording_metadata(file_path: Path, base_dir: Path) -> Dict[str, Any]:
    """
    Extract standardized recording metadata from a single raw PPG CSV file.
    """
    rel_path = file_path.relative_to(base_dir) if file_path.is_relative_to(base_dir) else file_path
    stem = file_path.stem

    # Inferred subject ID: "1.csv" -> 1
    if stem.isdigit():
        subject_id = int(stem)
        recording_id = f"sub_{subject_id:03d}_rec_01"
    else:
        # Fallback without making unreliable assumptions
        subject_id = stem
        recording_id = f"{stem}_rec_01"

    df = pd.read_csv(file_path)

    n_samples = len(df)
    # 2 PPG channels: Red and Infra Red
    n_channels = 2

    gender = str(df["Gender"].iloc[0]) if "Gender" in df.columns and len(df) > 0 else "UNKNOWN"
    age = int(df["Age"].iloc[0]) if "Age" in df.columns and len(df) > 0 else -1
    hb = float(df["Hemoglobin (g/dL)"].iloc[0]) if "Hemoglobin (g/dL)" in df.columns and len(df) > 0 else -1.0

    # Signal summaries for quick QA
    red_col = pd.to_numeric(df["Red (a.u)"], errors="coerce")
    ir_col = pd.to_numeric(df["Infra Red (a.u)"], errors="coerce")

    return {
        "subject_id": subject_id,
        "recording_id": recording_id,
        "source_file": str(rel_path).replace("\\", "/"),
        "n_samples": n_samples,
        "n_channels": n_channels,
        "gender": gender,
        "age": age,
        "hemoglobin_g_dl": round(hb, 2),
        "red_min": int(red_col.min()) if not red_col.isnull().all() else None,
        "red_max": int(red_col.max()) if not red_col.isnull().all() else None,
        "red_mean": round(float(red_col.mean()), 2) if not red_col.isnull().all() else None,
        "ir_min": int(ir_col.min()) if not ir_col.isnull().all() else None,
        "ir_max": int(ir_col.max()) if not ir_col.isnull().all() else None,
        "ir_mean": round(float(ir_col.mean()), 2) if not ir_col.isnull().all() else None,
        "sampling_rate_hz_verified": "UNVERIFIED",
        "duration_sec_verified": "UNVERIFIED"
    }


def build_metadata_dataframe(data_dir: Path) -> pd.DataFrame:
    """
    Scan raw data directory and build complete master metadata DataFrame.
    """
    csv_files = sorted(list(data_dir.rglob("*.csv")), key=lambda p: int(p.stem) if p.stem.isdigit() else p.name)
    if not csv_files:
        return pd.DataFrame()

    records = []
    for f in csv_files:
        try:
            meta = extract_recording_metadata(f, data_dir.parent.parent if "data" in data_dir.parts else data_dir)
            records.append(meta)
        except Exception as e:
            print(f"WARNING: Failed to extract metadata for {f.name}: {e}", file=sys.stderr)

    df_meta = pd.DataFrame(records)
    return df_meta


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate master metadata CSV from raw PPG recordings.")
    parser.add_argument(
        "--data-dir",
        type=str,
        default=os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw"),
        help="Path to raw data directory"
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default=os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "metadata", "recordings_metadata.csv"),
        help="Path to output metadata CSV"
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    out_path = Path(args.output_path)

    if not data_dir.exists():
        print(f"ERROR: Raw data directory not found: {data_dir}", file=sys.stderr)
        return 1

    out_path.parent.mkdir(parents=True, exist_ok=True)

    df_meta = build_metadata_dataframe(data_dir)
    if df_meta.empty:
        print("ERROR: No valid recording metadata generated.", file=sys.stderr)
        return 1

    df_meta.to_csv(out_path, index=False)
    print("=" * 80)
    print("PRAHARI PPG PIPELINE -- MASTER METADATA GENERATED (STEP 1C)")
    print("=" * 80)
    print(f"Saved Metadata Table to: {out_path}")
    print(f"Total Recordings Logged: {len(df_meta)}")
    print(f"Total Unique Subjects: {df_meta['subject_id'].nunique()}")
    print(f"Columns: {list(df_meta.columns)}")
    print("-" * 80)
    print("First 5 entries:")
    print(df_meta[["subject_id", "recording_id", "source_file", "n_samples", "gender", "age", "hemoglobin_g_dl"]].head(5).to_string(index=False))
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
