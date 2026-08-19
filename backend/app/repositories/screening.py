from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models import Screening


def create_screening(
    db: Session,
    *,
    beneficiary_id: int,
    worker_id: int,
    started_at: str,
    status: str = "IN_PROGRESS",
    device_id: str | None = None,
) -> Screening:
    """Create a new screening record."""
    screening = Screening(
        beneficiary_id=beneficiary_id,
        worker_id=worker_id,
        started_at=started_at,
        status=status,
        device_id=device_id,
    )
    db.add(screening)
    db.commit()
    db.refresh(screening)
    return screening


def get_screening(db: Session, screening_id: int) -> Screening | None:
    """Get a screening by ID."""
    return db.query(Screening).filter(Screening.id == screening_id).first()


def list_screenings_for_beneficiary(
    db: Session,
    beneficiary_id: int,
    *,
    skip: int = 0,
    limit: int = 100,
) -> list[Screening]:
    """List screenings for a beneficiary, ordered by started_at descending."""
    return (
        db.query(Screening)
        .filter(Screening.beneficiary_id == beneficiary_id)
        .order_by(desc(Screening.started_at))
        .offset(skip)
        .limit(limit)
        .all()
    )