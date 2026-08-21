"""
tests/test_dataset_validation.py
Tests for Step 1B Dataset Validation logic.
"""

import pytest
import json
from pathlib import Path
from scripts.validate_dataset import (
    validate_file,
    validate_dataset,
    compute_signal_hash,
    REQUIRED_COLUMNS
)


def test_validate_valid_file(mock_dataset_dir):
    res = validate_file(mock_dataset_dir / "1.csv")
    assert res["is_valid"] is True
    assert len(res["critical_errors"]) == 0
    assert res["red_is_numeric"] is True
    assert res["ir_is_numeric"] is True
    assert res["has_nan"] is False
    assert res["has_inf"] is False
    assert res["gender_uniform"] is True
    assert res["age_uniform"] is True
    assert res["hb_uniform"] is True


def test_validate_corrupt_files(mock_corrupt_dataset_dir):
    # NaN file
    res_nan = validate_file(mock_corrupt_dataset_dir / "has_nan.csv")
    assert res_nan["is_valid"] is False
    assert res_nan["has_nan"] is True

    # Missing column file
    res_missing = validate_file(mock_corrupt_dataset_dir / "missing_col.csv")
    assert res_missing["is_valid"] is False
    assert len(res_missing["missing_columns"]) > 0

    # Negative signal file
    res_neg = validate_file(mock_corrupt_dataset_dir / "has_neg.csv")
    assert res_neg["ir_negative_count"] > 0
    assert any("Negative signal" in w for w in res_neg["warnings"])

    # Inconsistent age
    res_inconsistent = validate_file(mock_corrupt_dataset_dir / "inconsistent_age.csv")
    assert res_inconsistent["is_valid"] is False
    assert res_inconsistent["age_uniform"] is False


def test_validate_dataset_summary(mock_dataset_dir):
    summary_json, text_report = validate_dataset(mock_dataset_dir)
    assert summary_json["status"] == "PASSED"
    assert summary_json["total_files_analyzed"] == 3
    assert summary_json["valid_files_count"] == 3
    assert summary_json["all_required_columns_present"] is True
    assert summary_json["nan_values_detected"] is False
    assert "PRAHARI PPG PIPELINE" in text_report
