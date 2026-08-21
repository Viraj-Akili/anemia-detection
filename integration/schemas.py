"""Pydantic and dataclass schemas for the PRAHARI Multimodal Integration Layer.

Defines strict, validated schemas for multimodal patient screening requests and
unified responses, preserving the independent integrity of both the Image (CV)
and Optical PPG hardware modalities without unvalidated statistical fusion.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ==============================================================================
# Request Schemas
# ==============================================================================

class PatientDemographics(BaseModel):
    """Patient demographic data used for modality calibration."""
    age: Optional[float] = Field(
        default=25.0,
        ge=0.0,
        le=130.0,
        description="Patient age in years (used by PPG model features). Default: 25.0."
    )
    gender: Optional[str] = Field(
        default="Male",
        description="Patient biological sex / gender (used by PPG model features). E.g. 'Male', 'Female'."
    )


class MultimodalScreeningRequest(BaseModel):
    """Input payload for multimodal screening request."""
    image_path: Optional[str] = Field(
        default=None,
        description="Path to conjunctival photograph (PNG, JPEG, WebP, BMP, TIFF)."
    )
    ppg_csv_path: Optional[str] = Field(
        default=None,
        description="Path to 10s raw ESP32/MAX30102 PPG recording CSV (timestamp_ms,red,ir)."
    )
    age: Optional[float] = Field(
        default=25.0,
        ge=0.0,
        le=130.0,
        description="Patient age in years."
    )
    gender: Optional[str] = Field(
        default="Male",
        description="Patient gender ('Male', 'Female', 'Other')."
    )


# ==============================================================================
# Modality Detail Schemas
# ==============================================================================

class ImageQualitySummary(BaseModel):
    """Quality gate results for the conjunctival photograph."""
    status: str = Field(..., description="'good' or 'poor'")
    score: float = Field(..., ge=0.0, le=1.0, description="Engineering usability score (0-1).")
    checks: Dict[str, str] = Field(default_factory=dict, description="Per-check pass/fail status.")
    reasons: List[str] = Field(default_factory=list, description="Failed check reasons if any.")


class ModalityError(BaseModel):
    """Structured error for a failed or rejected modality."""
    code: str = Field(..., description="Machine-readable error code.")
    message: str = Field(..., description="Human-readable error explanation.")


class ImageModalityResult(BaseModel):
    """Result from the conjunctival image / CV screening model."""
    available: bool = Field(..., description="Whether image modality was supplied.")
    status: str = Field(
        ...,
        description="Execution status: 'SUCCESS', 'REJECTED', 'ERROR', or 'NOT_PROVIDED'."
    )
    label: Optional[str] = Field(
        default=None,
        description="Binary screening prediction: 'anemic' or 'non_anemic'."
    )
    probability: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Random Forest model probability for the anemic class (0-1)."
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Model confidence for the predicted class (0-1)."
    )
    quality_status: Optional[str] = Field(
        default=None,
        description="Image quality gate verdict ('good' or 'poor')."
    )
    quality_score: Optional[float] = Field(
        default=None,
        description="Image quality score (0.0 to 1.0)."
    )
    quality_checks: Optional[Dict[str, str]] = Field(
        default=None,
        description="Detailed pass/fail checks (blur, brightness, contrast, resolution, tissue)."
    )
    quality_reasons: Optional[List[str]] = Field(
        default=None,
        description="List of reasons for quality rejection."
    )
    model_name: Optional[str] = Field(
        default=None,
        description="Underlying AI model identifier."
    )
    inference_latency_ms: Optional[float] = Field(
        default=None,
        description="Image inference latency in milliseconds."
    )
    error: Optional[ModalityError] = Field(
        default=None,
        description="Modality error details if failed or rejected."
    )


class PPGModalityResult(BaseModel):
    """Result from the MAX30102 / ESP32 optical PPG pipeline."""
    available: bool = Field(..., description="Whether PPG modality was supplied.")
    status: str = Field(
        ...,
        description="Execution status: 'SUCCESS', 'REJECTED', 'ERROR', or 'NOT_PROVIDED'."
    )
    predicted_hb_g_dl: Optional[float] = Field(
        default=None,
        description="Predicted total blood Hemoglobin in g/dL."
    )
    signal_quality: Optional[str] = Field(
        default=None,
        description="Signal quality evaluation: 'GOOD' or 'POOR'."
    )
    sqi: Optional[float] = Field(
        default=None,
        description="Mean cardiac Signal Quality Index (0.0 to 1.0)."
    )
    sampling_rate_hz: Optional[float] = Field(
        default=None,
        description="Effective sampling rate measured from hardware timestamps."
    )
    samples: Optional[int] = Field(
        default=None,
        description="Total samples in recording (nominal 250 for 10s @ 25 Hz)."
    )
    duration_sec: Optional[float] = Field(
        default=None,
        description="Recording duration in seconds."
    )
    feature_count: Optional[int] = Field(
        default=None,
        description="Number of verified features extracted (nominal 74)."
    )
    model_name: Optional[str] = Field(
        default=None,
        description="Underlying PPG regression model identifier (Lasso Regression)."
    )
    error: Optional[ModalityError] = Field(
        default=None,
        description="Modality error details if failed or rejected."
    )


class FusionResult(BaseModel):
    """Multimodal fusion layer metadata.
    
    CRITICAL: Because no paired dataset exists, status remains 'NOT_VALIDATED'
    and no unvalidated mathematical combination is performed.
    """
    status: str = Field(
        default="NOT_VALIDATED",
        description="Fusion status. Always 'NOT_VALIDATED' until a clinically paired dataset is available."
    )
    method: Optional[str] = Field(
        default=None,
        description="Fusion method applied (null for unvalidated state)."
    )
    result: Optional[Any] = Field(
        default=None,
        description="Fused score or clinical decision (null for unvalidated state)."
    )
    note: str = Field(
        default=(
            "Statistical multimodal fusion is not performed because no paired dataset "
            "(concurrent conjunctival image + MAX30102 PPG on identical subjects) is currently available. "
            "Modality outputs are preserved independently without unvalidated weighting or conversion."
        ),
        description="Scientific explanation of fusion status."
    )


# ==============================================================================
# Unified Response Schema
# ==============================================================================

class MultimodalScreeningResponse(BaseModel):
    """Top-level unified screening response containing both modality results."""
    success: bool = Field(
        ...,
        description="Whether the screening request succeeded (at least one modality processed)."
    )
    patient: PatientDemographics = Field(
        ...,
        description="Patient demographic metadata."
    )
    image: ImageModalityResult = Field(
        ...,
        description="Conjunctival image model results."
    )
    ppg: PPGModalityResult = Field(
        ...,
        description="Optical PPG model results."
    )
    fusion: FusionResult = Field(
        default_factory=FusionResult,
        description="Multimodal fusion metadata."
    )
    execution_time_ms: Optional[float] = Field(
        default=None,
        description="Total multimodal coordinator execution time in milliseconds."
    )
    error: Optional[ModalityError] = Field(
        default=None,
        description="Top-level error if the entire request failed."
    )
