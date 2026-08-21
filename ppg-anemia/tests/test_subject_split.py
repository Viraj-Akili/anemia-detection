"""
tests/test_subject_split.py
Tests for Step 1F Subject-Level Split logic and leakage prevention.
"""

import pytest
import pandas as pd
import numpy as np
from scripts.create_subject_split import (
    perform_subject_level_split,
    compute_anemia_label
)


def test_compute_anemia_label():
    assert compute_anemia_label("Female", 11.9) == "Anemic"
    assert compute_anemia_label("Female", 12.0) == "Non-Anemic"
    assert compute_anemia_label("Male", 12.9) == "Anemic"
    assert compute_anemia_label("Male", 13.0) == "Non-Anemic"


def test_perform_subject_level_split_no_leakage():
    # Create a synthetic 68-subject metadata table
    n_subs = 68
    records = []
    for i in range(1, n_subs + 1):
        records.append({
            "subject_id": i,
            "recording_id": f"sub_{i:03d}_rec_01",
            "source_file": f"data/raw/{i}.csv",
            "n_samples": 250 if i % 2 == 0 else 249,
            "n_channels": 2,
            "gender": "Female" if i <= 38 else "Male",
            "age": 20 + (i % 45),
            "hemoglobin_g_dl": 9.5 + (i * 0.11),
            "sampling_rate_hz_verified": "UNVERIFIED",
            "duration_sec_verified": "UNVERIFIED"
        })
    df_meta = pd.DataFrame(records)

    train_df, val_df, test_df = perform_subject_level_split(
        df_meta,
        train_ratio=0.70,
        val_ratio=0.15,
        test_ratio=0.15,
        random_seed=42
    )

    train_subs = set(train_df["subject_id"])
    val_subs = set(val_df["subject_id"])
    test_subs = set(test_df["subject_id"])

    # Strict leakage assertion
    assert len(train_subs & val_subs) == 0, "Train and Val share subjects!"
    assert len(train_subs & test_subs) == 0, "Train and Test share subjects!"
    assert len(val_subs & test_subs) == 0, "Val and Test share subjects!"

    # Completeness assertion
    assert len(train_subs) + len(val_subs) + len(test_subs) == n_subs

    # Split sizes
    assert len(train_df) >= 45
    assert len(val_df) >= 8
    assert len(test_df) >= 8


def test_subject_split_reproducibility():
    records = [
        {"subject_id": i, "recording_id": f"sub_{i:03d}_rec_01", "source_file": f"data/raw/{i}.csv",
         "n_samples": 250, "n_channels": 2, "gender": "Male", "age": 30, "hemoglobin_g_dl": 13.0}
        for i in range(1, 21)
    ]
    df_meta = pd.DataFrame(records)

    t1, v1, te1 = perform_subject_level_split(df_meta, random_seed=123)
    t2, v2, te2 = perform_subject_level_split(df_meta, random_seed=123)

    assert t1["subject_id"].tolist() == t2["subject_id"].tolist()
    assert v1["subject_id"].tolist() == v2["subject_id"].tolist()
    assert te1["subject_id"].tolist() == te2["subject_id"].tolist()
