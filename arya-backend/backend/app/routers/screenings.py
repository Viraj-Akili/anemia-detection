import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import (
    create_screening,
    get_screening,
    list_screenings_for_beneficiary,
)
from app.schemas import MultimodalEvaluationResponse, ScreeningCreate, ScreeningRead
from app.services import screening_orchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/screenings", tags=["screenings"])


@router.post("", response_model=ScreeningRead, status_code=status.HTTP_201_CREATED)
def create_screening_endpoint(
    screening_in: ScreeningCreate,
    db: Session = Depends(get_db),
) -> ScreeningRead:
    """Create a new screening."""
    screening = create_screening(
        db,
        beneficiary_id=screening_in.beneficiary_id,
        worker_id=screening_in.worker_id,
        started_at=screening_in.started_at,
        status=screening_in.status,
        device_id=screening_in.device_id,
    )
    return screening


@router.get("/{screening_id}", response_model=ScreeningRead)
def get_screening_endpoint(
    screening_id: int,
    db: Session = Depends(get_db),
) -> ScreeningRead:
    """Get a screening by ID."""
    screening = get_screening(db, screening_id)
    if not screening:
        raise HTTPException(status_code=404, detail="Screening not found")
    return screening


@router.get("/beneficiary/{beneficiary_id}", response_model=list[ScreeningRead])
def list_screenings_for_beneficiary_endpoint(
    beneficiary_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[ScreeningRead]:
    """List screenings for a beneficiary."""
    return list_screenings_for_beneficiary(db, beneficiary_id, skip=skip, limit=limit)


@router.post(
    "/evaluate-multimodal",
    response_model=MultimodalEvaluationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Execute end-to-end multimodal screening with Image & PPG ML, Swayam Risk Engine, and DB persistence",
)
async def evaluate_multimodal_endpoint(
    age_years: float = Form(..., description="Patient age in years (e.g. 2.5 or 28)"),
    gender: str = Form(..., description="Biological sex ('MALE' / 'FEMALE')"),
    beneficiary_id: Optional[int] = Form(None, description="Existing beneficiary ID if registered"),
    patient_name: Optional[str] = Form(None, description="Patient name if creating new beneficiary"),
    worker_id: int = Form(1, description="Assigned frontline health worker ID"),
    is_pregnant: bool = Form(False, description="Whether patient is currently pregnant"),
    trimester: Optional[int] = Form(None, description="Pregnancy trimester (1, 2, or 3) if pregnant"),
    weight_kg: Optional[float] = Form(None, description="Weight in kg"),
    height_cm: Optional[float] = Form(None, description="Height in cm"),
    muac_cm: Optional[float] = Form(None, description="Mid-Upper Arm Circumference in cm"),
    diet_iron_rich: bool = Form(False, description="Iron rich food intake yesterday"),
    diet_frequency: str = Form("never", description="Iron rich food frequency: never|rare|sometimes|often"),
    diet_diversity: int = Form(0, description="Dietary diversity score (0-9 food groups)"),
    ifa_adherence: str = Form("unknown", description="IFA tablet adherence: good|poor|unknown"),
    symptom_severe_pallor: bool = Form(False, description="Clinical severe pallor observed"),
    symptom_breathlessness: bool = Form(False, description="Breathlessness at rest or exertion"),
    symptom_bilateral_oedema: bool = Form(False, description="Bilateral pitting oedema observed"),
    symptom_fatigue: bool = Form(False, description="Generalized severe fatigue"),
    device_id: Optional[str] = Form("PRAHARI_MOBILE_POC", description="Device / sensor identifier"),
    image: Optional[UploadFile] = File(None, description="Conjunctival image file (PNG/JPG/HEIC)"),
    ppg_csv: Optional[UploadFile] = File(None, description="MAX30102 25Hz CSV file (timestamp_ms,red,ir)"),
    db: Session = Depends(get_db),
) -> MultimodalEvaluationResponse:
    """Execute end-to-end point-of-care screening:
    1. Evaluates Image/CV model on conjunctiva image (with blur/lighting quality gate).
    2. Evaluates PPG model on 25Hz 10-second MAX30102 CSV (extracts Hb & SQI).
    3. Preserves independent telemetry outputs (no unvalidated statistical fusion).
    4. Evaluates Swayam Risk Engine & WHO deterministic safety rules (wires PPG Hb into Red Flag 1).
    5. Persists encounter, measurements, and results into PostgreSQL.
    6. Returns unified multimodal screening response.
    """
    image_bytes = await image.read() if image else None
    ppg_csv_text = (await ppg_csv.read()).decode("utf-8", errors="replace") if ppg_csv else None

    # Enforce pregnancy trimester requirement if pregnant
    if is_pregnant and trimester not in (1, 2, 3):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Trimester (1, 2, or 3) is required when is_pregnant is True",
        )

    try:
        response = screening_orchestrator.process_screening(
            db=db,
            beneficiary_id=beneficiary_id,
            patient_name=patient_name,
            worker_id=worker_id,
            age_years=age_years,
            gender=gender,
            is_pregnant=is_pregnant,
            trimester=trimester,
            weight_kg=weight_kg,
            height_cm=height_cm,
            muac_cm=muac_cm,
            diet_iron_rich=diet_iron_rich,
            diet_frequency=diet_frequency,
            diet_diversity=diet_diversity,
            ifa_adherence=ifa_adherence,
            symptom_severe_pallor=symptom_severe_pallor,
            symptom_breathlessness=symptom_breathlessness,
            symptom_bilateral_oedema=symptom_bilateral_oedema,
            symptom_fatigue=symptom_fatigue,
            image_bytes=image_bytes,
            image_filename=image.filename if image else None,
            ppg_csv_text=ppg_csv_text,
            ppg_filename=ppg_csv.filename if ppg_csv else None,
            device_id=device_id,
        )
        return response
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Screening evaluation error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal screening evaluation error: {str(exc)}",
        )