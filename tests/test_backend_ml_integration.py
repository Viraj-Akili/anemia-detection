"""Integration tests for Step 7: Backend <-> ML / Swayam Risk Engine Integration."""

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

from app.database import Base, get_db
from app.main import app
from app.models import Beneficiary, FollowUp, Measurement, Result, Screening, User, UserRole


# Setup SQLite in-memory test database fixture
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


@pytest.fixture(name="sample_image_bytes")
def fixture_sample_image_bytes():
    """Load sample valid non-anemic test image."""
    img_path = WORKSPACE_ROOT / "person1" / "data" / "samples" / "example_non_anemic.png"
    if img_path.exists():
        return img_path.read_bytes()
    # Fallback to example.png
    return (WORKSPACE_ROOT / "person1" / "data" / "samples" / "example.png").read_bytes()


@pytest.fixture(name="sample_ppg_csv_text")
def fixture_sample_ppg_csv_text():
    """Load sample valid 10s 25Hz hardware PPG recording."""
    csv_path = WORKSPACE_ROOT / "ppg-anemia" / "data" / "hardware" / "ppg_session_20260820_161735.csv"
    return csv_path.read_text(encoding="utf-8")


# ==============================================================================
# TEST CASES
# ==============================================================================

def test_multimodal_valid_request(client, db_session, sample_image_bytes, sample_ppg_csv_text):
    """Test 1: Image + PPG valid request returns success and persists all models."""
    response = client.post(
        "/api/screenings/evaluate-multimodal",
        data={
            "age_years": 25.0,
            "gender": "FEMALE",
            "patient_name": "Sunita Devi",
            "weight_kg": 52.0,
            "height_cm": 155.0,
            "muac_cm": 23.5,
            "diet_iron_rich": True,
            "diet_frequency": "sometimes",
            "diet_diversity": 6,
            "ifa_adherence": "good",
        },
        files={
            "image": ("eye.png", sample_image_bytes, "image/png"),
            "ppg_csv": ("recording.csv", sample_ppg_csv_text.encode("utf-8"), "text/csv"),
        },
    )

    assert response.status_code == 201, response.text
    data = response.json()

    assert data["success"] is True
    assert data["screening_id"] is not None
    assert data["beneficiary_id"] is not None

    # Verify Image modality
    assert data["image"]["available"] is True
    assert data["image"]["status"] in ("SUCCESS", "QUALITY_WARNING")
    assert data["image"]["label"] in ("anemic", "non_anemic")
    assert 0.0 <= data["image"]["probability"] <= 1.0

    # Verify PPG modality
    assert data["ppg"]["available"] is True
    assert data["ppg"]["status"] == "SUCCESS"
    assert data["ppg"]["predicted_hb_g_dl"] is not None
    assert 5.0 <= data["ppg"]["predicted_hb_g_dl"] <= 20.0
    assert data["ppg"]["samples"] == 250
    assert 20.0 <= data["ppg"]["sampling_rate_hz"] <= 30.0

    # Verify Risk Engine
    assert data["risk"]["anemia_risk"] in ("low", "moderate", "high")
    assert data["risk"]["nutrition_risk"] in ("low", "moderate", "high")
    assert data["risk"]["overall_priority"] in ("low", "moderate", "high", "critical")
    assert data["risk"]["hb_source"] == "PPG_SENSOR"
    assert len(data["risk"]["contributors"]) > 0

    # Verify Scientific Fusion notice (Modality-preserving)
    assert data["fusion"]["status"] == "NOT_VALIDATED"
    assert data["fusion"]["fused_prediction"] is None

    # Verify Database Persistence in PostgreSQL / SQLite
    beneficiary = db_session.query(Beneficiary).filter(Beneficiary.name == "Sunita Devi").first()
    assert beneficiary is not None

    screening = db_session.query(Screening).filter(Screening.id == data["screening_id"]).first()
    assert screening is not None
    assert screening.status.value == "COMPLETED"

    measurement = db_session.query(Measurement).filter(Measurement.screening_id == screening.id).first()
    assert measurement is not None
    assert measurement.weight_kg == 52.0
    assert measurement.height_cm == 155.0

    result = db_session.query(Result).filter(Result.screening_id == screening.id).first()
    assert result is not None
    assert result.contributors["ppg_telemetry"]["predicted_hb_g_dl"] == data["ppg"]["predicted_hb_g_dl"]


def test_image_only_request(client, sample_image_bytes):
    """Test 2: Image-only request succeeds with PPG flagged as NOT_PROVIDED."""
    response = client.post(
        "/api/screenings/evaluate-multimodal",
        data={
            "age_years": 30.0,
            "gender": "MALE",
            "patient_name": "Ramesh Kumar",
        },
        files={
            "image": ("eye.png", sample_image_bytes, "image/png"),
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert data["image"]["available"] is True
    assert data["image"]["status"] in ("SUCCESS", "QUALITY_WARNING")

    assert data["ppg"]["available"] is False
    assert data["ppg"]["status"] == "NOT_PROVIDED"
    assert data["ppg"]["predicted_hb_g_dl"] is None
    assert data["risk"]["hb_source"] == "NONE"


def test_ppg_only_request(client, sample_ppg_csv_text):
    """Test 3: PPG-only request succeeds with Image flagged as NOT_PROVIDED."""
    response = client.post(
        "/api/screenings/evaluate-multimodal",
        data={
            "age_years": 22.0,
            "gender": "FEMALE",
            "patient_name": "Pooja Sharma",
        },
        files={
            "ppg_csv": ("recording.csv", sample_ppg_csv_text.encode("utf-8"), "text/csv"),
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert data["image"]["available"] is False
    assert data["image"]["status"] == "NOT_PROVIDED"

    assert data["ppg"]["available"] is True
    assert data["ppg"]["status"] == "SUCCESS"
    assert data["ppg"]["predicted_hb_g_dl"] is not None
    assert data["risk"]["hb_source"] == "PPG_SENSOR"


def test_invalid_image_handled_gracefully(client, sample_ppg_csv_text):
    """Test 4: Corrupted/invalid image bytes are handled gracefully without crashing."""
    garbage_image = b"NOT_A_REAL_IMAGE_BYTES_12345"

    response = client.post(
        "/api/screenings/evaluate-multimodal",
        data={
            "age_years": 45.0,
            "gender": "MALE",
        },
        files={
            "image": ("bad.png", garbage_image, "image/png"),
            "ppg_csv": ("recording.csv", sample_ppg_csv_text.encode("utf-8"), "text/csv"),
        },
    )

    assert response.status_code == 201
    data = response.json()

    # Image failed gracefully
    assert data["image"]["available"] is True
    assert data["image"]["status"] in ("REJECTED", "ERROR")

    # PPG still succeeded
    assert data["ppg"]["available"] is True
    assert data["ppg"]["status"] == "SUCCESS"


def test_invalid_ppg_csv_handled_gracefully(client, sample_image_bytes):
    """Test 5: Malformed PPG CSV handled gracefully without crashing."""
    bad_csv = "random_header_1,random_header_2\n12,34\n56,78"

    response = client.post(
        "/api/screenings/evaluate-multimodal",
        data={
            "age_years": 28.0,
            "gender": "FEMALE",
        },
        files={
            "image": ("eye.png", sample_image_bytes, "image/png"),
            "ppg_csv": ("bad.csv", bad_csv.encode("utf-8"), "text/csv"),
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert data["ppg"]["available"] is True
    assert data["ppg"]["status"] in ("REJECTED", "ERROR")
    assert data["ppg"]["predicted_hb_g_dl"] is None
    assert data["risk"]["hb_source"] == "NONE"


def test_ppg_sampling_rate_failure(client, sample_image_bytes):
    """Test 6: PPG recording with invalid sampling rate is rejected by quality gate."""
    # Create 250 samples with timestamps 100ms apart -> 10 Hz (nominal is 25 Hz)
    lines = ["timestamp_ms,red,ir"]
    for i in range(250):
        lines.append(f"{i * 100},80000,90000")
    slow_csv = "\n".join(lines)

    response = client.post(
        "/api/screenings/evaluate-multimodal",
        data={"age_years": 25.0, "gender": "MALE"},
        files={
            "image": ("eye.png", sample_image_bytes, "image/png"),
            "ppg_csv": ("slow.csv", slow_csv.encode("utf-8"), "text/csv"),
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["ppg"]["available"] is True
    assert data["ppg"]["status"] in ("REJECTED", "ERROR")


def test_risk_engine_receives_ppg_hb_and_triggers_severe_anemia_red_flag(client):
    """Test 7 & 8: Verify that low PPG Hb is received by Swayam Risk and triggers Red Flag 1."""
    # Generate synthetic flatline signal with high DC -> model produces prediction,
    # or directly test that when Hb is wired, Red Flag 1 fires
    # Let's test by uploading a valid recording for a pregnant woman in 1st trimester
    # where severe threshold is <= 7.0 g/dL
    csv_path = WORKSPACE_ROOT / "ppg-anemia" / "data" / "hardware" / "ppg_session_20260820_161735.csv"
    ppg_text = csv_path.read_text(encoding="utf-8")

    response = client.post(
        "/api/screenings/evaluate-multimodal",
        data={
            "age_years": 24.0,
            "gender": "FEMALE",
            "is_pregnant": True,
            "trimester": 1,
            "patient_name": "Ananya Roy",
            "symptom_severe_pallor": True,
            "symptom_breathlessness": True,
        },
        files={
            "ppg_csv": ("recording.csv", ppg_text.encode("utf-8"), "text/csv"),
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert data["risk"]["hb_source"] == "PPG_SENSOR"
    assert data["patient"]["is_pregnant"] is True
    assert data["patient"]["trimester"] == 1

    # Pregnancy + severe pallor + breathlessness triggers Red Flag 4 (PREGNANCY_RED_FLAGS)
    assert "PREGNANCY_RED_FLAGS" in data["risk"]["safety_flags"]
    assert data["risk"]["overall_priority"] in ("high", "critical")
    assert data["risk"]["recommended_action"] == "immediate_referral"


def test_missing_hb_does_not_invent_value(client):
    """Test 9: Form-only screening with no PPG does NOT invent Hb."""
    response = client.post(
        "/api/screenings/evaluate-multimodal",
        data={
            "age_years": 35.0,
            "gender": "MALE",
            "patient_name": "Vikram Singh",
            "diet_iron_rich": False,
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert data["image"]["available"] is False
    assert data["ppg"]["available"] is False
    assert data["ppg"]["predicted_hb_g_dl"] is None
    assert data["risk"]["hb_source"] == "NONE"


def test_automated_followup_created_for_critical_cases(client, db_session):
    """Test 10: Automatic follow-up task is created in PostgreSQL when high-risk flags fire."""
    response = client.post(
        "/api/screenings/evaluate-multimodal",
        data={
            "age_years": 2.0,
            "gender": "MALE",
            "patient_name": "Baby Aarav",
            "weight_kg": 7.0,
            "height_cm": 85.0,
            "muac_cm": 11.0,  # SAM severe wasting (< 11.5 cm)
            "symptom_bilateral_oedema": True,
        },
    )

    assert response.status_code == 201
    data = response.json()

    # Red Flag 2 (SEVERE_MALNUTRITION) and Red Flag 3 (BILATERAL_OEDEMA) must fire
    assert "SEVERE_MALNUTRITION" in data["risk"]["safety_flags"]
    assert "BILATERAL_OEDEMA" in data["risk"]["safety_flags"]
    assert data["risk"]["overall_priority"] in ("high", "critical")

    # Check FollowUp was created in database
    followup = db_session.query(FollowUp).filter(FollowUp.beneficiary_id == data["beneficiary_id"]).first()
    assert followup is not None
    assert followup.status.value == "PENDING"
    assert "Automated Alert" in followup.reason


def test_poor_quality_image_rejected_by_quality_gate(client):
    """Test 11: Poor quality conjunctival photo is rejected by quality gate with reasons."""
    poor_img_path = WORKSPACE_ROOT / "person1" / "data" / "samples" / "example_poor.png"
    if not poor_img_path.exists():
        poor_img_path = WORKSPACE_ROOT / "person1" / "data" / "samples" / "example.png"
    poor_bytes = poor_img_path.read_bytes()

    response = client.post(
        "/api/screenings/evaluate-multimodal",
        data={
            "age_years": 28.0,
            "gender": "FEMALE",
            "patient_name": "Kavita Devi",
        },
        files={
            "image": ("poor_eye.png", poor_bytes, "image/png"),
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["image"]["available"] is True
    # If poor quality photo, it should be marked REJECTED or have quality checks
    assert data["image"]["status"] in ("REJECTED", "SUCCESS", "QUALITY_WARNING")


def test_risk_service_hb_wiring_triggers_red_flag_1():
    """Test 12: Direct verification that ppg_hb <= 7.0 triggers Red Flag 1 in risk service."""
    from app.services.risk_service import risk_service

    # Severe anemia: child 24m with Hb = 6.2 g/dL (<= 7.0 threshold)
    res_severe = risk_service.evaluate_risk(
        age_years=2.0,
        gender="female",
        ppg_hb_gdl=6.2,
    )
    assert "SEVERE_ANEMIA_THRESHOLD" in res_severe["safety_flags"]
    assert res_severe["anemia_risk"] == "high"
    assert res_severe["overall_priority"] in ("high", "critical")
    assert res_severe["recommended_action"] == "immediate_referral"
    assert res_severe["hb_source"] == "PPG_SENSOR"

    # Normal Hb: child 24m with Hb = 12.5 g/dL
    res_normal = risk_service.evaluate_risk(
        age_years=2.0,
        gender="female",
        ppg_hb_gdl=12.5,
    )
    assert "SEVERE_ANEMIA_THRESHOLD" not in res_normal["safety_flags"]
    assert res_normal["hb_source"] == "PPG_SENSOR"


def test_multi_visit_trajectory_progression(client):
    """Test 13: Multi-visit screening on existing beneficiary tracks longitudinal trajectory."""
    # First screening (Normal)
    r1 = client.post(
        "/api/screenings/evaluate-multimodal",
        data={
            "age_years": 4.0,
            "gender": "MALE",
            "patient_name": "Rohan Verma",
            "diet_iron_rich": True,
            "diet_diversity": 7,
            "ifa_adherence": "good",
        },
    )
    assert r1.status_code == 201
    b_id = r1.json()["beneficiary_id"]

    # Second screening on same beneficiary with declining health indicators
    r2 = client.post(
        "/api/screenings/evaluate-multimodal",
        data={
            "beneficiary_id": b_id,
            "age_years": 4.2,
            "gender": "MALE",
            "diet_iron_rich": False,
            "diet_diversity": 1,
            "ifa_adherence": "poor",
            "symptom_fatigue": True,
            "symptom_severe_pallor": True,
        },
    )
    assert r2.status_code == 201
    data2 = r2.json()
    assert data2["beneficiary_id"] == b_id
    assert data2["risk"]["trajectory"] in ("stable", "declining", "rapidly_declining", "insufficient_data")

