from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models import FollowUp


def create_followup(
    db: Session,
    *,
    beneficiary_id: int,
    assigned_user_id: int,
    due_date: str,
    reason: str,
    screening_id: int | None = None,
    status: str = "PENDING",
    notes: str | None = None,
) -> FollowUp:
    """Create a new follow-up record."""
    followup = FollowUp(
        beneficiary_id=beneficiary_id,
        screening_id=screening_id,
        assigned_user_id=assigned_user_id,
        due_date=due_date,
        status=status,
        reason=reason,
        notes=notes,
    )
    db.add(followup)
    db.commit()
    db.refresh(followup)
    return followup


def get_followup(db: Session, followup_id: int) -> FollowUp | None:
    """Get a follow-up by ID."""
    return db.query(FollowUp).filter(FollowUp.id == followup_id).first()


def list_followups(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 100,
    beneficiary_id: int | None = None,
    status: str | None = None,
) -> list[FollowUp]:
    """List follow-ups with optional filtering."""
    query = db.query(FollowUp)
    if beneficiary_id:
        query = query.filter(FollowUp.beneficiary_id == beneficiary_id)
    if status:
        query = query.filter(FollowUp.status == status)
    return query.order_by(desc(FollowUp.due_date)).offset(skip).limit(limit).all()