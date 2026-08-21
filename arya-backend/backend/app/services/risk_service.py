"""Risk engine execution service wrapping Swayam Risk Engine & WHO Safety Rules."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Ensure sibling directories (risk-engine) are on sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
RISK_ENGINE_SRC = WORKSPACE_ROOT / "risk-engine" / "backend" / "src"
SWAYAM_SRC = WORKSPACE_ROOT / "swayam risk" / "backend" / "src"
for src_path in (RISK_ENGINE_SRC, SWAYAM_SRC):
    if src_path.exists() and str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

try:
    import anthropometry.who_tables as who_tables
    import anthropometry.engine as anthro_engine
    import context.engine as context_engine
    import context.thresholds as thresholds
    import fusion.engine as fusion_engine
    import fusion.features as fusion_features
    import safety.rules as safety_rules
    import safety.engine as safety_engine
    import trajectory.engine as trajectory_engine
    from models.schemas import (
        RiskBand,
        OverallPriority,
        Trajectory,
        RecommendedAction,
        DietInput,
        IfaInput,
        SymptomsInput,
    )
except ImportError as exc:
    logger.error(f"Failed to import Swayam risk engine modules: {exc}")
    raise

# Preload WHO child growth reference tables once
try:
    who_tables.preload()
except Exception as exc:
    logger.warning(f"WHO tables preload notice: {exc}")


def _proba_to_risk_band(proba: float) -> RiskBand:
    """Convert probability to standard 3-tier risk band."""
    if proba < 0.33:
        return RiskBand.LOW
    elif proba < 0.67:
        return RiskBand.MODERATE
    else:
        return RiskBand.HIGH


class RiskService:
    """Service wrapper for executing the calibrated XGBoost fusion and WHO safety rules."""

    def evaluate_risk(
        self,
        *,
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
        image_label: Optional[str] = None,
        image_probability: Optional[float] = None,
        image_confidence: Optional[float] = None,
        ppg_hb_gdl: Optional[float] = None,
        visit_history: Optional[list[dict]] = None,
    ) -> dict[str, Any]:
        """Execute the full clinical risk assessment pipeline.

        Wired Inputs:
        - Image ML classification & confidence -> AnemiaInput
        - Verified Optical PPG Hemoglobin -> SafetyInput.hb_gdl (activates Red Flag 1)
        """
        age_months = int(age_years * 12)
        sex = gender.lower()

        # 1. Map Image ML output to AI input
        if image_label:
            if image_label == "anemic":
                ai_risk = "high"
            elif image_probability is not None and 0.4 <= image_probability <= 0.6:
                ai_risk = "moderate"
            else:
                ai_risk = "low"
            ai_confidence = float(image_confidence) if image_confidence is not None else 0.85
        else:
            ai_risk = "low"
            ai_confidence = 0.50

        # 2. Compute Anthropometry z-scores & categories
        anthro_result: dict[str, Any] = {
            "whz": 0.0,
            "haz": 0.0,
            "waz": 0.0,
            "muac_z": 0.0,
            "whz_cat": "normal",
            "haz_cat": "normal",
            "waz_cat": "normal",
            "muac_cat": "normal",
        }

        # 2. Compute Anthropometry z-scores & categories (age-aware, optional MUAC support)
        if 0 < age_months <= 60 and weight_kg and height_cm:
            try:
                whz_val = anthro_engine.whz(age_months, sex, weight_kg, height_cm)
                haz_val = anthro_engine.haz(age_months, sex, height_cm)
                waz_val = anthro_engine.waz(age_months, sex, weight_kg)

                anthro_result["whz"] = whz_val
                anthro_result["haz"] = haz_val
                anthro_result["waz"] = waz_val

                anthro_result["whz_cat"] = anthro_engine.zscore_to_category(whz_val)
                anthro_result["haz_cat"] = anthro_engine.zscore_to_category(haz_val)
                anthro_result["waz_cat"] = anthro_engine.zscore_to_category(waz_val)

                if muac_cm:
                    muac_z_val = anthro_engine.muac_z(age_months, sex, muac_cm * 10)  # cm -> mm
                    anthro_result["muac_z"] = muac_z_val
                    anthro_result["muac_cat"] = anthro_engine.muac_category(age_months, sex, muac_cm * 10)
            except Exception as exc:
                logger.warning(f"WHO child anthropometry calculation notice: {exc}")
        elif age_months > 60 and weight_kg and height_cm:
            try:
                height_m = height_cm / 100.0
                bmi = weight_kg / (height_m * height_m)
                if bmi < 16.0:
                    anthro_result["whz_cat"] = "severe"
                elif bmi < 18.5:
                    anthro_result["whz_cat"] = "moderate"
                else:
                    anthro_result["whz_cat"] = "normal"
            except Exception as exc:
                logger.warning(f"Adult/adolescent BMI calculation notice: {exc}")

        if muac_cm and age_months > 60:
            # Adult / Older child MUAC thresholds (WHO/FANTA < 230 mm indicator)
            muac_mm_val = muac_cm * 10.0
            if muac_mm_val < 230.0:
                anthro_result["muac_cat"] = "moderate"
            else:
                anthro_result["muac_cat"] = "normal"

        # 3. Context modifiers
        diet_in = DietInput(
            iron_rich_food=diet_iron_rich,
            frequency=diet_frequency,  # type: ignore
            diversity=min(max(diet_diversity, 0), 9),
        )
        ifa_in = IfaInput(adherence=ifa_adherence)  # type: ignore
        symptoms_in = SymptomsInput(
            severe_pallor=symptom_severe_pallor,
            breathlessness=symptom_breathlessness,
            bilateral_oedema=symptom_bilateral_oedema,
            fatigue=symptom_fatigue,
        )

        context_modifiers = context_engine.compute_modifiers(
            diet=diet_in,
            ifa=ifa_in,
            symptoms=symptoms_in,
            age_months=float(age_months) if not is_pregnant else None,
            sex=sex,
            pregnancy=is_pregnant,
            trimester=trimester,
        )

        context_dict = {
            "diet_risk": context_modifiers.dietary_risk,
            "ifa_protection": context_modifiers.ifa_protection,
            "symptom_flags": len(context_modifiers.symptom_flags),
            "age_months": age_months,
            "sex": sex,
            "pregnancy": is_pregnant,
            "trimester": trimester or 0,
        }

        # 4. Visit history features
        history_list = visit_history or []
        history_features = {
            "prev_anemia_risk": 0.0,
            "prev_nutrition_risk": 0.0,
            "visits_count": len(history_list),
        }
        if history_list:
            last_visit = history_list[-1]
            anemia_map = {"low": 0.0, "moderate": 0.5, "high": 1.0, "critical": 1.0}
            nutrition_map = {"low": 0.0, "moderate": 0.5, "high": 1.0, "critical": 1.0}
            history_features["prev_anemia_risk"] = anemia_map.get(
                str(last_visit.get("anemia_risk", "low")).lower(), 0.0
            )
            history_features["prev_nutrition_risk"] = nutrition_map.get(
                str(last_visit.get("nutrition_risk", "low")).lower(), 0.0
            )

        # 5. Build fixed 20-feature vector & predict
        feature_vec = fusion_features.build_features(
            anemia={"risk": ai_risk, "confidence": ai_confidence},
            anthropometry=anthro_result,
            context=context_dict,
            history=history_features,
        )

        fusion_output = fusion_engine.predict(feature_vec)

        anemia_risk_band = _proba_to_risk_band(fusion_output["anemia_risk_proba"])
        nutrition_risk_band = _proba_to_risk_band(fusion_output["nutrition_risk_proba"])

        # 6. Evaluate 5 WHO Deterministic Red-Flag Safety Rules
        # WIRED: Pass verified PPG Hb output into SafetyInput.hb_gdl
        safety_input = safety_rules.SafetyInput(
            pregnancy=is_pregnant,
            trimester=trimester,
            age_months=float(age_months) if not is_pregnant else None,
            sex=sex,
            hb_gdl=ppg_hb_gdl,  # <--- WIRED VERIFIED PPG HB
            muac_category=anthro_result["muac_cat"],
            whz=anthro_result["whz"],
            bilateral_oedema=symptom_bilateral_oedema,
            severe_pallor=symptom_severe_pallor,
            breathlessness=symptom_breathlessness,
            consecutive_poor_quality=0,
        )
        rule_result = safety_rules.evaluate(safety_input)

        # 7. Merge fusion predictions with safety rules (escalation only)
        safety_output = safety_engine.apply(
            anemia_risk=anemia_risk_band,
            nutrition_risk=nutrition_risk_band,
            rule_output=rule_result,
        )

        # 8. Multi-visit trajectory calculation
        traj_result = trajectory_engine.compute(history_list)
        trajectory_value = traj_result["trajectory"]
        early_intervention = traj_result["early_intervention"]

        if early_intervention and safety_output["overall_priority"].value in ("low", "moderate"):
            safety_output["overall_priority"] = OverallPriority.HIGH
            safety_output["recommended_action"] = RecommendedAction.CONFIRMATORY_TESTING

        return {
            "anemia_risk": safety_output["anemia_risk"].value,
            "nutrition_risk": safety_output["nutrition_risk"].value,
            "overall_priority": safety_output["overall_priority"].value,
            "confidence": float(fusion_output["confidence"]),
            "trajectory": trajectory_value,
            "contributors": fusion_output["contributors"],
            "recommended_action": (
                safety_output["recommended_action"].value
                if hasattr(safety_output["recommended_action"], "value")
                else str(safety_output["recommended_action"])
            ),
            "safety_flags": list(safety_output["safety_flags"]),
            "hb_source": "PPG_SENSOR" if ppg_hb_gdl is not None else "NONE",
            "raw_fusion_anemia_proba": float(fusion_output["anemia_risk_proba"]),
            "raw_fusion_nutrition_proba": float(fusion_output["nutrition_risk_proba"]),
        }


# Singleton instance
risk_service = RiskService()
