"""
scripts/validate_dataset.py

STEP 1B — DATASET VALIDATION
PRAHARI PPG / Hardware ML Pipeline

SAFETY NOTICE:
This script performs non-destructive validation.
It NEVER modifies or deletes raw records.
Results are written to reports/dataset_validation_report.txt and reports/dataset_summary.json.
"""

import os
import sys
import json
import hashlib
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple
import pandas as pd
import numpy as np

REQUIRED_COLUMNS = [
    "Red (a.u)",
    "Infra Red (a.u)",
    "Gender",
    "Age",
    "Hemoglobin (g/dL)"
]


def compute_signal_hash(red_series: pd.Series, ir_series: pd.Series) -> str:
    """Compute a SHA256 hash of the concatenated RED and IR signals."""
    byte_payload = (
        red_series.to_numpy().tobytes() +
        ir_series.to_numpy().tobytes()
    )
    return hashlib.sha256(byte_payload).hexdigest()


def validate_file(file_path: Path) -> Dict[str, Any]:
    """
    Perform deep validation on a single raw recording file.
    """
    res: Dict[str, Any] = {
        "file_name": file_path.name,
        "file_path": str(file_path),
        "is_valid": True,
        "critical_errors": [],
        "warnings": [],
        "n_rows": 0,
        "n_cols": 0,
        "missing_columns": [],
        "has_nan": False,
        "nan_counts": {},
        "has_inf": False,
        "red_is_numeric": False,
        "ir_is_numeric": False,
        "red_negative_count": 0,
        "ir_negative_count": 0,
        "red_min": None,
        "red_max": None,
        "red_mean": None,
        "ir_min": None,
        "ir_max": None,
        "ir_mean": None,
        "gender_uniform": True,
        "age_uniform": True,
        "hb_uniform": True,
        "gender_value": None,
        "age_value": None,
        "hb_value": None,
        "signal_hash": None,
    }

    if file_path.stat().st_size == 0:
        res["is_valid"] = False
        res["critical_errors"].append("File is 0 bytes.")
        return res

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        res["is_valid"] = False
        res["critical_errors"].append(f"CSV read error: {str(e)}")
        return res

    res["n_rows"] = len(df)
    res["n_cols"] = len(df.columns)

    # 1. Required Columns
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    res["missing_columns"] = missing
    if missing:
        res["is_valid"] = False
        res["critical_errors"].append(f"Missing required columns: {missing}")
        return res

    # 2. NaN / Null Check
    nan_counts = df[REQUIRED_COLUMNS].isnull().sum().to_dict()
    res["nan_counts"] = {k: int(v) for k, v in nan_counts.items() if v > 0}
    if any(v > 0 for v in nan_counts.values()):
        res["has_nan"] = True
        res["is_valid"] = False
        res["critical_errors"].append(f"NaN values found: {res['nan_counts']}")

    # 3. Numeric Types and Conversion
    try:
        red_num = pd.to_numeric(df["Red (a.u)"], errors="coerce")
        res["red_is_numeric"] = not red_num.isnull().any()
    except Exception:
        res["red_is_numeric"] = False

    try:
        ir_num = pd.to_numeric(df["Infra Red (a.u)"], errors="coerce")
        res["ir_is_numeric"] = not ir_num.isnull().any()
    except Exception:
        res["ir_is_numeric"] = False

    if not res["red_is_numeric"]:
        res["is_valid"] = False
        res["critical_errors"].append("Non-numeric values in 'Red (a.u)' column.")

    if not res["ir_is_numeric"]:
        res["is_valid"] = False
        res["critical_errors"].append("Non-numeric values in 'Infra Red (a.u)' column.")

    # 4. Infinite & Negative Values
    if res["red_is_numeric"] and res["ir_is_numeric"]:
        red_infs = int(np.isinf(red_num).sum())
        ir_infs = int(np.isinf(ir_num).sum())
        if red_infs > 0 or ir_infs > 0:
            res["has_inf"] = True
            res["is_valid"] = False
            res["critical_errors"].append(f"Infinite values found: Red={red_infs}, IR={ir_infs}")

        red_negs = int((red_num < 0).sum())
        ir_negs = int((ir_num < 0).sum())
        res["red_negative_count"] = red_negs
        res["ir_negative_count"] = ir_negs
        if red_negs > 0 or ir_negs > 0:
            res["warnings"].append(f"Negative signal counts found: Red={red_negs}, IR={ir_negs}")

        res["red_min"] = float(red_num.min())
        res["red_max"] = float(red_num.max())
        res["red_mean"] = float(red_num.mean())
        res["ir_min"] = float(ir_num.min())
        res["ir_max"] = float(ir_num.max())
        res["ir_mean"] = float(ir_num.mean())

        # Signal hash
        res["signal_hash"] = compute_signal_hash(red_num, ir_num)

    # 5. Metadata Uniformity within file
    g_unique = df["Gender"].dropna().unique()
    a_unique = df["Age"].dropna().unique()
    h_unique = df["Hemoglobin (g/dL)"].dropna().unique()

    if len(g_unique) > 1:
        res["is_valid"] = False
        res["gender_uniform"] = False
        res["critical_errors"].append(f"Inconsistent Gender in single file: {list(g_unique)}")
    elif len(g_unique) == 1:
        res["gender_value"] = str(g_unique[0])

    if len(a_unique) > 1:
        res["is_valid"] = False
        res["age_uniform"] = False
        res["critical_errors"].append(f"Inconsistent Age in single file: {list(a_unique)}")
    elif len(a_unique) == 1:
        res["age_value"] = int(a_unique[0])

    if len(h_unique) > 1:
        res["is_valid"] = False
        res["hb_uniform"] = False
        res["critical_errors"].append(f"Inconsistent Hemoglobin in single file: {list(h_unique)}")
    elif len(h_unique) == 1:
        res["hb_value"] = float(h_unique[0])

    if len(res["critical_errors"]) > 0:
        res["is_valid"] = False

    # 6. Sample Length Check
    if res["n_rows"] != 250:
        res["warnings"].append(f"Sample length is {res['n_rows']} (expected 250).")

    return res


def validate_dataset(data_dir: Path) -> Tuple[Dict[str, Any], str]:
    """
    Validate all CSV files under data_dir, checking individual files and cross-file relationships.
    """
    csv_files = sorted(list(data_dir.rglob("*.csv")))
    file_validations = [validate_file(f) for f in csv_files]

    total_files = len(file_validations)
    valid_files = [r for r in file_validations if r["is_valid"]]
    files_with_critical_errors = [r for r in file_validations if len(r["critical_errors"]) > 0]
    files_with_warnings = [r for r in file_validations if len(r["warnings"]) > 0]

    # Duplicate / Identical Signal Check
    hash_to_files: Dict[str, List[str]] = {}
    for r in file_validations:
        h = r["signal_hash"]
        if h:
            hash_to_files.setdefault(h, []).append(r["file_name"])

    exact_duplicate_groups = [files for files in hash_to_files.values() if len(files) > 1]

    # Length consistency
    lengths = [r["n_rows"] for r in file_validations]
    length_distribution: Dict[int, int] = {}
    for l in lengths:
        length_distribution[l] = length_distribution.get(l, 0) + 1

    all_same_length = len(set(lengths)) == 1 if lengths else False
    all_exact_250 = all(l == 250 for l in lengths) if lengths else False

    # Subject consistency check (by inferred subject ID from filename)
    subject_records: Dict[int, List[Dict[str, Any]]] = {}
    for r in file_validations:
        stem = Path(r["file_name"]).stem
        if stem.isdigit():
            s_id = int(stem)
            subject_records.setdefault(s_id, []).append(r)

    inconsistent_subjects = []
    for s_id, records in subject_records.items():
        if len(records) > 1:
            hbs = set(rec["hb_value"] for rec in records if rec["hb_value"] is not None)
            genders = set(rec["gender_value"] for rec in records if rec["gender_value"] is not None)
            ages = set(rec["age_value"] for rec in records if rec["age_value"] is not None)
            if len(hbs) > 1 or len(genders) > 1 or len(ages) > 1:
                inconsistent_subjects.append({
                    "subject_id": s_id,
                    "records_count": len(records),
                    "hb_values": list(hbs),
                    "genders": list(genders),
                    "ages": list(ages)
                })

    # Summary statistics for verified records
    all_hbs = [r["hb_value"] for r in valid_files if r["hb_value"] is not None]
    all_ages = [r["age_value"] for r in valid_files if r["age_value"] is not None]
    all_genders = [r["gender_value"] for r in valid_files if r["gender_value"] is not None]

    gender_counts = {}
    for g in all_genders:
        gender_counts[g] = gender_counts.get(g, 0) + 1

    summary_json: Dict[str, Any] = {
        "status": "PASSED" if len(files_with_critical_errors) == 0 else "FAILED",
        "dataset_directory": str(data_dir.resolve()),
        "total_files_analyzed": total_files,
        "valid_files_count": len(valid_files),
        "files_with_critical_errors_count": len(files_with_critical_errors),
        "files_with_warnings_count": len(files_with_warnings),
        "all_required_columns_present": all(len(r["missing_columns"]) == 0 for r in file_validations),
        "all_red_numeric": all(r["red_is_numeric"] for r in file_validations),
        "all_ir_numeric": all(r["ir_is_numeric"] for r in file_validations),
        "nan_values_detected": any(r["has_nan"] for r in file_validations),
        "infinite_values_detected": any(r["has_inf"] for r in file_validations),
        "negative_signals_detected": any(r["red_negative_count"] > 0 or r["ir_negative_count"] > 0 for r in file_validations),
        "internal_metadata_consistent": all(
            r["gender_uniform"] and r["age_uniform"] and r["hb_uniform"] for r in file_validations
        ),
        "all_recordings_same_length": all_same_length,
        "all_recordings_exactly_250_samples": all_exact_250,
        "sample_length_distribution": length_distribution,
        "duplicate_recording_groups_count": len(exact_duplicate_groups),
        "duplicate_recording_groups": exact_duplicate_groups,
        "cross_recording_subject_inconsistencies": inconsistent_subjects,
        "demographics": {
            "gender_breakdown": gender_counts,
            "age_min": int(min(all_ages)) if all_ages else None,
            "age_max": int(max(all_ages)) if all_ages else None,
            "age_mean": float(np.mean(all_ages)) if all_ages else None,
            "hb_min": float(min(all_hbs)) if all_hbs else None,
            "hb_max": float(max(all_hbs)) if all_hbs else None,
            "hb_mean": float(np.mean(all_hbs)) if all_hbs else None,
            "hb_std": float(np.std(all_hbs)) if all_hbs else None
        }
    }

    # Generate Human-Readable Text Report
    report_lines = [
        "=" * 80,
        "PRAHARI PPG PIPELINE -- DATASET VALIDATION REPORT (STEP 1B)",
        "=" * 80,
        f"Validation Status: {summary_json['status']}",
        f"Target Directory: {summary_json['dataset_directory']}",
        f"Total CSV Files Evaluated: {total_files}",
        f"Valid Files: {len(valid_files)} / {total_files}",
        f"Files with Critical Errors: {len(files_with_critical_errors)}",
        f"Files with Warnings: {len(files_with_warnings)}",
        "-" * 80,
        "CORE INTEGRITY CHECKS:",
        f"  [1] Required Columns Present (Red, IR, Gender, Age, Hb): {'PASS' if summary_json['all_required_columns_present'] else 'FAIL'}",
        f"  [2] Numeric Red Signal: {'PASS' if summary_json['all_red_numeric'] else 'FAIL'}",
        f"  [3] Numeric Infra Red Signal: {'PASS' if summary_json['all_ir_numeric'] else 'FAIL'}",
        f"  [4] NaN / Null Free: {'PASS' if not summary_json['nan_values_detected'] else 'FAIL'}",
        f"  [5] Infinity Free: {'PASS' if not summary_json['infinite_values_detected'] else 'FAIL'}",
        f"  [6] Negative Signal Free: {'PASS' if not summary_json['negative_signals_detected'] else 'FAIL'}",
        f"  [7] Internal File Metadata Uniformity: {'PASS' if summary_json['internal_metadata_consistent'] else 'FAIL'}",
        f"  [8] Exact Duplicate Signals: {len(exact_duplicate_groups)} duplicate pairs found",
        f"  [9] Subject Cross-Recording Metadata Consistency: {'PASS' if len(inconsistent_subjects) == 0 else 'FAIL'}",
        "-" * 80,
        "RECORDING LENGTH ANALYSIS:",
        f"  All recordings same length? {all_same_length}",
        f"  All recordings exactly 250 samples? {all_exact_250}",
        "  Observed Length Breakdown:"
    ]
    for length, cnt in sorted(length_distribution.items()):
        report_lines.append(f"    - {length} samples: {cnt} files")

    report_lines.extend([
        "-" * 80,
        "TARGET & DEMOGRAPHIC METRICS (Across Verified Subjects):",
        f"  - Subject Count: {len(valid_files)}",
        f"  - Gender Distribution: {gender_counts}",
        f"  - Age (years): Range = [{summary_json['demographics']['age_min']}, {summary_json['demographics']['age_max']}], Mean = {summary_json['demographics']['age_mean']:.2f}",
        f"  - Hemoglobin (g/dL): Range = [{summary_json['demographics']['hb_min']:.2f}, {summary_json['demographics']['hb_max']:.2f}], Mean = {summary_json['demographics']['hb_mean']:.2f} +/- {summary_json['demographics']['hb_std']:.2f}",
        "=" * 80,
    ])

    if files_with_critical_errors:
        report_lines.append("CRITICAL ERRORS DETAILS:")
        for r in files_with_critical_errors:
            report_lines.append(f"  * {r['file_name']}: {r['critical_errors']}")
        report_lines.append("=" * 80)

    if files_with_warnings:
        report_lines.append("WARNINGS DETAILS (NON-BLOCKING):")
        for r in files_with_warnings[:10]:
            report_lines.append(f"  * {r['file_name']}: {r['warnings']}")
        if len(files_with_warnings) > 10:
            report_lines.append(f"  ... and {len(files_with_warnings) - 10} more files with warnings (e.g. 249 vs 250 length).")
        report_lines.append("=" * 80)

    text_report = "\n".join(report_lines)
    return summary_json, text_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate raw PPG dataset and generate validation reports.")
    parser.add_argument(
        "--data-dir",
        type=str,
        default=os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw"),
        help="Path to raw data directory"
    )
    parser.add_argument(
        "--reports-dir",
        type=str,
        default=os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports"),
        help="Path to output reports directory"
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    reports_dir = Path(args.reports_dir)

    if not data_dir.exists():
        print(f"ERROR: Raw data directory not found: {data_dir}", file=sys.stderr)
        return 1

    reports_dir.mkdir(parents=True, exist_ok=True)

    summary_json, text_report = validate_dataset(data_dir)

    # Write text report
    txt_path = reports_dir / "dataset_validation_report.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text_report)
    print(f"Saved text report to: {txt_path}")

    # Write JSON summary
    json_path = reports_dir / "dataset_summary.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary_json, f, indent=2)
    print(f"Saved machine-readable summary to: {json_path}")

    # Print to stdout
    print("\n" + text_report)

    return 0 if summary_json["status"] == "PASSED" else 1


if __name__ == "__main__":
    sys.exit(main())
