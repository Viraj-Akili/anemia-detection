"""
arya-backend/backend/app/routers/nutrition.py

Nutrition Chatbot & Anthropometry API Endpoints.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services.anthropometry_service import (
    AnthropometryEvaluationResult,
    AnthropometryInputError,
    evaluate_anthropometry,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/nutrition", tags=["nutrition"])


class AnthropometryEvaluationRequest(BaseModel):
    height_cm: float = Field(..., description="Height in centimeters (e.g. 160.0)")
    weight_kg: float = Field(..., description="Weight in kilograms (e.g. 55.0)")
    age_years: float = Field(..., description="Age in years (e.g. 28.0 or 3.5)")
    gender: str = Field("FEMALE", description="Biological sex ('MALE' / 'FEMALE')")
    is_pregnant: bool = Field(False, description="Whether patient is currently pregnant")
    muac_value: Optional[float] = Field(None, description="Optional MUAC measurement value")
    muac_unit: str = Field("mm", description="MUAC unit: 'mm' or 'cm'")


class ChatbotAssessmentRequest(BaseModel):
    height_cm: float = Field(..., description="Height in centimeters")
    weight_kg: float = Field(..., description="Weight in kilograms")
    age_years: float = Field(..., description="Age in years")
    gender: str = Field("FEMALE", description="Biological sex")
    muac_value: Optional[float] = Field(None, description="Optional MUAC measurement")
    muac_unit: str = Field("mm", description="MUAC unit ('mm' or 'cm')")
    questionnaire_answers: Dict[str, Any] = Field(default_factory=dict)


@router.post(
    "/evaluate-anthropometry",
    response_model=AnthropometryEvaluationResult,
    status_code=status.HTTP_200_OK,
    summary="Evaluate age-aware BMI, MUAC, and anthropometric nutritional risk",
)
def evaluate_anthropometry_endpoint(
    payload: AnthropometryEvaluationRequest,
) -> AnthropometryEvaluationResult:
    """Validate and compute age-aware BMI and MUAC classifications with overlap deduplication."""
    try:
        result = evaluate_anthropometry(
            height_cm=payload.height_cm,
            weight_kg=payload.weight_kg,
            age_years=payload.age_years,
            gender=payload.gender.lower(),
            muac_value=payload.muac_value,
            muac_unit=payload.muac_unit,
        )
        return result
    except AnthropometryInputError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.error(f"Error evaluating anthropometry: {exc}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal calculation error")
