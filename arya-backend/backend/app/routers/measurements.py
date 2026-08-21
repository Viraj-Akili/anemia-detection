from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import (
    create_measurement,
    get_measurements_for_screening,
)
from app.schemas import MeasurementCreate, MeasurementRead

router = APIRouter(prefix="/api/screenings", tags=["measurements"])


@router.post("/{screening_id}/measurements", response_model=MeasurementRead, status_code=status.HTTP_201_CREATED)
def create_measurement_endpoint(
    screening_id: int,
    measurement_in: MeasurementCreate,
    db: Session = Depends(get_db),
) -> MeasurementRead:
    """Create a new measurement for a screening."""
    measurement = create_measurement(
        db,
        screening_id=screening_id,
        weight_kg=measurement_in.weight_kg,
        height_cm=measurement_in.height_cm,
        muac_mm=measurement_in.muac_mm,
    )
    return measurement


@router.get("/{screening_id}/measurements", response_model=list[MeasurementRead])
def get_measurements_for_screening_endpoint(
    screening_id: int,
    db: Session = Depends(get_db),
) -> list[MeasurementRead]:
    """Get all measurements for a screening."""
    return get_measurements_for_screening(db, screening_id)