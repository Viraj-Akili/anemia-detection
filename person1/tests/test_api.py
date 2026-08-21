"""Tests for the PRAHARI anemia screening API.

Uses FastAPI TestClient (no real server needed) and real dataset images
from the test split.  All 5 prior test suites must still pass.

Run:  pytest tests/test_api.py -v
"""

from __future__ import annotations

import io
import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image
import numpy as np

# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    """Create a TestClient that triggers the lifespan (model loading)."""
    from app.main import app

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture(scope="module")
def sample_images() -> dict[str, str]:
    """One anemic and one non-anemic image from the test split."""
    import pandas as pd
    manifest = pd.read_csv("data/manifest.csv")
    test = manifest[manifest["split"] == "test"]
    # Pick any image from each class — the API contract test doesn't require
    # the model to be right, just that it runs and returns valid output.
    anemic_rows = test[test["label"] == "anemic"]
    non_anemic_rows = test[test["label"] == "non_anemic"]
    assert len(anemic_rows) > 0, "no anemic test images found"
    assert len(non_anemic_rows) > 0, "no non-anemic test images found"
    return {
        "anemic": str(anemic_rows.iloc[0]["image_path"]),
        "non_anemic": str(non_anemic_rows.iloc[0]["image_path"]),
    }


# ── Health ────────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_200(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert body["model_loaded"] is True
        assert "random_forest" in body["model"]

    def test_health_degraded_when_no_engine(self, client):
        from app.api.anemia import engine as original_engine, set_engine
        try:
            set_engine(None)
            r = client.get("/health")
            assert r.status_code == 200
            body = r.json()
            assert body["status"] == "degraded"
            assert body["model_loaded"] is False
            assert body["model"] == "none"
            assert body["version"] == "n/a"
        finally:
            set_engine(original_engine)

    def test_no_filesystem_paths_in_health_or_screen(self, client, sample_images):
        r_health = client.get("/health")
        text_health = r_health.text
        assert "c:\\" not in text_health.lower()
        assert "models/" not in text_health.lower()

        path = sample_images["anemic"]
        with open(path, "rb") as f:
            r_screen = client.post(
                "/api/v1/anemia/screen",
                files={"image": (Path(path).name, f, "image/png")},
            )
        text_screen = r_screen.text
        assert "c:\\" not in text_screen.lower()
        assert "models/" not in text_screen.lower()


class TestModels:
    def test_models_200(self, client):
        r = client.get("/models")
        assert r.status_code == 200
        body = r.json()
        assert body["name"] == "random_forest_color_baseline"
        assert body["version"] == "1.0"
        assert "anemic" in body["labels"]
        assert "non_anemic" in body["labels"]


# ── Valid inference ───────────────────────────────────────────────────────

class TestValidScreen:
    def test_anemic_image(self, client, sample_images):
        path = sample_images["anemic"]
        with open(path, "rb") as f:
            r = client.post(
                "/api/v1/anemia/screen",
                files={"image": (Path(path).name, f, "image/png")},
            )
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert body["prediction"]["label"] in ("anemic", "non_anemic")  # label is model-dependent
        assert 0.0 <= body["prediction"]["model_probability"] <= 1.0
        assert 0.0 <= body["prediction"]["model_confidence"] <= 1.0
        assert body["image_quality"]["status"] == "good"
        assert body["inference"]["model"] == "random_forest_color_baseline"

    def test_non_anemic_image(self, client, sample_images):
        path = sample_images["non_anemic"]
        with open(path, "rb") as f:
            r = client.post(
                "/api/v1/anemia/screen",
                files={"image": (Path(path).name, f, "image/png")},
            )
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert body["prediction"]["label"] == "non_anemic"


# ── Error handling ────────────────────────────────────────────────────────

class TestErrorHandling:
    def test_missing_image(self, client):
        r = client.post("/api/v1/anemia/screen")
        assert r.status_code == 422

    def test_empty_upload(self, client):
        r = client.post(
            "/api/v1/anemia/screen",
            files={"image": ("empty.png", b"", "image/png")},
        )
        assert r.status_code == 400

    def test_unsupported_format(self, client):
        r = client.post(
            "/api/v1/anemia/screen",
            files={"image": ("fake.txt", b"not an image", "text/plain")},
        )
        assert r.status_code == 415

    def test_corrupted_image(self, client):
        garbage = b"\x89PNG\r\n\x1a\n" + b"\xff" * 50  # starts like PNG but is garbage
        r = client.post(
            "/api/v1/anemia/screen",
            files={"image": ("corrupt.png", garbage, "image/png")},
        )
        # Engine either returns success=false or 400; both are acceptable
        assert r.status_code in (200, 400)

    def test_poor_quality_image(self, client):
        # Very dark synthetic image
        arr = np.random.randint(0, 15, (50, 50, 3), dtype=np.uint8)
        buf = io.BytesIO()
        Image.fromarray(arr).save(buf, format="PNG")
        buf.seek(0)
        r = client.post(
            "/api/v1/anemia/screen",
            files={"image": ("dark.png", buf.read(), "image/png")},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is False
        assert body["error"]["code"] == "IMAGE_QUALITY_LOW"

    def test_no_stack_trace_in_error(self, client):
        r = client.post(
            "/api/v1/anemia/screen",
            files={"image": ("fake.txt", b"not an image", "text/plain")},
        )
        text = r.text.lower()
        assert "traceback" not in text
        assert "traceback" not in r.json().get("detail", "")


# ── Response schema ───────────────────────────────────────────────────────

class TestResponseSchema:
    def test_success_has_all_fields(self, client, sample_images):
        path = sample_images["anemic"]
        with open(path, "rb") as f:
            r = client.post(
                "/api/v1/anemia/screen",
                files={"image": (Path(path).name, f, "image/png")},
            )
        body = r.json()
        assert "success" in body
        assert "prediction" in body
        assert "image_quality" in body
        assert "inference" in body
        # prediction sub-fields
        pred = body["prediction"]
        assert "label" in pred
        assert "model_probability" in pred
        assert "model_confidence" in pred
        # quality sub-fields
        q = body["image_quality"]
        assert "status" in q
        assert "score" in q
        assert "checks" in q
        assert "reasons" in q

    def test_failure_has_error_field(self, client):
        r = client.post(
            "/api/v1/anemia/screen",
            files={"image": ("fake.txt", b"not an image", "text/plain")},
        )
        # HTTPException responses are wrapped in {"detail": ...}
        body = r.json()
        detail = body.get("detail", body)  # unwrap if wrapped
        assert detail.get("success") is False
        assert "error" in detail
        assert "code" in detail["error"]
        assert "message" in detail["error"]
