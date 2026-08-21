"""
scripts/preprocess_dataset.py

STEP 2F — DATASET PREPROCESSING AUTOMATION
PRAHARI PPG / Hardware ML Pipeline

SAFETY NOTICE:
This script performs read-only processing of data/raw/.
It NEVER modifies or overwrites raw dataset files.
All processed outputs are saved to data/processed/.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd
import numpy as np

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ppg.preprocessing import preprocess_ppg


def preprocess_all_recordings(
    raw_dir: Path,
    metadata_path: Path,
    output_dir: Path,
    fs: float = 25.0
) -> Dict[str, Any]:
    """
    Load all raw recordings, execute preprocessing and quality checks,
    and save structured outputs into data/processed/.
    """
    subjects_out_dir = output_dir / "subjects"
    subjects_out_dir.mkdir(parents=True, exist_ok=True)

    csv_files = sorted(
        list(raw_dir.rglob("*.csv")),
        key=lambda p: int(p.stem) if p.stem.isdigit() else p.name
    )

    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {raw_dir}")

    consolidated_rows: List[Dict[str, Any]] = []
    quality_summaries: List[Dict[str, Any]] = []

    status_counts = {"GOOD": 0, "WARNING": 0, "REJECT": 0}

    for f in csv_files:
        stem = f.stem
        subject_id = int(stem) if stem.isdigit() else stem
        recording_id = f"sub_{subject_id:03d}_rec_01" if isinstance(subject_id, int) else f"{subject_id}_rec_01"

        df_raw = pd.read_csv(f)
        gender = str(df_raw["Gender"].iloc[0]) if "Gender" in df_raw.columns else "UNKNOWN"
        age = int(df_raw["Age"].iloc[0]) if "Age" in df_raw.columns else -1
        hb = float(df_raw["Hemoglobin (g/dL)"].iloc[0]) if "Hemoglobin (g/dL)" in df_raw.columns else -1.0

        clean_red, clean_ir, quality = preprocess_ppg(
            df_raw["Red (a.u)"],
            df_raw["Infra Red (a.u)"],
            fs=fs
        )

        status = quality["status"]
        status_counts[status] = status_counts.get(status, 0) + 1

        # Build per-sample rows
        n_pts = len(clean_red)
        time_sec = np.arange(n_pts) / fs

        df_subject_processed = pd.DataFrame({
            "sample_index": np.arange(n_pts),
            "time_sec": np.round(time_sec, 4),
            "raw_red": df_raw["Red (a.u)"].to_numpy()[:n_pts],
            "raw_ir": df_raw["Infra Red (a.u)"].to_numpy()[:n_pts],
            "clean_red": np.round(clean_red, 6),
            "clean_ir": np.round(clean_ir, 6),
            "gender": gender,
            "age": age,
            "hemoglobin_g_dl": hb,
            "quality_status": status
        })

        # Save individual subject file
        sub_file_path = subjects_out_dir / f"{subject_id}_processed.csv"
        df_subject_processed.to_csv(sub_file_path, index=False)

        # Accumulate for consolidated dataset
        for _, row in df_subject_processed.iterrows():
            row_dict = row.to_dict()
            row_dict["subject_id"] = subject_id
            row_dict["recording_id"] = recording_id
            row_dict["source_file"] = f"data/raw/{f.name}"
            consolidated_rows.append(row_dict)

        # Accumulate quality summary
        quality_summaries.append({
            "subject_id": subject_id,
            "recording_id": recording_id,
            "source_file": f"data/raw/{f.name}",
            "n_samples": n_pts,
            "duration_sec": round(n_pts / fs, 2),
            "gender": gender,
            "age": age,
            "hemoglobin_g_dl": hb,
            "quality_status": status,
            "is_usable": quality["is_usable"],
            "red_cardiac_sqi": quality["metrics"]["red_cardiac_sqi"],
            "ir_cardiac_sqi": quality["metrics"]["ir_cardiac_sqi"],
            "mean_cardiac_sqi": quality["metrics"]["mean_cardiac_sqi"],
            "red_ir_cross_correlation": quality["metrics"]["red_ir_cross_correlation"],
            "warnings": "; ".join(quality["warnings"]) if quality["warnings"] else "None",
            "rejection_reasons": "; ".join(quality["reasons"]) if quality["reasons"] else "None"
        })

    # Save consolidated dataset
    df_consolidated = pd.DataFrame(consolidated_rows)
    # Order columns cleanly
    cols_order = [
        "subject_id", "recording_id", "source_file", "sample_index", "time_sec",
        "raw_red", "raw_ir", "clean_red", "clean_ir",
        "gender", "age", "hemoglobin_g_dl", "quality_status"
    ]
    df_consolidated = df_consolidated[cols_order]
    consolidated_path = output_dir / "processed_recordings.csv"
    df_consolidated.to_csv(consolidated_path, index=False)

    # Save quality summary
    df_quality = pd.DataFrame(quality_summaries)
    quality_summary_path = output_dir / "preprocessing_quality_summary.csv"
    df_quality.to_csv(quality_summary_path, index=False)

    return {
        "total_recordings_processed": len(csv_files),
        "status_counts": status_counts,
        "consolidated_output_path": str(consolidated_path),
        "quality_summary_path": str(quality_summary_path),
        "subjects_output_directory": str(subjects_out_dir),
        "sample_length_breakdown": df_quality["n_samples"].value_counts().to_dict(),
        "mean_sqi_overall": float(df_quality["mean_cardiac_sqi"].mean()),
        "mean_red_ir_corr": float(df_quality["red_ir_cross_correlation"].mean())
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Preprocess raw PPG dataset files.")
    parser.add_argument(
        "--raw-dir",
        type=str,
        default=os.path.join(PROJECT_ROOT, "data", "raw"),
        help="Path to raw data directory"
    )
    parser.add_argument(
        "--metadata-path",
        type=str,
        default=os.path.join(PROJECT_ROOT, "data", "metadata", "recordings_metadata.csv"),
        help="Path to recordings_metadata.csv"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=os.path.join(PROJECT_ROOT, "data", "processed"),
        help="Path to output processed directory"
    )
    parser.add_argument(
        "--fs",
        type=float,
        default=25.0,
        help="Verified sampling rate in Hz (default: 25.0)"
    )
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    metadata_path = Path(args.metadata_path)
    output_dir = Path(args.output_dir)

    if not raw_dir.exists():
        print(f"ERROR: Raw data directory not found: {raw_dir}", file=sys.stderr)
        return 1

    print("=" * 80)
    print("PRAHARI PPG PIPELINE -- PREPROCESSING DATASET (STEP 2F)")
    print("=" * 80)
    print(f"Raw Data Directory: {raw_dir}")
    print(f"Output Directory:   {output_dir}")
    print(f"Sampling Rate:      {args.fs} Hz (Verified)")
    print("-" * 80)

    summary = preprocess_all_recordings(raw_dir, metadata_path, output_dir, fs=args.fs)

    print(f"Total Recordings Processed: {summary['total_recordings_processed']}")
    print("Signal Quality Classification:")
    for status, count in summary["status_counts"].items():
        pct = (count / summary["total_recordings_processed"]) * 100
        print(f"  * {status:<8}: {count:>2} recordings ({pct:5.1f}%)")
    print("-" * 80)
    print(f"Overall Mean Cardiac SQI:           {summary['mean_sqi_overall']:.3f}")
    print(f"Overall Mean Red-IR Correlation:   {summary['mean_red_ir_corr']:.3f}")
    print(f"Sample Counts Breakdown:            {summary['sample_length_breakdown']}")
    print("-" * 80)
    print(f"Saved Consolidated Dataset: {summary['consolidated_output_path']}")
    print(f"Saved Quality Summary:     {summary['quality_summary_path']}")
    print(f"Saved Per-Subject Files:   {summary['subjects_output_directory']}")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
