from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from app.models import Beneficiary, Screening, Measurement, Result, FollowUp


def get_beneficiary_screening_history(
    db: Session, beneficiary_id: int
) -> list[dict]:
    """
    Get complete longitudinal screening history for a beneficiary.
    Returns screenings with their measurements, result, and follow-ups.
    """
    screenings = (
        db.query(Screening)
        .options(
            joinedload(Screening.measurements),
            joinedload(Screening.result),
            joinedload(Screening.followups),
        )
        .filter(Screening.beneficiary_id == beneficiary_id)
        .order_by(desc(Screening.started_at))
        .all()
    )

    history = []
    for screening in screenings:
        screening_data = {
            "id": screening.id,
            "beneficiary_id": screening.beneficiary_id,
            "worker_id": screening.worker_id,
            "status": screening.status,
            "started_at": screening.started_at,
            "completed_at": screening.completed_at,
            "device_id": screening.device_id,
            "created_at": screening.created_at,
            "updated_at": screening.updated_at,
            "measurements": [
                {
                    "id": m.id,
                    "weight_kg": m.weight_kg,
                    "height_cm": m.height_cm,
                    "muac_mm": m.muac_mm,
                    "created_at": m.created_at,
                }
                for m in screening.measurements
            ],
            "result": None,
            "followups": [
                {
                    "id": f.id,
                    "assigned_user_id": f.assigned_user_id,
                    "due_date": f.due_date,
                    "status": f.status,
                    "reason": f.reason,
                    "notes": f.notes,
                    "completed_at": f.completed_at,
                }
                for f in screening.followups
            ],
        }

        if screening.result:
            r = screening.result
            screening_data["result"] = {
                "id": r.id,
                "anemia_risk": r.anemia_risk,
                "nutrition_risk": r.nutrition_risk,
                "overall_priority": r.overall_priority,
                "confidence": r.confidence,
                "trajectory": r.trajectory,
                "recommended_action": r.recommended_action,
                "contributors": r.contributors,
                "model_name": r.model_name,
                "model_version": r.model_version,
                "created_at": r.created_at,
            }

        history.append(screening_data)

    return history