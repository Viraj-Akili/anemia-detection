"""
tests/conftest.py
Pytest fixtures for PRAHARI PPG Pipeline test suite.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path


@pytest.fixture
def mock_valid_df():
    """Create a standard valid raw PPG dataframe matching dataset specs."""
    n_samples = 250
    t = np.linspace(0, 10, n_samples)
    red = 115000 + 500 * np.sin(2 * np.pi * 1.2 * t) + np.random.normal(0, 20, n_samples)
    ir = 105000 + 600 * np.sin(2 * np.pi * 1.2 * t) + np.random.normal(0, 20, n_samples)
    df = pd.DataFrame({
        "Red (a.u)": red.astype(int),
        "Infra Red (a.u)": ir.astype(int),
        "Gender": ["Female"] * n_samples,
        "Age": [28] * n_samples,
        "Hemoglobin (g/dL)": [11.5] * n_samples
    })
    return df


@pytest.fixture
def mock_dataset_dir(tmp_path, mock_valid_df):
    """Create a temporary dataset directory with various valid and edge-case CSVs."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Valid file 1 (250 samples, Subject 1)
    mock_valid_df.to_csv(raw_dir / "1.csv", index=False)

    # Valid file 2 (249 samples, Subject 2)
    df2 = mock_valid_df.iloc[:249].copy()
    df2["Gender"] = "Male"
    df2["Age"] = 45
    df2["Hemoglobin (g/dL)"] = 14.8
    df2.to_csv(raw_dir / "2.csv", index=False)

    # Valid file 3 (250 samples, Subject 3)
    df3 = mock_valid_df.copy()
    df3["Gender"] = "Female"
    df3["Age"] = 60
    df3["Hemoglobin (g/dL)"] = 10.2
    df3.to_csv(raw_dir / "3.csv", index=False)

    return raw_dir


@pytest.fixture
def mock_corrupt_dataset_dir(tmp_path, mock_valid_df):
    """Create a directory with intentionally corrupted/edge-case CSVs."""
    corrupt_dir = tmp_path / "corrupt_raw"
    corrupt_dir.mkdir(parents=True, exist_ok=True)

    # 1. Missing columns
    df_missing = mock_valid_df.drop(columns=["Infra Red (a.u)"])
    df_missing.to_csv(corrupt_dir / "missing_col.csv", index=False)

    # 2. NaN values
    df_nan = mock_valid_df.copy()
    df_nan.loc[5, "Red (a.u)"] = np.nan
    df_nan.to_csv(corrupt_dir / "has_nan.csv", index=False)

    # 3. Negative values
    df_neg = mock_valid_df.copy()
    df_neg.loc[10, "Infra Red (a.u)"] = -100
    df_neg.to_csv(corrupt_dir / "has_neg.csv", index=False)

    # 4. Inconsistent metadata within file
    df_inconsistent = mock_valid_df.copy()
    df_inconsistent.loc[0:10, "Age"] = 30
    df_inconsistent.loc[11:, "Age"] = 40
    df_inconsistent.to_csv(corrupt_dir / "inconsistent_age.csv", index=False)

    # 5. Empty file (0 bytes)
    empty_file = corrupt_dir / "empty.csv"
    empty_file.write_text("")

    return corrupt_dir
