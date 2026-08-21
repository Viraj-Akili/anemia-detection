from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import (
    create_beneficiary,
    get_beneficiary,
    list_beneficiaries,
)
from app.schemas import BeneficiaryCreate, BeneficiaryRead

router = APIRouter(prefix="/api/beneficiaries", tags=["beneficiaries"])


@router.post("", response_model=BeneficiaryRead, status_code=status.HTTP_201_CREATED)
def create_beneficiary_endpoint(
    beneficiary_in: BeneficiaryCreate,
    db: Session = Depends(get_db),
) -> BeneficiaryRead:
    """Create a new beneficiary."""
    beneficiary = create_beneficiary(
        db,
        name=beneficiary_in.name,
        date_of_birth=beneficiary_in.date_of_birth,
        sex=beneficiary_in.sex,
        category=beneficiary_in.category,
        created_by_id=1,  # TODO: Get from authenticated user
        is_pregnant=beneficiary_in.is_pregnant,
        trimester=beneficiary_in.trimester,
    )
    return beneficiary


@router.get("", response_model=list[BeneficiaryRead])
def list_beneficiaries_endpoint(
    skip: int = 0,
    limit: int = 100,
    category: str | None = None,
    db: Session = Depends(get_db),
) -> list[BeneficiaryRead]:
    """List beneficiaries with optional filtering."""
    return list_beneficiaries(db, skip=skip, limit=limit, category=category)


@router.get("/{beneficiary_id}", response_model=BeneficiaryRead)
def get_beneficiary_endpoint(
    beneficiary_id: int,
    db: Session = Depends(get_db),
) -> BeneficiaryRead:
    """Get a beneficiary by ID."""
    beneficiary = get_beneficiary(db, beneficiary_id)
    if not beneficiary:
        raise HTTPException(status_code=404, detail="Beneficiary not found")
    return beneficiary