from sqlalchemy.orm import Session

from app.models import Result


def create_result(
    db: Session,
    *,
    screening_id: int,
    anemia_risk: str,
    nutrition_risk: str,
    overall_priority: str,
    confidence: float | None = None,
    trajectory: str | None = None,
    recommended_action: str | None = None,
    contributors: dict | None = None,
    model_name: str | None = None,
    model_version: str | None = None,
) -> Result:
    """Create a new result record for a screening."""
    result = Result(
        screening_id=screening_id,
        anemia_risk=anemia_risk,
        nutrition_risk=nutrition_risk,
        overall_priority=overall_priority,
        confidence=confidence,
        trajectory=trajectory,
        recommended_action=recommended_action,
        contributors=contributors,
        model_name=model_name,
        model_version=model_version,
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


def get_result_for_screening(db: Session, screening_id: int) -> Result | None:
    """Get the result for a screening (zero or one)."""
    return db.query(Result).filter(Result.screening_id == screening_id).first()