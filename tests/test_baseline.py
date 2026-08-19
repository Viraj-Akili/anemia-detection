"""Tests for the classical baseline pipeline (Hour 3)."""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from PIL import Image

from app.ai.features import ColorFeatureExtractor
from app.ai.inference import ANEMIC, BaselineClassifier


def make_synthetic_images(tmp_path: Path, n: int, anemic: bool) -> list[Path]:
    """Solid-color RGBA crops: reddish (anemic) vs pale (non-anemic)."""
    paths = []
    base = (200, 90, 90) if anemic else (240, 210, 205)
    for i in range(n):
        p = tmp_path / f"{'anemic' if anemic else 'non'}_{i}.png"
        arr = np.zeros((30, 60, 4), dtype=np.uint8)
        arr[..., :3] = base
        arr[..., 3] = 255
        Image.fromarray(arr, mode="RGBA").save(p)
        paths.append(p)
    return paths


@pytest.fixture()
def synthetic_pipeline(tmp_path: Path):
    """A tiny trained pipeline (fit on train-only synthetic data)."""
    (tmp_path / "train").mkdir()
    train_an = make_synthetic_images(tmp_path / "train", 12, anemic=True)
    train_non = make_synthetic_images(tmp_path / "train", 8, anemic=False)
    X_train_paths = [str(p) for p in train_an + train_non]
    y_train = np.array([ANEMIC] * 12 + ["non_anemic"] * 8)

    pipe = Pipeline(
        [
            ("features", ColorFeatureExtractor()),
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=2000)),
        ]
    )
    pipe.fit(X_train_paths, y_train)
    model_path = tmp_path / "model.joblib"
    joblib.dump(pipe, model_path)
    return model_path, train_an[0], train_non[0]


def test_scaler_fit_on_train_only_consistent():
    # A scaler fit on training data transforms new data using the TRAINING
    # statistics only. X_train ~ N(10, 3), X_new ~ N(11, 3): standardized
    # values should center near (11 - 10) / 3 (per-feature noise allowed).
    rng = np.random.default_rng(0)
    X_train = rng.normal(10, 3, size=(50, 19))
    X_new = rng.normal(11, 3, size=(10, 19))
    scaler = StandardScaler().fit(X_train)
    out = scaler.transform(X_new)
    assert out.shape == (10, 19)
    assert not np.isnan(out).any()
    assert abs(out.mean() - 1 / 3) < 0.15


def test_saved_model_reloads(synthetic_pipeline):
    model_path, _, _ = synthetic_pipeline
    pipe = joblib.load(model_path)
    assert isinstance(pipe, Pipeline)
    assert "scaler" in pipe.named_steps
    assert "clf" in pipe.named_steps


def test_inference_valid_labels_and_proba(synthetic_pipeline, tmp_path):
    model_path, anemic_img, non_img = synthetic_pipeline
    clf = BaselineClassifier(model_path)
    pa = clf.predict(anemic_img)
    pn = clf.predict(non_img)

    assert pa.label in (ANEMIC, "non_anemic")
    assert 0.0 <= pa.probability <= 1.0
    assert 0.0 <= pa.confidence <= 1.0
    # Reddish (anemic-like) image should get higher P(anemic) than pale one.
    assert pa.probability > pn.probability


def test_inference_missing_model_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        BaselineClassifier(tmp_path / "does_not_exist.joblib")
