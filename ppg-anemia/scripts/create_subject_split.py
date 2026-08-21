"""
scripts/create_subject_split.py

STEP 1F — LEAKAGE-FREE SUBJECT-LEVEL SPLIT GENERATOR
PRAHARI PPG / Hardware ML Pipeline

SAFETY & LEAKAGE PREVENTION:
Splitting MUST be performed strictly at the SUBJECT level (not by individual recording or window).
A subject that appears in Train must NEVER appear in Validation or Test.
This script only generates partition metadata and does NOT train any model.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Dict, Tuple, List, Any
import pandas as pd
import numpy as np


def compute_anemia_label(gender: str, hb: float) -> str:
    """
    Standard WHO clinical hemoglobin cutoffs for anemia in adults:
    - Female: Hb < 12.0 g/dL
    - Male: Hb < 13.0 g/dL
    """
    g = str(gender).strip().lower()
    if g == "female":
        return "Anemic" if hb < 12.0 else "Non-Anemic"
    elif g == "male":
        return "Anemic" if hb < 13.0 else "Non-Anemic"
    else:
        return "Anemic" if hb < 12.5 else "Non-Anemic"


def perform_subject_level_split(
    df_meta: pd.DataFrame,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    random_seed: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Generate deterministic, stratified subject-level splits (Train, Validation, Test).
    Ensures zero subject overlap across splits.
    """
    assert abs((train_ratio + val_ratio + test_ratio) - 1.0) < 1e-5, "Split ratios must sum to 1.0"

    # Collapse recording-level metadata to distinct subjects
    subject_df = (
        df_meta.groupby("subject_id")
        .agg({
            "gender": "first",
            "age": "first",
            "hemoglobin_g_dl": "first",
            "recording_id": "count",
            "n_samples": "mean"
        })
        .reset_index()
        .rename(columns={"recording_id": "n_recordings"})
    )

    # Assign stratification category based on Gender + Clinical Anemia status
    subject_df["anemia_status"] = [
        compute_anemia_label(row["gender"], row["hemoglobin_g_dl"])
        for _, row in subject_df.iterrows()
    ]
    subject_df["strata"] = subject_df["gender"].astype(str) + "_" + subject_df["anemia_status"].astype(str)

    rng = np.random.default_rng(random_seed)

    train_sub_ids: List[Any] = []
    val_sub_ids: List[Any] = []
    test_sub_ids: List[Any] = []

    # Stratified allocation per stratum
    for stratum, group in subject_df.groupby("strata"):
        sub_ids = group["subject_id"].tolist()
        rng.shuffle(sub_ids)
        n = len(sub_ids)

        n_train = int(round(n * train_ratio))
        n_val = int(round(n * val_ratio))
        # Ensure at least 1 in val and test if group is large enough
        if n >= 3 and n_val == 0:
            n_val = 1
        n_test = n - n_train - n_val

        # Guard against negative counts in small strata
        if n_test < 0:
            n_test = 0
            n_train = n - n_val

        s_train = sub_ids[:n_train]
        s_val = sub_ids[n_train:n_train + n_val]
        s_test = sub_ids[n_train + n_val:]

        train_sub_ids.extend(s_train)
        val_sub_ids.extend(s_val)
        test_sub_ids.extend(s_test)

    # Convert to DataFrames
    train_df = subject_df[subject_df["subject_id"].isin(train_sub_ids)].copy().sort_values("subject_id")
    val_df = subject_df[subject_df["subject_id"].isin(val_sub_ids)].copy().sort_values("subject_id")
    test_df = subject_df[subject_df["subject_id"].isin(test_sub_ids)].copy().sort_values("subject_id")

    # CRITICAL LEAKAGE VALIDATION CHECKS
    train_set = set(train_df["subject_id"])
    val_set = set(val_df["subject_id"])
    test_set = set(test_df["subject_id"])

    assert len(train_set & val_set) == 0, f"DATA LEAKAGE: Train and Val overlap on {train_set & val_set}"
    assert len(train_set & test_set) == 0, f"DATA LEAKAGE: Train and Test overlap on {train_set & test_set}"
    assert len(val_set & test_set) == 0, f"DATA LEAKAGE: Val and Test overlap on {val_set & test_set}"
    assert len(train_set) + len(val_set) + len(test_set) == len(subject_df), "Subject count mismatch in split"

    train_df["split"] = "train"
    val_df["split"] = "validation"
    test_df["split"] = "test"

    return train_df, val_df, test_df


def print_split_summary(train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame) -> None:
    """Print clean summary table of split statistics."""
    total = len(train_df) + len(val_df) + len(test_df)
    print("=" * 80)
    print("PRAHARI PPG PIPELINE -- SUBJECT-LEVEL SPLIT SUMMARY (STEP 1F)")
    print("=" * 80)
    print(f"Total Unique Subjects: {total}")
    print(f"  * Train Set:      {len(train_df):>3} subjects ({len(train_df)/total*100:5.1f}%)")
    print(f"  * Validation Set: {len(val_df):>3} subjects ({len(val_df)/total*100:5.1f}%)")
    print(f"  * Test Set:       {len(test_df):>3} subjects ({len(test_df)/total*100:5.1f}%)")
    print("-" * 80)

    for name, df in [("TRAIN", train_df), ("VALIDATION", val_df), ("TEST", test_df)]:
        g_counts = df["gender"].value_counts().to_dict()
        anemia_counts = df["anemia_status"].value_counts().to_dict()
        hb_mean = df["hemoglobin_g_dl"].mean()
        hb_std = df["hemoglobin_g_dl"].std()
        age_mean = df["age"].mean()
        print(f"[{name}] (N={len(df)})")
        print(f"  - Gender: {g_counts}")
        print(f"  - Anemia Status: {anemia_counts}")
        print(f"  - Hemoglobin: Mean = {hb_mean:.2f} +/- {hb_std:.2f} g/dL (Min: {df['hemoglobin_g_dl'].min():.1f}, Max: {df['hemoglobin_g_dl'].max():.1f})")
        print(f"  - Age: Mean = {age_mean:.1f} years (Min: {df['age'].min()}, Max: {df['age'].max()})")
        print(f"  - Subject IDs: {sorted(df['subject_id'].tolist())}")
        print("-" * 80)

    print("[SUCCESS] Zero subject overlap verified across Train, Validation, and Test partitions.")
    print("=" * 80)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create leakage-free subject-level splits.")
    parser.add_argument(
        "--metadata-path",
        type=str,
        default=os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "metadata", "recordings_metadata.csv"),
        help="Path to master recordings_metadata.csv"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "metadata"),
        help="Path to output split files"
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    meta_path = Path(args.metadata_path)
    output_dir = Path(args.output_dir)

    if not meta_path.exists():
        print(f"ERROR: Metadata file not found at: {meta_path}. Run build_metadata.py first.", file=sys.stderr)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    df_meta = pd.read_csv(meta_path)
    train_df, val_df, test_df = perform_subject_level_split(
        df_meta,
        train_ratio=0.70,
        val_ratio=0.15,
        test_ratio=0.15,
        random_seed=args.seed
    )

    # Save to metadata directory
    train_path = output_dir / "train_subjects.csv"
    val_path = output_dir / "validation_subjects.csv"
    test_path = output_dir / "test_subjects.csv"

    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    test_df.to_csv(test_path, index=False)

    print_split_summary(train_df, val_df, test_df)
    print(f"Saved: {train_path}")
    print(f"Saved: {val_path}")
    print(f"Saved: {test_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
