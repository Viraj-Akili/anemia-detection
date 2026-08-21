"""Pydantic request/response models for the PRAHARI screening API.

Contract source: ``PRAHARI_Risk_Logic_Backend_Implementation_Plan.md``,
Appendix A — field names, types, and enums below match it verbatim.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums — Appendix A response field enums
# ---------------------------------------------------------------------------


class RiskBand(str, Enum):
    """Anemia / nutrition risk bands (screening framing — never diagnosis)."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class OverallPriority(str, Enum):
    """Overall screening priority — superset of :class:`RiskBand` with critical."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class Trajectory(str, Enum):
    """Risk trend over the beneficiary's recent visit history."""

    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    RAPIDLY_DECLINING = "rapidly_declining"
    INSUFFICIENT_DATA = "insufficient_data"


class RecommendedAction(str, Enum):
    """Next action for the frontline worker (never a medical order)."""

    ROUTINE_MONITORING = "routine_monitoring"
    NUTRITION_COUNSELLING = "nutrition_counselling"
    CONFIRMATORY_TESTING = "confirmatory_testing"
    IMMEDIATE_REFERRAL = "immediate_referral"
    MANUAL_PROTOCOL_ESCALATION = "manual_protocol_escalation"


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class AnemiaInput(BaseModel):
    """Output of the CV pipeline (the AI team's classifier)."""

    risk: RiskBand = Field(description="CV-pipeline risk band for anemia.")
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Classifier confidence in [0, 1].",
    )


class DietInput(BaseModel):
    """Dietary risk inputs from the structured questionnaire."""

    iron_rich_food: bool = Field(
        default=False,
        description="Whether iron-rich food was consumed recently (e.g. yesterday).",
    )
    frequency: Literal["never", "rare", "sometimes", "often"] = Field(
        default="never",
        description="Iron-rich food intake frequency over the past week.",
    )
    diversity: int = Field(
        default=0,
        ge=0,
        le=9,
        description="Dietary diversity: number of food groups consumed (0-9).",
    )


class IfaInput(BaseModel):
    """IFA (iron-folic acid) supplement adherence."""

    adherence: Literal["good", "poor", "unknown"] = Field(
        default="unknown",
        description="Good → protective multiplier; poor/unknown → no protection.",
    )


class SymptomsInput(BaseModel):
    """Symptom red-flag scan inputs (escalation only, never downgrade)."""

    severe_pallor: bool = Field(default=False)
    breathlessness: bool = Field(default=False)
    bilateral_oedema: bool = Field(default=False)
    fatigue: bool = Field(default=False)


class ScreeningRequest(BaseModel):
    """``POST /api/screening/analyze`` request body — Appendix A contract.

    The exact example payload from the prompt validates against this model:

    .. code-block:: json

        {
          "beneficiary_id": "B001",
          "anemia": {"risk": "moderate", "confidence": 0.82},
          "weight": 13.1,
          "height": 97,
          "muac": 12.7,
          "diet": {"iron_rich_food": false}
        }

    ``age_months`` / ``sex`` / ``pregnancy`` are resolved from the registered
    beneficiary record by default (see ``api/deps.py``); the optional context
    fields below only override that record when the worker enters them directly.
    """

    beneficiary_id: str = Field(min_length=1, description="Registered beneficiary id (e.g. B001).")
    anemia: AnemiaInput = Field(description="CV-pipeline anemia estimate.")

    weight: float = Field(gt=0.0, lt=250.0, description="Weight in kg.")
    height: float = Field(gt=0.0, lt=250.0, description="Height in cm.")
    muac: float = Field(
        gt=0.0,
        le=100.0,
        description="Mid-upper arm circumference in cm (converted to mm for storage).",
    )

    diet: DietInput = Field(default_factory=DietInput)

    # Optional context overrides (defaults mirror the beneficiary record).
    pregnancy: bool = Field(default=False)
    trimester: int | None = Field(default=None, ge=1, le=3, description="Required when pregnant.")
    ifa: IfaInput = Field(default_factory=IfaInput)
    symptoms: SymptomsInput = Field(default_factory=SymptomsInput)


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class Contributor(BaseModel):
    """One explainability entry — top contributing feature, human-readable."""

    feature: str = Field(description="Machine feature name (e.g. ``diet_risk``).")
    label: str = Field(
        description="Plain-language reason, e.g. 'Low reported dietary iron intake'.",
    )
    importance: float = Field(
        ge=-1.0,
        le=1.0,
        description="Signed contribution (SHAP value when available).",
    )


class ScreeningResponse(BaseModel):
    """``POST /api/screening/analyze`` response body — Appendix A contract.

    .. code-block:: json

        {
          "anemia_risk": "moderate",
          "nutrition_risk": "high",
          "overall_priority": "high",
          "confidence": 0.81,
          "trajectory": "declining",
          "contributors": [],
          "recommended_action": "confirmatory_testing",
          "safety_flags": []
        }
    """

    anemia_risk: RiskBand
    nutrition_risk: RiskBand
    overall_priority: OverallPriority
    confidence: float = Field(ge=0.0, le=1.0, description="Calibrated confidence in [0, 1].")
    trajectory: Trajectory
    contributors: list[Contributor] = Field(
        default_factory=list,
        description="Top contributing factors, most important first.",
    )
    recommended_action: RecommendedAction
    safety_flags: list[str] = Field(
        default_factory=list,
        description="WHO red-flag identifiers raised by the safety layer (escalation only).",
    )


class HealthResponse(BaseModel):
    """``GET /health`` payload."""

    status: Literal["ok"]
    service: str
    version: str
