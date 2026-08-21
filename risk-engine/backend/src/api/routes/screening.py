"""``POST /api/screening/analyze`` — the single screening endpoint.

Full pipeline wiring:

    request → load history → anthropometry → context → features
            → fusion → safety → trajectory → persist → response
"""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import anthropometry.engine as anthro_engine
import context.engine as context_engine
import fusion.engine as fusion_engine
import fusion.features as fusion_features
import safety.engine as safety_engine
import safety.rules as safety_rules
import trajectory.engine as trajectory_engine
from api.deps import get_db
from models.entities import Beneficiary, Visit
from models.schemas import OverallPriority, RiskBand, ScreeningRequest, ScreeningResponse, Trajectory

router = APIRouter(prefix="/screening", tags=["screening"])
logger = logging.getLogger(__name__)


def _proba_to_risk_band(proba: float) -> RiskBand:
    """Convert probability to risk band using standard thresholds.

    Thresholds:
    - [0.0, 0.33) → low
    - [0.33, 0.67) → moderate
    - [0.67, 1.0] → high
    """
    if proba < 0.33:
        return RiskBand.LOW
    elif proba < 0.67:
        return RiskBand.MODERATE
    else:
        return RiskBand.HIGH


def _load_visit_history(db: Session, beneficiary_id: str, limit: int = 5) -> list[dict]:
    """Load last N visits for trajectory computation."""
    visits = (
        db.query(Visit)
        .filter(Visit.beneficiary_id == beneficiary_id)
        .order_by(Visit.visit_date.desc())
        .limit(limit)
        .all()
    )

    # Reverse to get oldest-first order for trajectory computation
    visits_data = []
    for v in reversed(visits):
        visits_data.append({
            "overall_priority": v.overall_priority,
            "visit_date": v.visit_date,
            "anemia_risk": v.anemia_risk,
            "nutrition_risk": v.nutrition_risk,
        })

    return visits_data


@router.post("/analyze", response_model=ScreeningResponse, summary="Analyze one screening visit")
def analyze(payload: ScreeningRequest, db: Session = Depends(get_db)) -> ScreeningResponse:
    """Run the full risk pipeline and return the Appendix A response shape."""

    start_time = time.perf_counter()
    beneficiary_id = payload.beneficiary_id

    try:
        # 1. Load beneficiary (for age, sex context)
        beneficiary = db.query(Beneficiary).filter(Beneficiary.id == beneficiary_id).first()
        if not beneficiary:
            logger.warning(f"Unknown beneficiary attempted: {beneficiary_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Unknown beneficiary: {beneficiary_id}",
            )

        age_months = beneficiary.age_months
        sex = beneficiary.sex
        pregnancy = payload.pregnancy or beneficiary.pregnancy

        # 2. Load visit history for trajectory
        history = _load_visit_history(db, beneficiary_id, limit=5)

        # 3. Anthropometry: compute z-scores and categories
        anthro_result = {
            "whz": anthro_engine.whz(age_months, sex, payload.weight, payload.height),
            "haz": anthro_engine.haz(age_months, sex, payload.height),
            "waz": anthro_engine.waz(age_months, sex, payload.weight),
            "muac_z": anthro_engine.muac_z(age_months, sex, payload.muac * 10),  # cm -> mm
        }
        anthro_result["whz_cat"] = anthro_engine.zscore_to_category(anthro_result["whz"])
        anthro_result["haz_cat"] = anthro_engine.zscore_to_category(anthro_result["haz"])
        anthro_result["waz_cat"] = anthro_engine.zscore_to_category(anthro_result["waz"])
        anthro_result["muac_cat"] = anthro_engine.muac_category(age_months, sex, payload.muac * 10)

        # 4. Context modifiers
        context_modifiers = context_engine.compute_modifiers(
            diet=payload.diet,
            ifa=payload.ifa,
            symptoms=payload.symptoms,
            age_months=age_months,
            sex=sex,
            pregnancy=pregnancy,
            trimester=payload.trimester,
        )

        # Convert context modifiers to dict for fusion features
        context_result = {
            "diet_risk": context_modifiers.dietary_risk,
            "ifa_protection": context_modifiers.ifa_protection,
            "symptom_flags": len(context_modifiers.symptom_flags),  # Count of flags
            "age_months": age_months,
            "sex": sex,
            "pregnancy": pregnancy,
            "trimester": payload.trimester or 0,
        }

        # 5. Build fusion feature vector
        history_features = {
            "prev_anemia_risk": 0.0,
            "prev_nutrition_risk": 0.0,
            "visits_count": len(history),
        }
        if history:
            last_visit = history[-1]
            anemia_map = {"low": 0.0, "moderate": 0.5, "high": 1.0}
            nutrition_map = {"low": 0.0, "moderate": 0.5, "high": 1.0}
            history_features["prev_anemia_risk"] = anemia_map.get(last_visit.get("anemia_risk", "low"), 0.0)
            history_features["prev_nutrition_risk"] = nutrition_map.get(last_visit.get("nutrition_risk", "low"), 0.0)

        feature_vec = fusion_features.build_features(
            anemia={"risk": payload.anemia.risk.value, "confidence": payload.anemia.confidence},
            anthropometry=anthro_result,
            context=context_result,
            history=history_features,
        )

        # 6. Fusion model prediction
        fusion_output = fusion_engine.predict(feature_vec)

        # Convert fusion probabilities to risk bands
        anemia_risk_band = _proba_to_risk_band(fusion_output["anemia_risk_proba"])
        nutrition_risk_band = _proba_to_risk_band(fusion_output["nutrition_risk_proba"])

        # 7. Safety rules (convert inputs to SafetyInput dataclass)
        from safety.rules import SafetyInput

        safety_input = SafetyInput(
            pregnancy=pregnancy,
            trimester=payload.trimester,
            age_months=age_months,
            sex=sex,
            hb_gdl=None,  # We don't have Hb estimate in this flow
            muac_category=anthro_result["muac_cat"],
            whz=anthro_result["whz"],
            bilateral_oedema=payload.symptoms.bilateral_oedema,
            severe_pallor=payload.symptoms.severe_pallor,
            breathlessness=payload.symptoms.breathlessness,
            consecutive_poor_quality=0,  # TODO: track this across visits
        )
        rule_result = safety_rules.evaluate(safety_input)

        # 8. Safety layer (escalation-only merge)
        safety_output = safety_engine.apply(
            anemia_risk=anemia_risk_band,
            nutrition_risk=nutrition_risk_band,
            rule_output=rule_result,
        )

        # 9. Trajectory computation (before persisting this visit)
        traj_result = trajectory_engine.compute(history)
        trajectory_value = Trajectory(traj_result["trajectory"])
        early_intervention = traj_result["early_intervention"]

        # Early intervention escalation: if flagged, escalate priority to HIGH minimum
        if early_intervention and safety_output["overall_priority"].value in ("low", "moderate"):
            safety_output["overall_priority"] = OverallPriority.HIGH
            safety_output["recommended_action"] = "confirmatory_testing"

        # 10. Persist visit
        new_visit = Visit(
            id=uuid.uuid4(),
            beneficiary_id=beneficiary_id,
            visit_date=datetime.utcnow(),
            weight_kg=payload.weight,
            height_cm=payload.height,
            muac_mm=payload.muac * 10,  # cm -> mm
            whz=anthro_result["whz"],
            haz=anthro_result["haz"],
            waz=anthro_result["waz"],
            muac_category=anthro_result["muac_cat"],
            whz_category=anthro_result["whz_cat"],
            haz_category=anthro_result["haz_cat"],
            waz_category=anthro_result["waz_cat"],
            anemia_ai_risk=payload.anemia.risk.value,
            anemia_ai_confidence=float(payload.anemia.confidence),
            anemia_risk=safety_output["anemia_risk"].value,
            nutrition_risk=safety_output["nutrition_risk"].value,
            overall_priority=safety_output["overall_priority"].value,
            confidence=float(fusion_output["confidence"]),
            trajectory=trajectory_value.value,
            contributors=fusion_output["contributors"],  # Already dicts from fusion engine
            recommended_action=(
                safety_output["recommended_action"].value
                if hasattr(safety_output["recommended_action"], "value")
                else safety_output["recommended_action"]
            ),
            safety_flags=safety_output["safety_flags"],
            escalated=early_intervention,
            context_snapshot={
                "diet": payload.diet.model_dump() if payload.diet else None,
                "ifa": payload.ifa.model_dump() if payload.ifa else None,
                "symptoms": payload.symptoms.model_dump() if payload.symptoms else None,
                "pregnancy": pregnancy,
                "trimester": payload.trimester,
            },
        )

        db.add(new_visit)
        db.commit()

        # 11. Build response
        response = ScreeningResponse(
            anemia_risk=safety_output["anemia_risk"],
            nutrition_risk=safety_output["nutrition_risk"],
            overall_priority=safety_output["overall_priority"],
            confidence=fusion_output["confidence"],
            trajectory=trajectory_value,
            contributors=fusion_output["contributors"],
            recommended_action=safety_output["recommended_action"],
            safety_flags=safety_output["safety_flags"],
        )

        # Log successful screening (no PII: no names, no raw measurements)
        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "Screening completed",
            extra={
                "beneficiary_id": beneficiary_id,
                "anemia_risk": response.anemia_risk.value,
                "nutrition_risk": response.nutrition_risk.value,
                "overall_priority": response.overall_priority.value,
                "trajectory": response.trajectory.value,
                "early_intervention": early_intervention,
                "safety_flags_count": len(response.safety_flags),
                "latency_ms": round(latency_ms, 2),
            },
        )

        return response

    except HTTPException:
        # Re-raise HTTP exceptions (404, 422) as-is
        raise
    except anthro_engine.AnthropometryInputError as exc:
        # Anthropometry validation errors → 422
        logger.warning(f"Anthropometry validation failed for {beneficiary_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Anthropometry validation error: {exc}",
        )
    except fusion_features.FeatureInputError as exc:
        # Feature building errors → 422
        logger.warning(f"Feature validation failed for {beneficiary_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Feature validation error: {exc}",
        )
    except Exception as exc:
        # Unexpected errors → 500 with generic message (don't leak internals)
        logger.exception(f"Unexpected error in screening for {beneficiary_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during screening analysis",
        )
