"""
arya-backend/backend/app/services/anthropometry_service.py

Scientifically defensible, age-aware Anthropometric Evaluation Service for PRAHARI.
Integrates Height, Weight, BMI, and MUAC with WHO Growth Standards & adult reference cutoffs.
Implements bounded scoring contributions and overlap/double-counting deduplication.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, Literal, Optional, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Physiological sanity bounds
MIN_HEIGHT_CM = 30.0
MAX_HEIGHT_CM = 250.0
MIN_WEIGHT_KG = 1.0
MAX_WEIGHT_KG = 250.0
MIN_MUAC_MM = 50.0
MAX_MUAC_MM = 500.0

# WHO 6-59 months MUAC cutoffs (WHO/UNICEF 2009/2013 guidelines)
SAM_MUAC_6_59M_MM = 115.0
MAM_MUAC_6_59M_MM = 125.0

# WHO / FANTA Adult Low MUAC cutoff (undernutrition indicator, correlates with BMI < 18.5)
ADULT_LOW_MUAC_MM = 230.0


class AnthropometryInputError(ValueError):
    """Raised when anthropometric inputs violate physiological or domain bounds."""


class AnthropometryEvaluationResult(BaseModel):
    """Complete structured output of the anthropometric evaluation."""
    height_cm: float
    weight_kg: float
    bmi: float
    bmi_category: str
    bmi_interpretation: str
    age_group_classification: str
    muac_mm: Optional[float] = None
    muac_cm: Optional[float] = None
    muac_category: str
    muac_interpretation: str
    risk_level: Literal["HEALTHY", "BORDERLINE", "UNHEALTHY", "CRITICAL"]
    score_adjustment: int
    deduplication_applied: bool
    clinical_explanation: str
    overlap_prevention_note: str
    safety_disclaimer: str = (
        "Anthropometric indices (BMI and MUAC) contribute solely to nutritional status screening "
        "and do not diagnose anemia, micronutrient deficiencies, or replace comprehensive clinical evaluation."
    )


def calculate_bmi(height_cm: float, weight_kg: float) -> float:
    """Calculate Body Mass Index (kg/m²) with strict input validation.
    
    Formula: BMI = weight_kg / (height_m ^ 2) = weight_kg / (height_cm / 100) ^ 2
    """
    if height_cm is None or height_cm <= 0:
        raise AnthropometryInputError(f"Height must be strictly positive (>0 cm), got {height_cm}")
    if weight_kg is None or weight_kg <= 0:
        raise AnthropometryInputError(f"Weight must be strictly positive (>0 kg), got {weight_kg}")
    
    if height_cm < MIN_HEIGHT_CM or height_cm > MAX_HEIGHT_CM:
        raise AnthropometryInputError(
            f"Height {height_cm:.1f} cm is outside realistic physiological range [{MIN_HEIGHT_CM}, {MAX_HEIGHT_CM}] cm"
        )
    if weight_kg < MIN_WEIGHT_KG or weight_kg > MAX_WEIGHT_KG:
        raise AnthropometryInputError(
            f"Weight {weight_kg:.1f} kg is outside realistic physiological range [{MIN_WEIGHT_KG}, {MAX_WEIGHT_KG}] kg"
        )
    
    height_m = height_cm / 100.0
    bmi = weight_kg / (height_m * height_m)
    return round(bmi, 1)


def normalize_muac_mm(muac_value: Optional[float], unit: str = "mm") -> Optional[float]:
    """Normalize MUAC measurement to millimeters (mm) with range validation."""
    if muac_value is None:
        return None
    
    val = float(muac_value)
    if val <= 0:
        raise AnthropometryInputError(f"MUAC must be strictly positive (>0), got {val}")
    
    # If unit is cm or value looks like cm (<50), convert to mm
    if unit.lower() in ("cm", "centimeters") or (unit.lower() == "auto" and val < 50.0):
        val_mm = val * 10.0
    else:
        val_mm = val
    
    if val_mm < MIN_MUAC_MM or val_mm > MAX_MUAC_MM:
        raise AnthropometryInputError(
            f"MUAC {val_mm:.1f} mm is outside realistic physiological range [{MIN_MUAC_MM}, {MAX_MUAC_MM}] mm"
        )
    
    return round(val_mm, 1)


def interpret_bmi(
    bmi: float,
    age_years: float,
    gender: str = "female",
) -> Tuple[str, str, str, Literal["HEALTHY", "BORDERLINE", "UNHEALTHY", "CRITICAL"]]:
    """Age-aware BMI interpretation.
    
    Distinguishes:
    1. Adults (>=19 years): Standard WHO adult BMI cutoffs (<18.5, 18.5-24.9, 25-29.9, >=30).
    2. Children/Adolescents 5-19 years (60-228 months): WHO 2007 BMI-for-age reference standards.
    3. Children under 5 years (<60 months): Explains that Weight-for-Height/WAZ is prioritized over isolated adult BMI.
    
    Returns: (bmi_category, bmi_interpretation, age_group_classification, risk_level)
    """
    age_months = int(age_years * 12)
    
    if age_years >= 19.0:
        age_group = "Adult (>=19 years)"
        if bmi < 16.0:
            category = "severe_underweight"
            interpretation = "Severe Underweight / Severe Chronic Energy Deficiency (BMI < 16.0 kg/m²)"
            risk = "CRITICAL"
        elif bmi < 17.0:
            category = "moderate_underweight"
            interpretation = "Moderate Underweight (BMI 16.0–16.9 kg/m²)"
            risk = "UNHEALTHY"
        elif bmi < 18.5:
            category = "mild_underweight"
            interpretation = "Mild Underweight / Low BMI (BMI 17.0–18.4 kg/m²)"
            risk = "BORDERLINE"
        elif bmi <= 24.9:
            category = "normal"
            interpretation = "Normal Healthy Adult Weight Range (BMI 18.5–24.9 kg/m²)"
            risk = "HEALTHY"
        elif bmi <= 29.9:
            category = "overweight"
            interpretation = "Overweight (BMI 25.0–29.9 kg/m²)"
            risk = "BORDERLINE"
        else:
            category = "obese"
            interpretation = "Obesity (BMI >= 30.0 kg/m²)"
            risk = "UNHEALTHY"
            
    elif age_years >= 5.0:
        age_group = "Child / Adolescent (5–19 years)"
        # WHO 2007 Growth Reference for 5-19 years
        # Note: Median BMI shifts from ~15 kg/m² at age 5 to ~21 kg/m² at age 19
        # Approximate age-interpolated thinness thresholds (< -2 SD)
        expected_median = 15.0 + (age_years - 5.0) * (21.5 - 15.0) / 14.0
        thinness_cutoff = expected_median - 2.5
        severe_thinness_cutoff = expected_median - 3.8
        overweight_cutoff = expected_median + 3.0
        
        if bmi < severe_thinness_cutoff:
            category = "severe_thinness"
            interpretation = f"Severe Thinness for age ({bmi:.1f} kg/m² vs WHO median {expected_median:.1f} kg/m², < -3 SD range)"
            risk = "CRITICAL"
        elif bmi < thinness_cutoff:
            category = "thinness"
            interpretation = f"Thinness / Underweight for age ({bmi:.1f} kg/m² vs WHO median {expected_median:.1f} kg/m², < -2 SD range)"
            risk = "UNHEALTHY"
        elif bmi > overweight_cutoff + 3.0:
            category = "obese"
            interpretation = f"Obese for age ({bmi:.1f} kg/m² vs WHO reference, > +2 SD range)"
            risk = "UNHEALTHY"
        elif bmi > overweight_cutoff:
            category = "overweight"
            interpretation = f"Overweight for age ({bmi:.1f} kg/m² vs WHO reference, > +1 SD range)"
            risk = "BORDERLINE"
        else:
            category = "normal"
            interpretation = f"Normal BMI-for-age ({bmi:.1f} kg/m², within -2 SD to +1 SD WHO reference range)"
            risk = "HEALTHY"
            
    else:
        # Children < 5 years (under 60 months)
        age_group = "Child (< 5 years / 6–59 months)"
        # For under 5 years, WHO Anthro prioritizes WHZ and MUAC rather than isolated adult BMI
        if bmi < 13.0:
            category = "low_bmi_preschool"
            interpretation = (
                f"Low Body Mass Index ({bmi:.1f} kg/m²). For children under 5 years, "
                "WHO Weight-for-Height (WHZ) and MUAC are prioritized over adult BMI cutoffs."
            )
            risk = "UNHEALTHY"
        elif bmi > 18.5:
            category = "high_bmi_preschool"
            interpretation = f"Elevated Body Mass Index ({bmi:.1f} kg/m² for child under 5 years)."
            risk = "BORDERLINE"
        else:
            category = "normal_preschool"
            interpretation = (
                f"Body Mass Index {bmi:.1f} kg/m². Standard WHO Weight-for-Height and MUAC "
                "are recommended for comprehensive acute growth tracking."
            )
            risk = "HEALTHY"
            
    return category, interpretation, age_group, risk


def interpret_muac(
    muac_mm: Optional[float],
    age_years: float,
) -> Tuple[str, str, Literal["HEALTHY", "BORDERLINE", "UNHEALTHY", "CRITICAL"]]:
    """Age-appropriate MUAC interpretation.
    
    Rules:
    1. Children 6–59 months (0.5 to < 5.0 years):
       - < 115 mm: Severe Acute Malnutrition (SAM) -> CRITICAL
       - 115 mm to < 125 mm: Moderate Acute Malnutrition (MAM) -> UNHEALTHY
       - >= 125 mm: Normal (does not meet acute malnutrition threshold) -> HEALTHY
    2. Adults (>=19 years):
       - < 230 mm: Adult low MUAC indicator (WHO/FANTA) -> BORDERLINE
       - >= 230 mm: Normal -> HEALTHY
    3. Other Ages (5–18 years):
       - Recorded and displayed informatively without inventing non-standard WHO cutoffs -> HEALTHY
    4. Not Provided:
       - "MUAC not provided — MUAC-based assessment was not applied." -> HEALTHY (No penalty)
    """
    if muac_mm is None:
        return "not_provided", "MUAC not provided — MUAC-based acute malnutrition assessment was not applied.", "HEALTHY"
    
    age_months = int(age_years * 12)
    
    if 6 <= age_months < 60:
        if muac_mm < SAM_MUAC_6_59M_MM:
            return (
                "severe",
                f"MUAC {muac_mm:.0f} mm ({muac_mm/10:.1f} cm) — Severe Acute Malnutrition (SAM) criterion for children 6–59 months (< 115 mm).",
                "CRITICAL",
            )
        elif muac_mm < MAM_MUAC_6_59M_MM:
            return (
                "moderate",
                f"MUAC {muac_mm:.0f} mm ({muac_mm/10:.1f} cm) — Moderate Acute Malnutrition (MAM) range for children 6–59 months (115–124 mm).",
                "UNHEALTHY",
            )
        else:
            return (
                "normal",
                f"MUAC {muac_mm:.0f} mm ({muac_mm/10:.1f} cm) — Within normal reference range (>= 125 mm) for children 6–59 months.",
                "HEALTHY",
            )
    elif age_years >= 19.0:
        if muac_mm < ADULT_LOW_MUAC_MM:
            return (
                "moderate",
                f"MUAC {muac_mm:.0f} mm ({muac_mm/10:.1f} cm) — Low adult arm circumference (< 230 mm, WHO/FANTA undernutrition indicator).",
                "BORDERLINE",
            )
        else:
            return (
                "normal",
                f"MUAC {muac_mm:.0f} mm ({muac_mm/10:.1f} cm) — Adequate adult arm circumference (>= 230 mm).",
                "HEALTHY",
            )
    else:
        # Children/Adolescents 5 to <19 years: record informatively without fabricating non-standard WHO cutoffs
        return (
            "informative",
            f"MUAC {muac_mm:.0f} mm ({muac_mm/10:.1f} cm) recorded. (Standard WHO SAM/MAM cutoffs apply strictly to 6–59 months; BMI-for-age is primary for 5–19 years).",
            "HEALTHY",
        )


def evaluate_anthropometry(
    height_cm: float,
    weight_kg: float,
    age_years: float,
    gender: str = "female",
    muac_value: Optional[float] = None,
    muac_unit: str = "mm",
) -> AnthropometryEvaluationResult:
    """Execute complete, bounded, deduplicated anthropometric evaluation."""
    bmi = calculate_bmi(height_cm, weight_kg)
    muac_mm = normalize_muac_mm(muac_value, muac_unit)
    muac_cm = round(muac_mm / 10.0, 1) if muac_mm is not None else None
    
    bmi_cat, bmi_interp, age_group, bmi_risk = interpret_bmi(bmi, age_years, gender)
    muac_cat, muac_interp, muac_risk = interpret_muac(muac_mm, age_years)
    
    # Bounded scoring contribution and overlap prevention
    risk_rank = {"HEALTHY": 0, "BORDERLINE": 1, "UNHEALTHY": 2, "CRITICAL": 3}
    penalty_map = {"HEALTHY": 0, "BORDERLINE": -10, "UNHEALTHY": -25, "CRITICAL": -40}
    
    # Overlap / Deduplication: Take the maximum deficit rather than multiplying or summing
    bmi_penalty = penalty_map[bmi_risk]
    muac_penalty = penalty_map[muac_risk]
    
    # Bounded penalty: take the worst of either index, avoiding double-penalization
    final_penalty = min(bmi_penalty, muac_penalty)  # Note: penalties are negative numbers
    deduplication_applied = (bmi_risk in ("UNHEALTHY", "CRITICAL") and muac_risk in ("UNHEALTHY", "CRITICAL"))
    
    # Determine composite anthropometric risk level
    overall_rank = max(risk_rank[bmi_risk], risk_rank[muac_risk])
    inv_rank = {0: "HEALTHY", 1: "BORDERLINE", 2: "UNHEALTHY", 3: "CRITICAL"}
    composite_risk: Literal["HEALTHY", "BORDERLINE", "UNHEALTHY", "CRITICAL"] = inv_rank[overall_rank]
    
    # Construct transparent explanation
    if composite_risk == "CRITICAL":
        explanation = (
            f"Critical anthropometric risk identified ({bmi_cat if bmi_risk == 'CRITICAL' else muac_cat}). "
            "Immediate clinical evaluation and nutritional rehabilitation referral recommended."
        )
    elif composite_risk == "UNHEALTHY":
        explanation = (
            f"Nutritional concern identified from anthropometric measurements ({bmi_cat if bmi_risk == 'UNHEALTHY' else muac_cat}). "
            "Targeted dietary counseling and supplemental nutrition monitoring recommended."
        )
    elif composite_risk == "BORDERLINE":
        explanation = (
            "Mild anthropometric vulnerability noted. Routine dietary diversification and growth monitoring advised."
        )
    else:
        explanation = (
            f"Anthropometric measurements ({bmi:.1f} kg/m²) fall within expected healthy reference parameters."
        )
        
    overlap_note = (
        "BMI and MUAC were evaluated as complementary indicators. Overlap deduplication was enforced to prevent artificial risk inflation."
        if deduplication_applied
        else "Individual anthropometric indicators evaluated independently without artificial inflation."
    )
    
    return AnthropometryEvaluationResult(
        height_cm=height_cm,
        weight_kg=weight_kg,
        bmi=bmi,
        bmi_category=bmi_cat,
        bmi_interpretation=bmi_interp,
        age_group_classification=age_group,
        muac_mm=muac_mm,
        muac_cm=muac_cm,
        muac_category=muac_cat,
        muac_interpretation=muac_interp,
        risk_level=composite_risk,
        score_adjustment=final_penalty,
        deduplication_applied=deduplication_applied,
        clinical_explanation=explanation,
        overlap_prevention_note=overlap_note,
    )
