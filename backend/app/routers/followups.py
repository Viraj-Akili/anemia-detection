from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import (
    create_followup,
    get_followup,
    list_followups,
)
from app.schemas import FollowUpCreate, FollowUpRead

router = APIRouter(prefix="/api/followups", tags=["followups"])


@router.post("", response_model=FollowUpRead, status_code=status.HTTP_201_CREATED)
def create_followup_endpoint(
    followup_in: FollowUpCreate,
    db: Session = Depends(get_db),
) -> FollowUpRead:
    """Create a new follow-up."""
    followup = create_followup(
        db,
        beneficiary_id=followup_in.beneficiary_id,
        screening_id=followup_in.screening_id,
        assigned_user_id=followup_in.assigned_user_id,
        due_date=followup_in.due_date,
        reason=followup_in.reason,
        status=followup_in.status,
        notes=followup_in.notes,
    )
    return followup


@router.get("", response_model=list[FollowUpRead])
def list_followups_endpoint(
    skip: int = 0,
    limit: int = 100,
    beneficiary_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
) -> list[FollowUpRead]:
    """List follow-ups with optional filtering."""
    return list_followups(
        db, skip=skip, limit=limit, beneficiary_id=beneficiary_id, status=status
    )


@router.get("/{followup_id}", response_model=FollowUpRead)
def get_followup_endpoint(
    followup_id: int,
    db: Session = Depends(get_db),
) -> FollowUpRead:
    """Get a follow-up by ID."""
    followup = get_followup(db, followup_id)
    if not followup:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    return followup