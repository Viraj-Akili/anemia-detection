"""
Step 8 Contract & End-to-End Verification Test
Verifies that FastAPI backend /api/screenings/evaluate-multimodal perfectly matches
the frontend's TypeScript API Client contract (apiClient.ts & types/index.ts).
"""

import io
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Setup workspace and backend module paths
WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = WORKSPACE_ROOT / "arya-backend" / "backend"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))
if str(WORKSPACE_ROOT / "person1") not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT / "person1"))
if str(WORKSPACE_ROOT / "ppg-anemia" / "src") not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT / "ppg-anemia" / "src"))
for risk_src in (WORKSPACE_ROOT / "risk-engine" / "backend" / "src", WORKSPACE_ROOT / "swayam risk" / "backend" / "src"):
    if risk_src.exists() and str(risk_src) not in sys.path:
        sys.path.insert(0, str(risk_src))

import app as arya_app
if str(BACKEND_ROOT / "app") not in arya_app.__path__:
    arya_app.__path__.insert(0, str(BACKEND_ROOT / "app"))
if str(WORKSPACE_ROOT / "person1" / "app") not in arya_app.__path__:
    arya_app.__path__.append(str(WORKSPACE_ROOT / "person1" / "app"))

from app.database import Base, get_db
from app.main import app
from app.models import User, UserRole


@pytest.fixture(name="db_session")
def fixture_db_session():
    """Create a clean in-memory SQLite database for test isolation."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    # Create default test worker
    worker = User(
        id=1,
        username="test_worker",
        full_name="Frontline Test Health Worker",
        role=UserRole.WORKER,
        is_active=True,
    )
    db.add(worker)
    db.commit()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(name="client")
def fixture_client(db_session):
    """Create a FastAPI test client wired to the isolated test database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_frontend_contract_full_multimodal(client):
    """Test full multimodal request with image + PPG CSV matching frontend FormData."""
    # Build sample 250-sample CSV matching hardware format
    csv_lines = ["timestamp_ms,red,ir"]
    for i in range(250):
        t = i * 40
        red = 120000 + int(5000 * (1 + 0.1 * (i % 25)))
        ir = 140000 + int(6000 * (1 + 0.1 * (i % 25)))
        csv_lines.append(f"{t},{red},{ir}")
    csv_bytes = "\n".join(csv_lines).encode("utf-8")

    # Minimal 100x100 PNG image
    import numpy as np
    from PIL import Image
    img_arr = np.full((100, 100, 3), (180, 70, 70), dtype=np.uint8)
    pil_img = Image.fromarray(img_arr)
    img_buf = io.BytesIO()
    pil_img.save(img_buf, format="PNG")
    img_bytes = img_buf.getvalue()

    form_data = {
        "age_years": "28.0",
        "gender": "FEMALE",
        "patient_name": "Sunita Devi",
        "is_pregnant": "true",
        "trimester": "2",
        "weight_kg": "55.0",
        "height_cm": "158.0",
        "muac_cm": "23.5",
        "diet_iron_rich": "false",
        "diet_frequency": "rare",
        "diet_diversity": "2",
        "ifa_adherence": "unknown",
        "symptom_severe_pallor": "true",
        "symptom_breathlessness": "false",
        "symptom_fatigue": "true",
        "symptom_bilateral_oedema": "false",
        "device_id": "PRAHARI_FRONTEND_WEB",
    }

    files = [
        ("image", ("conjunctiva.png", img_bytes, "image/png")),
        ("ppg_csv", ("recording.csv", csv_bytes, "text/csv")),
    ]

    response = client.post("/api/screenings/evaluate-multimodal", data=form_data, files=files)
    assert response.status_code == 201, f"Expected 201 Created, got {response.status_code}: {response.text}"

    data = response.json()

    # Verify top-level contract
    assert data["success"] is True
    assert isinstance(data["screening_id"], int)
    assert isinstance(data["beneficiary_id"], int)
    assert "timestamp" in data

    # Verify patient schema
    assert data["patient"]["name"] == "Sunita Devi"
    assert data["patient"]["age_years"] == 28.0
    assert data["patient"]["gender"] == "FEMALE"
    assert data["patient"]["is_pregnant"] is True
    assert data["patient"]["trimester"] == 2

    # Verify image schema
    img = data["image"]
    assert img["available"] is True
    assert img["status"] in ["SUCCESS", "REJECTED"]
    assert "quality_status" in img
    assert isinstance(img["quality_reasons"], list)
    if img["status"] == "SUCCESS":
        assert img["label"] in ["anemic", "non_anemic"]
        assert 0.0 <= img["probability"] <= 1.0
        assert 0.0 <= img["confidence"] <= 1.0

    # Verify PPG schema
    ppg = data["ppg"]
    assert ppg["available"] is True
    assert ppg["status"] == "SUCCESS"
    assert isinstance(ppg["predicted_hb_g_dl"], (int, float))
    assert ppg["samples"] == 250
    assert ppg["sampling_rate_hz"] == 25.0
    assert ppg["signal_quality"] in ["GOOD", "POOR", "UNUSABLE"]

    # Verify Risk & WHO Red Flag schema
    risk = data["risk"]
    assert risk["anemia_risk"] in ["low", "moderate", "high", "critical"]
    assert risk["nutrition_risk"] in ["low", "moderate", "high", "critical"]
    assert risk["overall_priority"] in ["low", "moderate", "high", "critical"]
    assert risk["hb_source"] == "PPG_SENSOR"
    assert isinstance(risk["safety_flags"], list)
    assert isinstance(risk["contributors"], list)
    assert isinstance(risk["recommended_action"], str)

    # Verify Scientific constraint schema (No Mathematical Fusion)
    fusion = data["fusion"]
    assert fusion["status"] == "NOT_VALIDATED"
    assert fusion["fused_prediction"] is None


def test_frontend_contract_image_only(client):
    """Test frontend contract when only image is uploaded."""
    import numpy as np
    from PIL import Image
    img_arr = np.full((100, 100, 3), (120, 90, 80), dtype=np.uint8)
    pil_img = Image.fromarray(img_arr)
    img_buf = io.BytesIO()
    pil_img.save(img_buf, format="PNG")

    form_data = {
        "age_years": "4.0",
        "gender": "MALE",
        "patient_name": "Aarav",
        "is_pregnant": "false",
        "muac_cm": "13.0",
    }

    files = [("image", ("eye.png", img_buf.getvalue(), "image/png"))]
    response = client.post("/api/screenings/evaluate-multimodal", data=form_data, files=files)
    assert response.status_code == 201
    data = response.json()

    assert data["image"]["available"] is True
    assert data["ppg"]["available"] is False
    assert data["risk"]["hb_source"] == "NONE"


def test_frontend_contract_ppg_only(client):
    """Test frontend contract when only PPG CSV is uploaded."""
    csv_lines = ["timestamp_ms,red,ir"]
    for i in range(250):
        t = i * 40
        red = 120000 + int(5000 * (1 + 0.1 * (i % 25)))
        ir = 140000 + int(6000 * (1 + 0.1 * (i % 25)))
        csv_lines.append(f"{t},{red},{ir}")
    csv_bytes = "\n".join(csv_lines).encode("utf-8")

    form_data = {
        "age_years": "35.0",
        "gender": "FEMALE",
        "patient_name": "Kavita",
    }

    files = [("ppg_csv", ("recording.csv", csv_bytes, "text/csv"))]
    response = client.post("/api/screenings/evaluate-multimodal", data=form_data, files=files)
    assert response.status_code == 201
    data = response.json()

    assert data["image"]["available"] is False
    assert data["ppg"]["available"] is True
    assert data["risk"]["hb_source"] == "PPG_SENSOR"
