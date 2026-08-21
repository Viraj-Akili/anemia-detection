"""
scripts/inspect_dataset.py

STEP 1A — DATASET DISCOVERY & INSPECTION
PRAHARI PPG / Hardware ML Pipeline

SAFETY NOTICE:
This script performs read-only inspection.
It NEVER modifies or overwrites raw dataset files.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd

EXPECTED_COLUMNS = [
    "Red (a.u)",
    "Infra Red (a.u)",
    "Gender",
    "Age",
    "Hemoglobin (g/dL)"
]


def find_csv_files(data_dir: Path) -> List[Path]:
    """Recursively find all CSV files under the given directory."""
    if not data_dir.exists():
        return []
    return sorted(list(data_dir.rglob("*.csv")))


def inspect_single_file(file_path: Path, base_dir: Path) -> Dict[str, Any]:
    """
    Inspect an individual CSV file and extract structural properties and metadata.
    """
    rel_path = file_path.relative_to(base_dir) if file_path.is_relative_to(base_dir) else file_path
    result = {
        "filename": file_path.name,
        "relative_path": str(rel_path),
        "absolute_path": str(file_path.resolve()),
        "is_empty": False,
        "is_malformed": False,
        "error_message": None,
        "n_rows": 0,
        "n_cols": 0,
        "columns": [],
        "missing_columns": [],
        "extra_columns": [],
        "has_expected_columns": False,
        "has_250_samples": False,
        "gender": None,
        "age": None,
        "hemoglobin": None,
        "inferred_subject_id": None,
    }

    # Check for empty file (0 bytes)
    if file_path.stat().st_size == 0:
        result["is_empty"] = True
        result["error_message"] = "File is 0 bytes (empty)"
        return result

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        result["is_malformed"] = True
        result["error_message"] = f"Failed to parse CSV: {str(e)}"
        return result

    if df.empty and len(df.columns) == 0:
        result["is_empty"] = True
        result["error_message"] = "DataFrame is empty with no columns"
        return result

    result["n_rows"] = len(df)
    result["n_cols"] = len(df.columns)
    result["columns"] = list(df.columns)

    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    extra = [c for c in df.columns if c not in EXPECTED_COLUMNS]
    result["missing_columns"] = missing
    result["extra_columns"] = extra
    result["has_expected_columns"] = (len(missing) == 0)
    result["has_250_samples"] = (len(df) == 250)

    # Inferred subject ID from filename (e.g., "1.csv" -> 1)
    stem = file_path.stem
    if stem.isdigit():
        result["inferred_subject_id"] = int(stem)
    else:
        # Check if contains pattern like subject_1 or sub-01
        cleaned = stem.lower().replace("subject", "").replace("sub", "").replace("_", "").replace("-", "")
        if cleaned.isdigit():
            result["inferred_subject_id"] = int(cleaned)

    # Extract demographic & target values if columns exist and rows > 0
    if len(df) > 0:
        if "Gender" in df.columns:
            g_unique = df["Gender"].dropna().unique()
            result["gender"] = list(g_unique)
        if "Age" in df.columns:
            a_unique = df["Age"].dropna().unique()
            result["age"] = list(a_unique)
        if "Hemoglobin (g/dL)" in df.columns:
            h_unique = df["Hemoglobin (g/dL)"].dropna().unique()
            result["hemoglobin"] = list(h_unique)

    return result


def inspect_dataset(data_dir: Path) -> Dict[str, Any]:
    """
    Run full dataset discovery across all CSV files in data_dir.
    """
    csv_files = find_csv_files(data_dir)
    file_results = [inspect_single_file(f, data_dir) for f in csv_files]

    total_files = len(file_results)
    empty_files = [r for r in file_results if r["is_empty"]]
    malformed_files = [r for r in file_results if r["is_malformed"]]
    valid_files = [r for r in file_results if not r["is_empty"] and not r["is_malformed"]]

    # Duplicate filename check
    filename_counts: Dict[str, int] = {}
    for r in file_results:
        filename_counts[r["filename"]] = filename_counts.get(r["filename"], 0) + 1
    duplicate_filenames = [fname for fname, count in filename_counts.items() if count > 1]

    # Column consistency
    files_with_missing_cols = [r for r in valid_files if not r["has_expected_columns"]]

    # Sample counts
    row_counts = [r["n_rows"] for r in valid_files]
    all_have_250_samples = (len(row_counts) > 0 and all(c == 250 for c in row_counts))
    sample_count_distribution: Dict[int, int] = {}
    for c in row_counts:
        sample_count_distribution[c] = sample_count_distribution.get(c, 0) + 1

    # Demographics and Target distributions
    unique_genders = set()
    all_ages = []
    all_hbs = []
    inferred_subject_ids = set()

    for r in valid_files:
        if r["gender"]:
            unique_genders.update(r["gender"])
        if r["age"]:
            all_ages.extend(r["age"])
        if r["hemoglobin"]:
            all_hbs.extend(r["hemoglobin"])
        if r["inferred_subject_id"] is not None:
            inferred_subject_ids.add(r["inferred_subject_id"])

    age_range = (min(all_ages), max(all_ages)) if all_ages else None
    hb_range = (min(all_hbs), max(all_hbs)) if all_hbs else None

    # Can subject IDs be reliably inferred?
    subject_ids_reliable = (
        len(inferred_subject_ids) == len(valid_files) and
        len(inferred_subject_ids) > 0
    )

    summary = {
        "data_dir": str(data_dir.resolve()),
        "total_files": total_files,
        "empty_files_count": len(empty_files),
        "empty_files": [r["relative_path"] for r in empty_files],
        "malformed_files_count": len(malformed_files),
        "malformed_files": [r["relative_path"] for r in malformed_files],
        "duplicate_filenames": duplicate_filenames,
        "expected_columns": EXPECTED_COLUMNS,
        "files_with_missing_columns": [
            {"file": r["relative_path"], "missing": r["missing_columns"]}
            for r in files_with_missing_cols
        ],
        "all_have_250_samples": all_have_250_samples,
        "sample_count_distribution": sample_count_distribution,
        "unique_genders": sorted(list(unique_genders)),
        "age_range": age_range,
        "hb_range": hb_range,
        "subject_ids_reliable": subject_ids_reliable,
        "unique_subject_ids_count": len(inferred_subject_ids),
        "unique_subject_ids": sorted(list(inferred_subject_ids)),
        "file_details": file_results,
    }
    return summary


def print_inspection_report(summary: Dict[str, Any]) -> None:
    """Print formatted inspection report to stdout."""
    print("=" * 80)
    print("PRAHARI PPG PIPELINE -- STEP 1A DATASET DISCOVERY REPORT")
    print("=" * 80)
    print(f"Directory Inspected: {summary['data_dir']}")
    print(f"Total CSV Files Found: {summary['total_files']}")
    print(f"Empty Files: {summary['empty_files_count']}")
    print(f"Malformed Files: {summary['malformed_files_count']}")
    print(f"Duplicate Filenames: {len(summary['duplicate_filenames'])}")
    if summary['duplicate_filenames']:
        print(f"  Duplicates: {summary['duplicate_filenames']}")
    print("-" * 80)

    print("SCHEMA & COLUMN VERIFICATION:")
    print(f"Expected Columns ({len(summary['expected_columns'])}): {summary['expected_columns']}")
    if summary["files_with_missing_columns"]:
        print(f"WARNING: {len(summary['files_with_missing_columns'])} files missing expected columns!")
        for item in summary["files_with_missing_columns"][:5]:
            print(f"  {item['file']}: missing {item['missing']}")
    else:
        print("  [SUCCESS] All files contain all 5 required columns.")
    print("-" * 80)

    print("SAMPLE LENGTH ANALYSIS:")
    print(f"All files have exactly 250 samples? {summary['all_have_250_samples']}")
    print("Sample Count Distribution:")
    for count, n_files in sorted(summary["sample_count_distribution"].items()):
        print(f"  {count} samples: {n_files} files")
    print("-" * 80)

    print("METADATA & TARGET DISTRIBUTIONS:")
    print(f"Unique Genders: {summary['unique_genders']}")
    if summary["age_range"]:
        print(f"Age Range: {summary['age_range'][0]} to {summary['age_range'][1]} years")
    else:
        print("Age Range: N/A")
    if summary["hb_range"]:
        print(f"Hemoglobin Range: {summary['hb_range'][0]:.2f} to {summary['hb_range'][1]:.2f} g/dL")
    else:
        print("Hemoglobin Range: N/A")
    print("-" * 80)

    print("SUBJECT IDENTIFIER INFERENCE:")
    print(f"Subject IDs reliably inferable from filenames? {summary['subject_ids_reliable']}")
    print(f"Unique Subject IDs found: {summary['unique_subject_ids_count']}")
    if summary["unique_subject_ids"]:
        ids_preview = summary["unique_subject_ids"][:10]
        print(f"Subject IDs (preview): {ids_preview} ... (total: {len(summary['unique_subject_ids'])})")
    print("=" * 80)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect raw PPG dataset files under data/raw/.")
    parser.add_argument(
        "--data-dir",
        type=str,
        default=os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw"),
        help="Path to raw data directory"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed table of every file"
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        print(f"ERROR: Target directory does not exist: {data_dir}", file=sys.stderr)
        return 1

    summary = inspect_dataset(data_dir)
    print_inspection_report(summary)

    if args.verbose and summary["file_details"]:
        print("\nDETAILED PER-FILE BREAKDOWN:")
        print(f"{'Filename':<12} | {'Rows':<6} | {'Cols':<6} | {'Gender':<8} | {'Age':<5} | {'Hb (g/dL)':<10} | {'Expected Cols?'}")
        print("-" * 75)
        for r in summary["file_details"]:
            g = str(r["gender"][0]) if r["gender"] else "N/A"
            a = str(r["age"][0]) if r["age"] else "N/A"
            h = f"{r['hemoglobin'][0]:.1f}" if r["hemoglobin"] else "N/A"
            print(f"{r['filename']:<12} | {r['n_rows']:<6} | {r['n_cols']:<6} | {g:<8} | {a:<5} | {h:<10} | {r['has_expected_columns']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
