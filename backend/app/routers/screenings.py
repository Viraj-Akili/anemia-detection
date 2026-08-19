from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import (
    create_screening,
    get_screening,
    list_screenings_for_beneficiary,
)
from app.schemas import ScreeningCreate, ScreeningRead

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