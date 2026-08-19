"""Tests for the CNN model (Hour 4). Run with pytest."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import torch

from app.ai.cnn_model import (
    AnemiaCNN,
    create_model,
    load_checkpoint,
    predict_proba,
    save_checkpoint,
)


@pytest.fixture()
def model():
    return create_model("mobilenet_v2", pretrained=False, device="cpu")


def test_model_initializes(model):
    assert isinstance(model, AnemiaCNN)
    assert model.backbone_name == "mobilenet_v2"


def test_model_accepts_224_input(model):
    x = torch.randn(2, 3, 224, 224)
    out = model(x)
    assert out.shape == (2, 1)


def test_output_is_logit_shape(model):
    # Binary head => 1 logit per sample.
    x = torch.randn(4, 3, 224, 224)
    assert model(x).shape == (4, 1)


def test_unknown_backbone_raises():
    with pytest.raises(ValueError):
        create_model("resnet_152", pretrained=False)


def test_checkpoint_roundtrip(tmp_path: Path):
    m = create_model("mobilenet_v2", pretrained=False)
    path = tmp_path / "ckpt.pth"
    save_checkpoint(m, path, extra={"classes": ["anemic", "non_anemic"]})
    assert path.exists()
    loaded = load_checkpoint(path, device="cpu")
    # Same weights after roundtrip
    for (k1, v1), (k2, v2) in zip(m.state_dict().items(), loaded.state_dict().items()):
        assert torch.equal(v1, v2)


def test_predict_proba_valid(model):
    x = torch.randn(8, 3, 224, 224)
    p = predict_proba(model, x, "cpu")
    assert p.shape == (8,)
    assert ((p >= 0) & (p <= 1)).all()
    assert torch.isfinite(p).all()


def test_prediction_labels_valid(model):
    x = torch.randn(16, 3, 224, 224)
    p = predict_proba(model, x, "cpu").numpy()
    labels = np.where(p >= 0.5, "anemic", "non_anemic")
    assert set(labels) <= {"anemic", "non_anemic"}


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
def test_gpu_inference():
    m = create_model("mobilenet_v2", pretrained=False, device="cuda")
    x = torch.randn(2, 3, 224, 224, device="cuda")
    out = m(x)
    assert out.shape == (2, 1)
    p = predict_proba(m, x, "cuda")
    assert ((p >= 0) & (p <= 1)).all()
