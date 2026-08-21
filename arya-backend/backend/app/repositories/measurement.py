from sqlalchemy.orm import Session

from app.models import Measurement


def create_measurement(
    db: Session,
    *,
    screening_id: int,
    weight_kg: float | None = None,
    height_cm: float | None = None,
    muac_mm: float | None = None,
) -> Measurement:
    """Create a new measurement record for a screening."""
    measurement = Measurement(
        screening_id=screening_id,
        weight_kg=weight_kg,
        height_cm=height_cm,
        muac_mm=muac_mm,
    )
    db.add(measurement)
    db.commit()
    db.refresh(measurement)
    return measurement


def get_measurements_for_screening(db: Session, screening_id: int) -> list[Measurement]:
    """Get all measurements for a screening, ordered by created_at."""
    return (
        db.query(Measurement)
        .filter(Measurement.screening_id == screening_id)
        .order_by(Measurement.created_at)
        .all()
    )