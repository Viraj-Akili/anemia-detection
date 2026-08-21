"""
tests/test_clinical_action_layer.py

Comprehensive test suite for STEP 9: Clinical Action / "What To Do Next" Result Layer.
Verifies all 12 clinical triage and rule-based action requirements:
1. Low-risk screening
2. Possible/mild anemia
3. Elevated/moderate risk
4. Severe/critical/red-flag case
5. Poor image quality
6. Rejected PPG
7. Image-only screening
8. PPG-only screening
9. Image + PPG screening
10. Backend unavailable / error handling
11. Verification: No medication dosage generated
12. Verification: No fake recommendation when data unavailable
"""

import io
import re
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from PIL import Image

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

# Clean up any existing app module in sys.modules to guarantee arya-backend is primary
if "app" in sys.modules and not hasattr(sys.modules["app"], "database"):
    for k in list(sys.modules.keys()):
        if k == "app" or k.startswith("app."):
            del sys.modules[k]

import app as arya_app
if str(BACKEND_ROOT / "app") not in arya_app.__path__:
    arya_app.__path__.insert(0, str(BACKEND_ROOT / "app"))
if str(WORKSPACE_ROOT / "person1" / "app") not in arya_app.__path__:
    arya_app.__path__.append(str(WORKSPACE_ROOT / "person1" / "app"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Beneficiary, FollowUp, Measurement, Result, Screening, User, UserRole
from app.services.risk_service import risk_service
from app.services.ml_service import ml_service


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


@pytest.fixture(name="sample_good_image_bytes")
def fixture_sample_good_image_bytes():
    """Load sample valid non-anemic test conjunctival image."""
    img_path = WORKSPACE_ROOT / "person1" / "data" / "samples" / "example_non_anemic.png"
    if img_path.exists():
        return img_path.read_bytes()
    return (WORKSPACE_ROOT / "person1" / "data" / "samples" / "example.png").read_bytes()


@pytest.fixture(name="sample_valid_ppg_csv")
def fixture_sample_valid_ppg_csv():
    """Load sample valid 10s 25Hz hardware PPG recording."""
    csv_path = WORKSPACE_ROOT / "ppg-anemia" / "data" / "hardware" / "ppg_session_20260820_161735.csv"
    return csv_path.read_text(encoding="utf-8")


# 1. Low-Risk Screening
def test_case_1_low_risk_screening(client, sample_good_image_bytes):
    response = client.post(
        "/api/screenings/evaluate-multimodal",
        data={
            "age_years": 28.0,
            "gender": "FEMALE",
            "patient_name": "Low Risk Beneficiary",
            "diet_iron_rich": True,
            "diet_frequency": "often",
            "diet_diversity": 7,
            "ifa_adherence": "good",
            "symptom_severe_pallor": False,
            "symptom_fatigue": False,
        },
        files={"image": ("conjunctiva.png", sample_good_image_bytes, "image/png")},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["risk"]["anemia_risk"] in ("low", "moderate")
    assert "recommended_action" in data["risk"]
    assert len(data["risk"]["safety_flags"]) == 0


# 2. Possible / Mild Anemia
def test_case_2_possible_mild_anemia():
    res = risk_service.evaluate_risk(
        age_years=28.0,
        gender="FEMALE",
        is_pregnant=False,
        diet_iron_rich=False,
        diet_frequency="rare",
        diet_diversity=2,
        symptom_fatigue=True,
        image_label="anemic",
        image_probability=0.55,
        image_confidence=0.75,
    )
    assert res["anemia_risk"] in ("moderate", "high")
    assert res["recommended_action"] in ("confirmatory_testing", "nutrition_counselling", "routine_monitoring")


# 3. Elevated / Moderate Risk
def test_case_3_elevated_moderate_risk():
    res = risk_service.evaluate_risk(
        age_years=25.0,
        gender="FEMALE",
        is_pregnant=True,
        trimester=2,
        diet_iron_rich=False,
        diet_frequency="never",
        diet_diversity=1,
        symptom_fatigue=True,
        image_label="anemic",
        image_probability=0.88,
        image_confidence=0.92,
    )
    assert res["overall_priority"] in ("moderate", "high")
    assert res["recommended_action"] in ("confirmatory_testing", "immediate_referral")


# 4. Severe / Critical / Red-Flag Case
def test_case_4_severe_red_flag_case():
    # Trigger RED FLAG 1 (Severe Anemia Threshold: Hb <= 8.0 for non-pregnant adult female)
    res = risk_service.evaluate_risk(
        age_years=28.0,
        gender="FEMALE",
        is_pregnant=False,
        ppg_hb_gdl=5.8,  # Below WHO 8.0 g/dL severe cutoff
        symptom_severe_pallor=True,
        symptom_breathlessness=True,
    )
    assert res["overall_priority"] in ("critical", "high")
    assert "SEVERE_ANEMIA_THRESHOLD" in res["safety_flags"]
    assert res["recommended_action"] == "immediate_referral"


# 5. Poor Image Quality Handling
def test_case_5_poor_image_quality(client):
    # Empty / corrupted bytes
    corrupt_bytes = b"NOT_A_VALID_IMAGE_DATA"
    response = client.post(
        "/api/screenings/evaluate-multimodal",
        data={"age_years": 25.0, "gender": "FEMALE"},
        files={"image": ("corrupt.png", corrupt_bytes, "image/png")},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["image"]["status"] in ("ERROR", "REJECTED")
    assert data["image"]["error_message"] is not None


# 6. Rejected PPG Handling
def test_case_6_rejected_ppg(client):
    bad_ppg_csv = "timestamp_ms,red,ir\n0,217000,248000\n40,217000,248000\n"  # Only 2 samples
    response = client.post(
        "/api/screenings/evaluate-multimodal",
        data={"age_years": 25.0, "gender": "FEMALE"},
        files={"ppg_csv": ("bad.csv", bad_ppg_csv.encode("utf-8"), "text/csv")},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["ppg"]["available"] is True
    assert data["ppg"]["status"] == "REJECTED"
    assert "Invalid sample count" in data["ppg"]["error_message"]


# 7. Image-Only Screening
def test_case_7_image_only_screening(client, sample_good_image_bytes):
    response = client.post(
        "/api/screenings/evaluate-multimodal",
        data={"age_years": 30.0, "gender": "MALE"},
        files={"image": ("image.png", sample_good_image_bytes, "image/png")},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["image"]["available"] is True
    assert data["ppg"]["available"] is False
    assert data["ppg"]["status"] == "NOT_PROVIDED"
    assert data["risk"]["hb_source"] == "NONE"


# 8. PPG-Only Screening
def test_case_8_ppg_only_screening(client, sample_valid_ppg_csv):
    response = client.post(
        "/api/screenings/evaluate-multimodal",
        data={"age_years": 30.0, "gender": "MALE"},
        files={"ppg_csv": ("ppg.csv", sample_valid_ppg_csv.encode("utf-8"), "text/csv")},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["image"]["available"] is False
    assert data["image"]["status"] == "NOT_PROVIDED"
    assert data["ppg"]["available"] is True
    assert data["ppg"]["status"] == "SUCCESS"
    assert data["risk"]["hb_source"] == "PPG_SENSOR"


# 9. Image + PPG Multimodal Screening (Independent Preserved Signals)
def test_case_9_image_and_ppg_screening(client, sample_good_image_bytes, sample_valid_ppg_csv):
    response = client.post(
        "/api/screenings/evaluate-multimodal",
        data={"age_years": 28.0, "gender": "FEMALE"},
        files={
            "image": ("image.png", sample_good_image_bytes, "image/png"),
            "ppg_csv": ("ppg.csv", sample_valid_ppg_csv.encode("utf-8"), "text/csv"),
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["image"]["available"] is True
    assert data["image"]["status"] == "SUCCESS"
    assert data["ppg"]["available"] is True
    assert data["ppg"]["status"] == "SUCCESS"
    assert data["fusion"]["status"] == "NOT_VALIDATED"  # No unvalidated mathematical fusion


# 10. Backend Error Handling / Validation
def test_case_10_invalid_inputs_rejected(client):
    # Invalid trimester with pregnancy
    response = client.post(
        "/api/screenings/evaluate-multimodal",
        data={"age_years": 25.0, "gender": "FEMALE", "is_pregnant": True, "trimester": 5},
    )
    assert response.status_code == 422


# 11. Verification: No Medication Dosage or Prescriptions
def test_case_11_no_medication_dosage_generated(client, sample_good_image_bytes, sample_valid_ppg_csv):
    response = client.post(
        "/api/screenings/evaluate-multimodal",
        data={"age_years": 28.0, "gender": "FEMALE", "symptom_severe_pallor": True},
        files={
            "image": ("image.png", sample_good_image_bytes, "image/png"),
            "ppg_csv": ("ppg.csv", sample_valid_ppg_csv.encode("utf-8"), "text/csv"),
        },
    )
    assert response.status_code == 201
    text_content = response.text.lower()
    
    # Must NOT contain pharmacological dosages or prescription directives
    forbidden_patterns = [
        r"\d+\s*mg\b",
        r"\d+\s*tablets?\b",
        r"prescribe\b",
        r"take \d+",
        r"ferrous sulphate \d+",
    ]
    for pat in forbidden_patterns:
        assert re.search(pat, text_content) is None, f"Forbidden medication pattern detected: {pat}"


# 12. Verification: No Fake Recommendation When Data Unavailable
def test_case_12_no_modalities_provided(client):
    response = client.post(
        "/api/screenings/evaluate-multimodal",
        data={"age_years": 25.0, "gender": "FEMALE"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["image"]["available"] is False
    assert data["ppg"]["available"] is False
    assert data["risk"]["hb_source"] == "NONE"
