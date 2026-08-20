"""Beneficiary CRUD routes — minimal POST and GET for frontend registration.

- POST /api/beneficiaries — register a new beneficiary
- GET /api/beneficiaries/{id} — retrieve beneficiary details
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.deps import get_db
from models.entities import Beneficiary

router = APIRouter(prefix="/beneficiaries", tags=["beneficiaries"])


class BeneficiaryCreate(BaseModel):
    """Request body for POST /api/beneficiaries."""

    id: str = Field(min_length=1, max_length=50, description="Unique beneficiary ID (e.g., B001)")
    name: str | None = Field(default=None, max_length=200, description="Beneficiary name (optional)")
    age_months: int = Field(ge=0, le=1200, description="Age in months (0-100 years)")
    sex: str = Field(pattern="^(male|female)$", description="Sex: male or female")
    pregnancy: bool = Field(default=False, description="Whether the beneficiary is pregnant")


class BeneficiaryResponse(BaseModel):
    """Response body for beneficiary endpoints."""

    id: str
    name: str | None
    age_months: int
    sex: str
    pregnancy: bool
    created_at: str

    model_config = {"from_attributes": True}


@router.post("", response_model=BeneficiaryResponse, status_code=status.HTTP_201_CREATED)
def create_beneficiary(payload: BeneficiaryCreate, db: Session = Depends(get_db)) -> BeneficiaryResponse:
    """Register a new beneficiary."""
    # Check if beneficiary already exists
    existing = db.query(Beneficiary).filter(Beneficiary.id == payload.id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Beneficiary with id '{payload.id}' already exists",
        )

    # Create new beneficiary
    beneficiary = Beneficiary(
        id=payload.id,
        name=payload.name,
        age_months=payload.age_months,
        sex=payload.sex,
        pregnancy=payload.pregnancy,
    )

    db.add(beneficiary)
    db.commit()
    db.refresh(beneficiary)

    return BeneficiaryResponse(
        id=beneficiary.id,
        name=beneficiary.name,
        age_months=beneficiary.age_months,
        sex=beneficiary.sex,
        pregnancy=beneficiary.pregnancy,
        created_at=beneficiary.created_at.isoformat(),
    )


@router.get("/{beneficiary_id}", response_model=BeneficiaryResponse)
def get_beneficiary(beneficiary_id: str, db: Session = Depends(get_db)) -> BeneficiaryResponse:
    """Retrieve beneficiary details by ID."""
    beneficiary = db.query(Beneficiary).filter(Beneficiary.id == beneficiary_id).first()

    if not beneficiary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Beneficiary '{beneficiary_id}' not found",
        )

    return BeneficiaryResponse(
        id=beneficiary.id,
        name=beneficiary.name,
        age_months=beneficiary.age_months,
        sex=beneficiary.sex,
        pregnancy=beneficiary.pregnancy,
        created_at=beneficiary.created_at.isoformat(),
    )
