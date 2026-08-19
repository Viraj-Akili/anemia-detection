from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import get_beneficiary, get_beneficiary_screening_history

router = APIRouter(prefix="/api/beneficiaries", tags=["history"])


@router.get("/{beneficiary_id}/history")
def get_beneficiary_history_endpoint(
    beneficiary_id: int,
    db: Session = Depends(get_db),
) -> list[dict]:
    """Get complete longitudinal screening history for a beneficiary."""
    # Verify beneficiary exists
    beneficiary = get_beneficiary(db, beneficiary_id)
    if not beneficiary:
        raise HTTPException(status_code=404, detail="Beneficiary not found")
    
    return get_beneficiary_screening_history(db, beneficiary_id)