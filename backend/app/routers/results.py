from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import (
    create_result,
    get_result_for_screening,
)
from app.schemas import ResultCreate, ResultRead

router = APIRouter(prefix="/api/screenings", tags=["results"])


@router.post("/{screening_id}/result", response_model=ResultRead, status_code=status.HTTP_201_CREATED)
def create_result_endpoint(
    screening_id: int,
    result_in: ResultCreate,
    db: Session = Depends(get_db),
) -> ResultRead:
    """Create or update a result for a screening."""
    # Check if result already exists
    existing = get_result_for_screening(db, screening_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Result already exists for this screening",
        )
    
    result = create_result(
        db,
        screening_id=screening_id,
        anemia_risk=result_in.anemia_risk,
        nutrition_risk=result_in.nutrition_risk,
        overall_priority=result_in.overall_priority,
        confidence=result_in.confidence,
        trajectory=result_in.trajectory,
        recommended_action=result_in.recommended_action,
        contributors=result_in.contributors,
        model_name=result_in.model_name,
        model_version=result_in.model_version,
    )
    return result


@router.get("/{screening_id}/result", response_model=ResultRead)
def get_result_for_screening_endpoint(
    screening_id: int,
    db: Session = Depends(get_db),
) -> ResultRead:
    """Get the result for a screening."""
    result = get_result_for_screening(db, screening_id)
    if not result:
        raise HTTPException(status_code=404, detail="Result not found for this screening")
    return result