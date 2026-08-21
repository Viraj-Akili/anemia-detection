from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models import Beneficiary, User


def create_beneficiary(
    db: Session,
    *,
    name: str,
    date_of_birth: str,
    sex: str,
    category: str,
    created_by_id: int,
    is_pregnant: bool = False,
    trimester: int | None = None,
) -> Beneficiary:
    """Create a new beneficiary record."""
    beneficiary = Beneficiary(
        name=name,
        date_of_birth=date_of_birth,
        sex=sex,
        category=category,
        is_pregnant=is_pregnant,
        trimester=trimester,
        created_by_id=created_by_id,
    )
    db.add(beneficiary)
    db.commit()
    db.refresh(beneficiary)
    return beneficiary


def get_beneficiary(db: Session, beneficiary_id: int) -> Beneficiary | None:
    """Get a beneficiary by ID."""
    return db.query(Beneficiary).filter(Beneficiary.id == beneficiary_id).first()


def list_beneficiaries(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 100,
    category: str | None = None,
) -> list[Beneficiary]:
    """List beneficiaries with optional filtering."""
    query = db.query(Beneficiary)
    if category:
        query = query.filter(Beneficiary.category == category)
    return query.order_by(desc(Beneficiary.created_at)).offset(skip).limit(limit).all()