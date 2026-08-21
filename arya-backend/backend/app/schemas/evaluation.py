"""Pydantic schemas for the unified Multimodal ML & Risk Screening endpoint."""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class PatientSummary(BaseModel):
    """Patient demographic context returned in the screening response."""
    beneficiary_id: Optional[int] = None
    name: Optional[str] = None
    age_years: float
    age_months: int
    gender: str
    is_pregnant: bool = False
    trimester: Optional[int] = None


class ImageModalitySummary(BaseModel):
    """Independent Image/CV screening evaluation summary."""
    available: bool = False
    status: str = "NOT_PROVIDED"  # "SUCCESS" | "QUALITY_WARNING" | "FAILED" | "NOT_PROVIDED"
    label: Optional[str] = None   # "anemic" | "non_anemic"
    probability: Optional[float] = None # Anemia probability in [0.0, 1.0]
    confidence: Optional[float] = None  # Model confidence in [0.5, 1.0]
    quality_status: Optional[str] = None # "good" | "poor"
    quality_score: Optional[float] = None
    quality_reasons: list[str] = Field(default_factory=list)
    error_message: Optional[str] = None


class PPGModalitySummary(BaseModel):
    """Independent Optical PPG hardware evaluation summary."""
    available: bool = False
    status: str = "NOT_PROVIDED"  # "SUCCESS" | "QUALITY_WARNING" | "FAILED" | "NOT_PROVIDED"
    predicted_hb_g_dl: Optional[float] = None # Continuous Hemoglobin in g/dL
    signal_quality: Optional[str] = None      # "good" | "poor"
    sqi: Optional[float] = None               # Signal Quality Index in [0.0, 1.0]
    sampling_rate_hz: Optional[float] = None
    samples: Optional[int] = None
    duration_sec: Optional[float] = None
    reasons: list[str] = Field(default_factory=list)
    error_message: Optional[str] = None


class ContributorSummary(BaseModel):
    """One SHAP explainability contribution factor."""
    feature: str
    label: str
    importance: float


class RiskAnalysisSummary(BaseModel):
    """Swayam clinical risk engine & WHO deterministic safety evaluation."""
    anemia_risk: str            # "low" | "moderate" | "high"
    nutrition_risk: str         # "low" | "moderate" | "high"
    overall_priority: str       # "low" | "moderate" | "high" | "critical"
    confidence: float           # Platt-calibrated model confidence [0.0, 1.0]
    trajectory: str             # "improving" | "stable" | "declining" | "rapidly_declining" | "insufficient_data"
    contributors: list[ContributorSummary] = Field(default_factory=list)
    recommended_action: str     # "routine_monitoring" | "nutrition_counselling" | "confirmatory_testing" | "immediate_referral" | "manual_protocol_escalation"
    safety_flags: list[str] = Field(default_factory=list) # e.g. ["SEVERE_ANEMIA_THRESHOLD"]
    hb_source: Optional[str] = None # "PPG_SENSOR" | "NONE"


class FusionSummary(BaseModel):
    """Scientific fusion boundary status (modality-preserving)."""
    status: str = "NOT_VALIDATED"
    method: Optional[str] = None
    fused_prediction: Optional[Any] = None
    scientific_notice: str = (
        "No mathematical fusion is applied between Image Probability and PPG Hemoglobin. "
        "Both telemetry signals are preserved independently for clinical safety."
    )


class MultimodalEvaluationResponse(BaseModel):
    """Complete response payload for POST /api/screenings/evaluate-multimodal."""
    success: bool = True
    screening_id: int
    beneficiary_id: int
    timestamp: str
    patient: PatientSummary
    image: ImageModalitySummary
    ppg: PPGModalitySummary
    risk: RiskAnalysisSummary
    fusion: FusionSummary = Field(default_factory=FusionSummary)

    model_config = ConfigDict(from_attributes=True)
