"""
tests/test_dataset_discovery.py
Tests for Step 1A Dataset Discovery logic.
"""

import pytest
from pathlib import Path
from scripts.inspect_dataset import (
    find_csv_files,
    inspect_single_file,
    inspect_dataset,
    EXPECTED_COLUMNS
)


def test_find_csv_files(mock_dataset_dir):
    files = find_csv_files(mock_dataset_dir)
    assert len(files) == 3
    assert all(f.suffix == ".csv" for f in files)


def test_inspect_single_valid_file(mock_dataset_dir):
    file_path = mock_dataset_dir / "1.csv"
    res = inspect_single_file(file_path, mock_dataset_dir)
    assert res["is_empty"] is False
    assert res["is_malformed"] is False
    assert res["n_rows"] == 250
    assert res["n_cols"] == 5
    assert res["has_expected_columns"] is True
    assert res["inferred_subject_id"] == 1
    assert res["gender"] == ["Female"]
    assert res["age"] == [28]
    assert res["hemoglobin"] == [11.5]


def test_inspect_corrupt_files(mock_corrupt_dataset_dir):
    # Empty file
    res_empty = inspect_single_file(mock_corrupt_dataset_dir / "empty.csv", mock_corrupt_dataset_dir)
    assert res_empty["is_empty"] is True

    # Missing column
    res_missing = inspect_single_file(mock_corrupt_dataset_dir / "missing_col.csv", mock_corrupt_dataset_dir)
    assert res_missing["has_expected_columns"] is False
    assert "Infra Red (a.u)" in res_missing["missing_columns"]


def test_inspect_dataset_summary(mock_dataset_dir):
    summary = inspect_dataset(mock_dataset_dir)
    assert summary["total_files"] == 3
    assert summary["empty_files_count"] == 0
    assert summary["malformed_files_count"] == 0
    assert summary["subject_ids_reliable"] is True
    assert summary["unique_genders"] == ["Female", "Male"]
    assert summary["age_range"] == (28, 60)
    assert summary["hb_range"] == (10.2, 14.8)
    assert summary["sample_count_distribution"] == {250: 2, 249: 1}
