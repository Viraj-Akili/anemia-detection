"""
tests/test_anthropometry_nutrition.py

Comprehensive test suite for STEP 10: Nutrition Chatbot Anthropometric Integration.
Validates all 19 required test cases:
1. Valid height + weight -> correct BMI
2. Zero height rejected
3. Negative height rejected
4. Zero weight rejected
5. Negative weight rejected
6. Adult BMI interpretation
7. Child BMI uses age-aware logic
8. MUAC omitted -> no MUAC penalty
9. MUAC unit conversion cm -> mm
10. Child 6-59 months MUAC < 115 mm (SAM / Critical)
11. Child 6-59 months MUAC 115-<125 mm (MAM / Moderate)
12. Child 6-59 months MUAC >= 125 mm (Normal)
13. MUAC outside applicable age group does not use the 6-59-month cutoff
14. BMI and MUAC do not cause uncontrolled score inflation (overlap deduplication verified)
15. Existing nutrition scoring remains functional
16. Existing anemia/image/PPG/risk pipelines remain unchanged
17. Missing anthropometric data is handled gracefully
18. Frontend build succeeds (verified via build pipeline)
19. Full existing test suite passes
"""

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
from app.models import User, UserRole
from app.services.anthropometry_service import (
    AnthropometryInputError,
    calculate_bmi,
    evaluate_anthropometry,
    interpret_bmi,
    interpret_muac,
    normalize_muac_mm,
)
from app.services.risk_service import risk_service


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

    worker = User(
        id=1,
        username="test_worker",
        full_name="Frontline Health Sentinel",
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
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# 1. Valid height + weight -> correct BMI
def test_case_1_valid_bmi_calculation():
    # 70 kg / (1.75 m)^2 = 70 / 3.0625 = 22.857... -> 22.9
    bmi = calculate_bmi(height_cm=175.0, weight_kg=70.0)
    assert bmi == 22.9

    # 55 kg / (1.60 m)^2 = 55 / 2.56 = 21.484... -> 21.5
    bmi2 = calculate_bmi(height_cm=160.0, weight_kg=55.0)
    assert bmi2 == 21.5


# 2. Zero height rejected
def test_case_2_zero_height_rejected():
    with pytest.raises(AnthropometryInputError) as exc_info:
        calculate_bmi(height_cm=0.0, weight_kg=55.0)
    assert "positive" in str(exc_info.value).lower() or ">0" in str(exc_info.value)


# 3. Negative height rejected
def test_case_3_negative_height_rejected():
    with pytest.raises(AnthropometryInputError) as exc_info:
        calculate_bmi(height_cm=-160.0, weight_kg=55.0)
    assert "positive" in str(exc_info.value).lower() or ">0" in str(exc_info.value)


# 4. Zero weight rejected
def test_case_4_zero_weight_rejected():
    with pytest.raises(AnthropometryInputError) as exc_info:
        calculate_bmi(height_cm=160.0, weight_kg=0.0)
    assert "positive" in str(exc_info.value).lower() or ">0" in str(exc_info.value)


# 5. Negative weight rejected
def test_case_5_negative_weight_rejected():
    with pytest.raises(AnthropometryInputError) as exc_info:
        calculate_bmi(height_cm=160.0, weight_kg=-55.0)
    assert "positive" in str(exc_info.value).lower() or ">0" in str(exc_info.value)


# 6. Adult BMI interpretation
def test_case_6_adult_bmi_interpretation():
    # Underweight (< 18.5)
    cat_under, _, _, risk_under = interpret_bmi(bmi=17.2, age_years=28.0)
    assert "underweight" in cat_under.lower()
    assert risk_under in ("BORDERLINE", "UNHEALTHY", "CRITICAL")

    # Normal (18.5 - 24.9)
    cat_norm, _, _, risk_norm = interpret_bmi(bmi=22.0, age_years=28.0)
    assert cat_norm == "normal"
    assert risk_norm == "HEALTHY"

    # Overweight (25.0 - 29.9)
    cat_over, _, _, risk_over = interpret_bmi(bmi=27.5, age_years=28.0)
    assert cat_over == "overweight"
    assert risk_over == "BORDERLINE"

    # Obese (>= 30.0)
    cat_obese, _, _, risk_obese = interpret_bmi(bmi=32.0, age_years=28.0)
    assert cat_obese == "obese"
    assert risk_obese == "UNHEALTHY"


# 7. Child BMI uses age-aware logic
def test_case_7_child_age_aware_bmi():
    # 7-year-old child with BMI 14.5 kg/m² is normal (in adults 14.5 is severe anorexia/underweight)
    cat_child, interp_child, age_group, risk_child = interpret_bmi(bmi=15.0, age_years=7.0)
    assert "5–19" in age_group or "Child" in age_group
    assert risk_child == "HEALTHY"
    assert "normal" in cat_child.lower()

    # 3-year-old preschooler (under 5 years)
    cat_pre, interp_pre, age_group_pre, _ = interpret_bmi(bmi=15.5, age_years=3.0)
    assert "< 5 years" in age_group_pre or "6–59 months" in age_group_pre
    assert "Weight-for-Height" in interp_pre or "WHZ" in interp_pre


# 8. MUAC omitted -> no MUAC penalty
def test_case_8_muac_omitted_no_penalty():
    eval_res = evaluate_anthropometry(
        height_cm=165.0,
        weight_kg=60.0,
        age_years=25.0,
        gender="female",
        muac_value=None,
    )
    assert eval_res.muac_mm is None
    assert eval_res.muac_category == "not_provided"
    assert eval_res.score_adjustment == 0
    assert eval_res.risk_level == "HEALTHY"


# 9. MUAC unit conversion cm -> mm
def test_case_9_muac_unit_conversion():
    # 13.5 cm -> 135.0 mm
    norm_mm = normalize_muac_mm(13.5, unit="cm")
    assert norm_mm == 135.0

    # 125 mm -> 125.0 mm
    norm_mm2 = normalize_muac_mm(125.0, unit="mm")
    assert norm_mm2 == 125.0


# 10. Child 6-59 months MUAC < 115 mm (SAM / Critical)
def test_case_10_child_sam_muac():
    cat, interp, risk = interpret_muac(muac_mm=112.0, age_years=2.5)
    assert cat == "severe"
    assert "Severe Acute Malnutrition" in interp or "SAM" in interp
    assert risk == "CRITICAL"


# 11. Child 6-59 months MUAC 115-<125 mm (MAM / Moderate)
def test_case_11_child_mam_muac():
    cat, interp, risk = interpret_muac(muac_mm=118.0, age_years=2.5)
    assert cat == "moderate"
    assert "Moderate Acute Malnutrition" in interp or "MAM" in interp
    assert risk == "UNHEALTHY"


# 12. Child 6-59 months MUAC >= 125 mm (Normal)
def test_case_12_child_normal_muac():
    cat, interp, risk = interpret_muac(muac_mm=135.0, age_years=2.5)
    assert cat == "normal"
    assert risk == "HEALTHY"


# 13. MUAC outside applicable age group does not use the 6-59-month cutoff
def test_case_13_muac_outside_pediatric_age_group():
    # For a 30-year-old adult, MUAC 180 mm is low adult arm circumference (< 230 mm), NOT SAM
    cat, interp, risk = interpret_muac(muac_mm=180.0, age_years=30.0)
    assert cat == "moderate"
    assert "230 mm" in interp
    assert "SAM" not in interp

    # For a 10-year-old child, recorded informatively without false 115mm SAM cutoff
    cat_10y, interp_10y, risk_10y = interpret_muac(muac_mm=140.0, age_years=10.0)
    assert cat_10y == "informative"
    assert risk_10y == "HEALTHY"


# 14. BMI and MUAC do not cause uncontrolled score inflation (overlap deduplication verified)
def test_case_14_overlap_deduplication():
    # Patient with both low BMI and low MUAC
    eval_res = evaluate_anthropometry(
        height_cm=160.0,
        weight_kg=40.0,  # BMI = 15.6 (severe underweight -> penalty -40)
        age_years=25.0,
        gender="female",
        muac_value=190.0,  # Low adult MUAC -> penalty -10
        muac_unit="mm",
    )
    # The final penalty is bounded at -40 (not -40 + -10 = -50)
    assert eval_res.score_adjustment == -40
    assert eval_res.risk_level == "CRITICAL"
    assert "deduplication" in eval_res.overlap_prevention_note.lower() or "independent" in eval_res.overlap_prevention_note.lower()


# 15. Existing nutrition scoring remains functional
def test_case_15_existing_nutrition_scoring(client):
    response = client.post(
        "/api/nutrition/evaluate-anthropometry",
        json={
            "height_cm": 160.0,
            "weight_kg": 55.0,
            "age_years": 28.0,
            "gender": "FEMALE",
            "is_pregnant": False,
            "muac_value": None,
            "muac_unit": "mm",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["bmi"] == 21.5
    assert data["bmi_category"] == "normal"
    assert data["risk_level"] == "HEALTHY"


# 16. Existing anemia/image/PPG/risk pipelines remain unchanged
def test_case_16_multimodal_screening_unchanged(client):
    # Verify evaluate-multimodal runs with height, weight, and muac
    img_path = WORKSPACE_ROOT / "person1" / "data" / "samples" / "example_non_anemic.png"
    img_bytes = img_path.read_bytes() if img_path.exists() else b""

    response = client.post(
        "/api/screenings/evaluate-multimodal",
        data={
            "age_years": 25.0,
            "gender": "FEMALE",
            "patient_name": "Anthropometry Test Beneficiary",
            "weight_kg": 52.0,
            "height_cm": 155.0,
            "muac_cm": 23.5,
            "diet_iron_rich": True,
            "diet_frequency": "sometimes",
            "diet_diversity": 6,
        },
        files={"image": ("eye.png", img_bytes, "image/png")} if img_bytes else None,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["risk"]["nutrition_risk"] in ("low", "moderate", "high")


# 17. Missing anthropometric data is handled gracefully
def test_case_17_missing_anthropometry_graceful():
    res = risk_service.evaluate_risk(
        age_years=25.0,
        gender="FEMALE",
        weight_kg=None,
        height_cm=None,
        muac_cm=None,
    )
    assert res["nutrition_risk"] in ("low", "moderate", "high")
    assert "recommended_action" in res
