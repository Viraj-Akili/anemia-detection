"""End-to-End Multimodal ML and Risk Engine Screening Orchestrator."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models import (
    Beneficiary,
    BeneficiaryCategory,
    FollowUp,
    FollowUpStatus,
    Measurement,
    Result,
    RiskLevel,
    Screening,
    ScreeningStatus,
    Sex,
    User,
    UserRole,
)
from app.repositories import get_beneficiary, get_beneficiary_screening_history
from app.schemas.evaluation import (
    ContributorSummary,
    FusionSummary,
    ImageModalitySummary,
    MultimodalEvaluationResponse,
    PatientSummary,
    PPGModalitySummary,
    RiskAnalysisSummary,
)
from app.services.ml_service import ml_service
from app.services.risk_service import risk_service

logger = logging.getLogger(__name__)


def _ensure_default_user(db: Session, worker_id: int = 1) -> User:
    """Ensure a default frontline health worker exists in DB for foreign key consistency."""
    user = db.query(User).filter(User.id == worker_id).first()
    if not user:
        user = User(
            id=worker_id,
            username=f"worker_{worker_id}",
            full_name="Frontline Health Sentinel",
            role=UserRole.WORKER,
            phone="9876543210",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


class ScreeningOrchestrator:
    """Orchestrates ML inference, clinical risk evaluation, and database persistence."""

    def process_screening(
        self,
        db: Session,
        *,
        beneficiary_id: Optional[int] = None,
        patient_name: Optional[str] = None,
        worker_id: int = 1,
        age_years: float,
        gender: str,
        is_pregnant: bool = False,
        trimester: Optional[int] = None,
        weight_kg: Optional[float] = None,
        height_cm: Optional[float] = None,
        muac_cm: Optional[float] = None,
        diet_iron_rich: bool = False,
        diet_frequency: str = "never",
        diet_diversity: int = 0,
        ifa_adherence: str = "unknown",
        symptom_severe_pallor: bool = False,
        symptom_breathlessness: bool = False,
        symptom_bilateral_oedema: bool = False,
        symptom_fatigue: bool = False,
        image_bytes: Optional[bytes] = None,
        image_filename: Optional[str] = None,
        ppg_csv_text: Optional[str] = None,
        ppg_filename: Optional[str] = None,
        device_id: Optional[str] = "PRAHARI_POC_V1",
    ) -> MultimodalEvaluationResponse:
        """Execute end-to-end multimodal screening, risk evaluation, and persistence."""

        now_utc = datetime.now(timezone.utc)
        _ensure_default_user(db, worker_id)

        # 1. Resolve or register beneficiary in PostgreSQL
        beneficiary = None
        if beneficiary_id:
            beneficiary = get_beneficiary(db, beneficiary_id)

        if not beneficiary:
            # Auto-calculate DOB from age
            dob = now_utc - timedelta(days=int(age_years * 365.25))
            sex_enum = Sex.MALE if gender.upper() in ("M", "MALE") else Sex.FEMALE
            cat_enum = (
                BeneficiaryCategory.PREGNANT_WOMAN
                if is_pregnant
                else (BeneficiaryCategory.CHILD if age_years < 12 else BeneficiaryCategory.CHILD)
            )

            beneficiary = Beneficiary(
                name=patient_name or f"Beneficiary_{int(now_utc.timestamp())}",
                date_of_birth=dob,
                sex=sex_enum,
                category=cat_enum,
                is_pregnant=is_pregnant,
                trimester=trimester,
                created_by_id=worker_id,
            )
            db.add(beneficiary)
            db.commit()
            db.refresh(beneficiary)

        # 2. Retrieve past visit history for trajectory calculation
        raw_history = get_beneficiary_screening_history(db, beneficiary.id)
        visit_history = []
        for h in raw_history:
            if h.get("result"):
                visit_history.append({
                    "overall_priority": str(h["result"]["overall_priority"]).lower(),
                    "anemia_risk": str(h["result"]["anemia_risk"]).lower(),
                    "nutrition_risk": str(h["result"]["nutrition_risk"]).lower(),
                    "visit_date": h["started_at"],
                })

        # 3. Execute Multimodal ML Subsystem (Independent Image & PPG inference)
        ml_result = ml_service.evaluate_modalities(
            patient_id=str(beneficiary.id),
            age_years=age_years,
            gender=gender,
            is_pregnant=is_pregnant,
            trimester=trimester,
            image_bytes=image_bytes,
            ppg_csv_text=ppg_csv_text,
        )

        image_out = ml_result.image
        ppg_out = ml_result.ppg

        # Format Image Summary
        image_summary = ImageModalitySummary(
            available=image_out.available if image_out else False,
            status=image_out.status if image_out else "NOT_PROVIDED",
            label=image_out.label if image_out else None,
            probability=image_out.probability if image_out else None,
            confidence=image_out.confidence if image_out else None,
            quality_status=image_out.quality_status if image_out else None,
            quality_score=image_out.quality_score if image_out else None,
            quality_reasons=image_out.quality_reasons if (image_out and image_out.quality_reasons) else [],
            error_message=image_out.error.message if (image_out and image_out.error) else None,
        )

        # Format PPG Summary
        ppg_summary = PPGModalitySummary(
            available=ppg_out.available if ppg_out else False,
            status=ppg_out.status if ppg_out else "NOT_PROVIDED",
            predicted_hb_g_dl=ppg_out.predicted_hb_g_dl if ppg_out else None,
            signal_quality=ppg_out.signal_quality if ppg_out else None,
            sqi=ppg_out.sqi if ppg_out else None,
            sampling_rate_hz=ppg_out.sampling_rate_hz if ppg_out else None,
            samples=ppg_out.samples if ppg_out else None,
            duration_sec=ppg_out.duration_sec if ppg_out else None,
            reasons=[ppg_out.error.message] if (ppg_out and ppg_out.error) else [],
            error_message=ppg_out.error.message if (ppg_out and ppg_out.error) else None,
        )

        # 4. Extract verified PPG Hb if valid
        verified_ppg_hb: Optional[float] = None
        if ppg_out and ppg_out.status == "SUCCESS" and ppg_out.predicted_hb_g_dl is not None:
            verified_ppg_hb = float(ppg_out.predicted_hb_g_dl)

        # 5. Execute Swayam Risk Engine & WHO Deterministic Safety Rules
        risk_out = risk_service.evaluate_risk(
            age_years=age_years,
            gender=gender,
            is_pregnant=is_pregnant,
            trimester=trimester,
            weight_kg=weight_kg,
            height_cm=height_cm,
            muac_cm=muac_cm,
            diet_iron_rich=diet_iron_rich,
            diet_frequency=diet_frequency,
            diet_diversity=diet_diversity,
            ifa_adherence=ifa_adherence,
            symptom_severe_pallor=symptom_severe_pallor,
            symptom_breathlessness=symptom_breathlessness,
            symptom_bilateral_oedema=symptom_bilateral_oedema,
            symptom_fatigue=symptom_fatigue,
            image_label=image_out.label if (image_out and image_out.status == "SUCCESS") else None,
            image_probability=image_out.probability if (image_out and image_out.status == "SUCCESS") else None,
            image_confidence=image_out.confidence if (image_out and image_out.status == "SUCCESS") else None,
            ppg_hb_gdl=verified_ppg_hb,  # <--- WIRED VERIFIED PPG HB
            visit_history=visit_history,
        )

        risk_summary = RiskAnalysisSummary(
            anemia_risk=risk_out["anemia_risk"],
            nutrition_risk=risk_out["nutrition_risk"],
            overall_priority=risk_out["overall_priority"],
            confidence=risk_out["confidence"],
            trajectory=risk_out["trajectory"],
            contributors=[
                ContributorSummary(
                    feature=c["feature"],
                    label=c["label"],
                    importance=float(c["importance"]),
                )
                for c in risk_out["contributors"]
            ],
            recommended_action=risk_out["recommended_action"],
            safety_flags=risk_out["safety_flags"],
            hb_source=risk_out["hb_source"],
        )

        # 6. Database Persistence
        # A) Create Screening record
        screening = Screening(
            beneficiary_id=beneficiary.id,
            worker_id=worker_id,
            status=ScreeningStatus.COMPLETED,
            started_at=now_utc,
            completed_at=datetime.now(timezone.utc),
            device_id=device_id,
        )
        db.add(screening)
        db.flush()

        # B) Create Measurement record if anthropometry is provided
        if weight_kg is not None or height_cm is not None or muac_cm is not None:
            measurement = Measurement(
                screening_id=screening.id,
                weight_kg=weight_kg,
                height_cm=height_cm,
                muac_mm=(muac_cm * 10) if muac_cm is not None else None,
            )
            db.add(measurement)

        # C) Map risk strings to RiskLevel DB Enum
        risk_map = {
            "low": RiskLevel.LOW,
            "moderate": RiskLevel.MODERATE,
            "high": RiskLevel.HIGH,
            "critical": RiskLevel.CRITICAL,
        }

        # D) Create Result record
        db_contributors = {
            "explainability": risk_out["contributors"],
            "safety_flags": risk_out["safety_flags"],
            "image_telemetry": {
                "label": image_summary.label,
                "probability": image_summary.probability,
                "confidence": image_summary.confidence,
                "quality_status": image_summary.quality_status,
                "quality_reasons": image_summary.quality_reasons,
            },
            "ppg_telemetry": {
                "predicted_hb_g_dl": ppg_summary.predicted_hb_g_dl,
                "sqi": ppg_summary.sqi,
                "signal_quality": ppg_summary.signal_quality,
                "reasons": ppg_summary.reasons,
            },
            "hb_source": risk_out["hb_source"],
        }

        result_entity = Result(
            screening_id=screening.id,
            anemia_risk=risk_map.get(risk_summary.anemia_risk.lower(), RiskLevel.LOW),
            nutrition_risk=risk_map.get(risk_summary.nutrition_risk.lower(), RiskLevel.LOW),
            overall_priority=risk_map.get(risk_summary.overall_priority.lower(), RiskLevel.LOW),
            confidence=risk_summary.confidence,
            trajectory=risk_summary.trajectory,
            recommended_action=risk_summary.recommended_action,
            contributors=db_contributors,
            model_name="PRAHARI_MULTIMODAL_V1",
            model_version="1.0.0",
        )
        db.add(result_entity)

        # E) If critical risk or rapid decline, auto-generate a high-priority FollowUp
        if risk_summary.overall_priority.lower() in ("high", "critical") or risk_summary.trajectory in (
            "declining",
            "rapidly_declining",
        ):
            followup = FollowUp(
                beneficiary_id=beneficiary.id,
                screening_id=screening.id,
                assigned_user_id=worker_id,
                due_date=now_utc + timedelta(days=7),
                status=FollowUpStatus.PENDING,
                reason=f"Automated Alert: {risk_summary.overall_priority.upper()} priority triage ({risk_summary.recommended_action})",
                notes=f"Safety Flags: {', '.join(risk_summary.safety_flags) if risk_summary.safety_flags else 'None'}",
            )
            db.add(followup)

        db.commit()
        db.refresh(screening)
        db.refresh(beneficiary)

        # 7. Assemble Unified Response
        patient_summary = PatientSummary(
            beneficiary_id=beneficiary.id,
            name=beneficiary.name,
            age_years=age_years,
            age_months=int(age_years * 12),
            gender=gender.upper(),
            is_pregnant=is_pregnant,
            trimester=trimester,
        )

        return MultimodalEvaluationResponse(
            success=True,
            screening_id=screening.id,
            beneficiary_id=beneficiary.id,
            timestamp=now_utc.isoformat(),
            patient=patient_summary,
            image=image_summary,
            ppg=ppg_summary,
            risk=risk_summary,
            fusion=FusionSummary(),
        )


# Singleton instance
screening_orchestrator = ScreeningOrchestrator()
