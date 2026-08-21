"""
scripts/extract_features.py

STEP 3F — FEATURE EXTRACTION & QUALITY AUDIT AUTOMATION
PRAHARI PPG / Hardware ML Pipeline

SAFETY NOTICE:
Performs read-only extraction from data/raw/ or data/processed/.
Saves feature table to data/processed/ppg_features.csv,
feature dictionary to data/metadata/feature_summary.csv,
and audit report to reports/feature_audit.md.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple
import pandas as pd
import numpy as np

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ppg.features import extract_features_from_recording

# Categorization mapping for documentation and audit
def categorize_feature(col_name: str) -> str:
    if col_name in ["subject_id", "recording_id", "source_file", "gender"]:
        return "Metadata"
    elif col_name == "hemoglobin_g_dl":
        return "Target"
    elif col_name in ["age", "gender_encoded"]:
        return "Demographic"
    elif any(col_name.startswith(p) for p in ["red_fft_", "ir_fft_"]):
        return "Frequency-Domain (FFT)"
    elif any(k in col_name for k in ["_n_pulses", "_pulse_rate_", "_pulse_amplitude_", "_pulse_interval_"]):
        return "Pulse Morphology"
    elif any(k in col_name for k in ["red_ir_", "_ac_dc", "ratio_of_ratios", "clean_red_ir_", "red_raw_", "ir_raw_"]):
        return "Cross-Channel & Optical Ratios"
    elif col_name.startswith("red_") or col_name.startswith("ir_"):
        return "Time-Domain Statistics"
    else:
        return "Other"


def audit_features(df_features: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any], str]:
    """
    Perform deep statistical quality audit on the extracted features.
    """
    # Exclude metadata and target from ML feature matrix
    meta_cols = ["subject_id", "recording_id", "source_file", "gender", "hemoglobin_g_dl"]
    feature_cols = [c for c in df_features.columns if c not in meta_cols]

    summary_records = []
    constant_features = []
    low_variance_features = []
    nan_features = []
    inf_features = []

    for col in feature_cols:
        series = df_features[col]
        n_nan = int(series.isna().sum())
        n_inf = int(np.isinf(series).sum()) if pd.api.types.is_numeric_dtype(series) else 0
        cat = categorize_feature(col)

        if pd.api.types.is_numeric_dtype(series):
            mean_val = float(series.mean())
            std_val = float(series.std())
            min_val = float(series.min())
            max_val = float(series.max())
            is_const = bool(std_val < 1e-8)
            is_low_var = bool(0 < std_val < 1e-4)
        else:
            mean_val, std_val, min_val, max_val = np.nan, np.nan, np.nan, np.nan
            is_const = bool(series.nunique() <= 1)
            is_low_var = False

        if is_const:
            constant_features.append(col)
        if is_low_var:
            low_variance_features.append(col)
        if n_nan > 0:
            nan_features.append((col, n_nan))
        if n_inf > 0:
            inf_features.append((col, n_inf))

        summary_records.append({
            "feature_name": col,
            "category": cat,
            "mean": round(mean_val, 4) if not np.isnan(mean_val) else None,
            "std": round(std_val, 4) if not np.isnan(std_val) else None,
            "min": round(min_val, 4) if not np.isnan(min_val) else None,
            "max": round(max_val, 4) if not np.isnan(max_val) else None,
            "missing_count": n_nan,
            "is_constant": is_const
        })

    df_summary = pd.DataFrame(summary_records)

    # Collinearity check (pairwise correlation > 0.98)
    numeric_df = df_features[feature_cols].select_dtypes(include=[np.number])
    corr_matrix = numeric_df.corr().abs()
    upper_tri = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    highly_correlated_pairs = []
    for col1 in upper_tri.columns:
        for col2 in upper_tri.index:
            val = upper_tri.loc[col2, col1]
            if not np.isnan(val) and val > 0.98:
                highly_correlated_pairs.append((col2, col1, round(float(val), 4)))

    audit_stats = {
        "total_recordings": len(df_features),
        "total_features": len(feature_cols),
        "feature_categories": df_summary["category"].value_counts().to_dict(),
        "constant_features": constant_features,
        "low_variance_features": low_variance_features,
        "nan_features": nan_features,
        "inf_features": inf_features,
        "highly_correlated_pairs_count": len(highly_correlated_pairs),
        "highly_correlated_pairs": highly_correlated_pairs[:10]
    }

    # Generate Markdown Report
    report_lines = [
        "# Feature Quality Audit Report — PRAHARI PPG Pipeline",
        "",
        "## 1. Summary Statistics",
        f"- **Total Subject Recordings Evaluated**: {len(df_features)}",
        f"- **Total ML Features Extracted**: {len(feature_cols)}",
        f"- **Target Column**: `hemoglobin_g_dl` (Isolated)",
        "",
        "### Feature Breakdown by Category:",
    ]
    for cat, cnt in sorted(audit_stats["feature_categories"].items(), key=lambda x: -x[1]):
        report_lines.append(f"- **{cat}**: {cnt} features")

    report_lines.extend([
        "",
        "---",
        "",
        "## 2. Data Cleanliness & Integrity Audit",
        f"- **NaN / Missing Values**: {'None (0 across all features)' if not nan_features else f'{len(nan_features)} features with NaNs'}",
        f"- **Infinite Values**: {'None (0 across all features)' if not inf_features else f'{len(inf_features)} features with Infs'}",
        f"- **Constant Features (std = 0)**: {len(constant_features)} ({', '.join(constant_features) if constant_features else 'None'})",
        f"- **Low-Variance Features (std < 1e-4)**: {len(low_variance_features)} ({', '.join(low_variance_features) if low_variance_features else 'None'})",
        f"- **Highly Collinear Feature Pairs (|r| > 0.98)**: {len(highly_correlated_pairs)} pairs identified",
        "",
        "### Notes on Constant/Normalized Features:",
        "- `red_std`, `ir_std`, `red_var`, `ir_var` on clean signals have standard deviation 0 across recordings because signals undergo per-recording Z-score normalization ($std=1.0$). These constants are safely handled by standard scalers or tree models.",
        "- Raw optical metrics (`red_raw_dc`, `red_raw_ac`, `ir_raw_dc`, `ir_raw_ac`, `ratio_of_ratios`) retain dynamic unnormalized physical variations.",
        "",
        "---",
        "",
        "## 3. Sample Highly Correlated Feature Pairs (|r| > 0.98)",
        "| Feature 1 | Feature 2 | Pearson |r| |",
        "|---|---|---|"
    ])
    for p in highly_correlated_pairs[:10]:
        report_lines.append(f"| `{p[0]}` | `{p[1]}` | {p[2]:.4f} |")

    report_text = "\n".join(report_lines)
    return df_summary, audit_stats, report_text


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract PPG features and generate audit reports.")
    parser.add_argument(
        "--raw-dir",
        type=str,
        default=os.path.join(PROJECT_ROOT, "data", "raw"),
        help="Path to raw data directory"
    )
    parser.add_argument(
        "--output-features",
        type=str,
        default=os.path.join(PROJECT_ROOT, "data", "processed", "ppg_features.csv"),
        help="Path to save extracted features CSV"
    )
    parser.add_argument(
        "--summary-output",
        type=str,
        default=os.path.join(PROJECT_ROOT, "data", "metadata", "feature_summary.csv"),
        help="Path to save feature dictionary summary"
    )
    parser.add_argument(
        "--audit-report",
        type=str,
        default=os.path.join(PROJECT_ROOT, "reports", "feature_audit.md"),
        help="Path to save markdown feature audit report"
    )
    parser.add_argument(
        "--fs",
        type=float,
        default=25.0,
        help="Verified sampling rate in Hz (default: 25.0)"
    )
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    out_features = Path(args.output_features)
    out_summary = Path(args.summary_output)
    out_audit = Path(args.audit_report)

    if not raw_dir.exists():
        print(f"ERROR: Raw data directory not found: {raw_dir}", file=sys.stderr)
        return 1

    print("=" * 80)
    print("PRAHARI PPG PIPELINE -- EXTRACTING FEATURES (STEP 3F)")
    print("=" * 80)

    csv_files = sorted(
        list(raw_dir.glob("*.csv")),
        key=lambda p: int(p.stem) if p.stem.isdigit() else p.name
    )
    print(f"Found {len(csv_files)} subject recordings in {raw_dir}")

    feature_rows = []
    for f in csv_files:
        row = extract_features_from_recording(f, fs=args.fs)
        feature_rows.append(row)

    df_features = pd.DataFrame(feature_rows)

    # Reorder columns: identifiers, demographics, signal features, target
    meta_cols = ["subject_id", "recording_id", "source_file", "gender", "age", "gender_encoded"]
    target_col = "hemoglobin_g_dl"
    signal_cols = [c for c in df_features.columns if c not in meta_cols and c != target_col]
    df_features = df_features[meta_cols + signal_cols + [target_col]]

    out_features.parent.mkdir(parents=True, exist_ok=True)
    df_features.to_csv(out_features, index=False)
    print(f"  [+] Saved Extracted Features Table ({len(df_features)} rows x {len(df_features.columns)} cols) to: {out_features}")

    # Audit features
    df_summary, audit_stats, report_text = audit_features(df_features)

    out_summary.parent.mkdir(parents=True, exist_ok=True)
    df_summary.to_csv(out_summary, index=False)
    print(f"  [+] Saved Feature Summary Dictionary to: {out_summary}")

    out_audit.parent.mkdir(parents=True, exist_ok=True)
    with open(out_audit, "w", encoding="utf-8") as fp:
        fp.write(report_text)
    print(f"  [+] Saved Feature Audit Report to: {out_audit}")

    print("-" * 80)
    print("FEATURE BREAKDOWN BY CATEGORY:")
    for cat, cnt in audit_stats["feature_categories"].items():
        print(f"  * {cat:<32}: {cnt:>2} features")
    print(f"  * Target Variable                 :  1 (`hemoglobin_g_dl`)")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    from typing import Tuple
    sys.exit(main())
