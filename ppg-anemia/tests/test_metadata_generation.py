"""
tests/test_metadata_generation.py
Tests for Step 1C Master Metadata Table generation.
"""

import pytest
import pandas as pd
from pathlib import Path
from scripts.build_metadata import (
    extract_recording_metadata,
    build_metadata_dataframe
)


def test_extract_recording_metadata(mock_dataset_dir):
    file_path = mock_dataset_dir / "1.csv"
    meta = extract_recording_metadata(file_path, mock_dataset_dir)

    assert meta["subject_id"] == 1
    assert meta["recording_id"] == "sub_001_rec_01"
    assert meta["n_samples"] == 250
    assert meta["n_channels"] == 2
    assert meta["gender"] == "Female"
    assert meta["age"] == 28
    assert meta["hemoglobin_g_dl"] == 11.5
    assert meta["sampling_rate_hz_verified"] == "UNVERIFIED"
    assert meta["duration_sec_verified"] == "UNVERIFIED"


def test_build_metadata_dataframe(mock_dataset_dir):
    df_meta = build_metadata_dataframe(mock_dataset_dir)
    assert len(df_meta) == 3
    expected_cols = [
        "subject_id", "recording_id", "source_file", "n_samples",
        "n_channels", "gender", "age", "hemoglobin_g_dl",
        "sampling_rate_hz_verified", "duration_sec_verified"
    ]
    for c in expected_cols:
        assert c in df_meta.columns
    assert df_meta["subject_id"].tolist() == [1, 2, 3]
