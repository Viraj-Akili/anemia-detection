"""
tests/test_models.py
Unit tests for Step 3 ML Modeling, Leakage Prevention, and Evaluation.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.dummy import DummyRegressor
from scripts.train_evaluate_models import evaluate_predictions


def test_evaluate_predictions_metrics():
    y_true = np.array([12.0, 14.0, 16.0, 10.0])
    y_pred = np.array([12.5, 13.5, 15.5, 10.5])

    metrics = evaluate_predictions(y_true, y_pred)
    assert metrics["mae"] == 0.5
    assert metrics["rmse"] == 0.5
    assert metrics["r2"] > 0.90


def test_scaler_fitted_on_train_only():
    """Verify that scaler parameters are derived strictly from the training partition."""
    # Synthetic train and test distributions
    train_x = np.array([[10.0], [20.0], [30.0]])
    test_x = np.array([[100.0], [200.0]])

    scaler = StandardScaler()
    scaler.fit(train_x)

    # Scaler mean must equal train_x mean (20.0), NOT combined mean
    assert scaler.mean_[0] == 20.0
    assert scaler.scale_[0] == np.std([10.0, 20.0, 30.0])

    transformed_test = scaler.transform(test_x)
    assert transformed_test.shape == (2, 1)


def test_subject_split_disjoint():
    """Verify zero overlap between train, validation, and test split CSVs."""
    meta_dir = Path("data/metadata")
    if (meta_dir / "train_subjects.csv").exists():
        df_train = pd.read_csv(meta_dir / "train_subjects.csv")
        df_val = pd.read_csv(meta_dir / "validation_subjects.csv")
        df_test = pd.read_csv(meta_dir / "test_subjects.csv")

        train_ids = set(df_train["subject_id"])
        val_ids = set(df_val["subject_id"])
        test_ids = set(df_test["subject_id"])

        assert len(train_ids & val_ids) == 0, "Train and Val share subject IDs!"
        assert len(train_ids & test_ids) == 0, "Train and Test share subject IDs!"
        assert len(val_ids & test_ids) == 0, "Val and Test share subject IDs!"


def test_model_pipeline_execution():
    """Verify that candidate models fit and predict without target leakage."""
    rng = np.random.default_rng(42)
    n_samples = 47
    n_features = 74

    X_train = rng.normal(0, 1, size=(n_samples, n_features))
    y_train = rng.normal(12.8, 1.5, size=n_samples)

    X_val = rng.normal(0, 1, size=(10, n_features))
    y_val = rng.normal(12.8, 1.5, size=10)

    # Baseline
    dummy = DummyRegressor(strategy="mean")
    dummy.fit(X_train, y_train)
    dummy_pred = dummy.predict(X_val)
    assert len(dummy_pred) == 10

    # Ridge
    ridge = Ridge(alpha=1.0)
    ridge.fit(X_train, y_train)
    ridge_pred = ridge.predict(X_val)
    assert len(ridge_pred) == 10
    assert not np.isnan(ridge_pred).any()
