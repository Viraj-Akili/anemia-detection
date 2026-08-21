"""Pydantic schemas for the PRAHARI anemia screening API.

Defines the explicit request/response contract so the frontend, Swayam,
and Arya can integrate against stable JSON shapes.

Medical rule: the model outputs a binary screening signal (anemic /
non_anemic) exactly as the dataset defines it.  No severity classes are
invented here — final risk determination is Swayam's responsibility.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ---- prediction ----------------------------------------------------------

class Prediction(BaseModel):
    """Model prediction for a single image."""

    label: str = Field(
        ...,
        description="Predicted class: 'anemic' or 'non_anemic' (dataset labels).",
        examples=["anemic"],
    )
    model_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Random Forest model probability for the anemic class (0-1).",
        examples=[0.912],
    )
    model_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Model probability for the predicted class (0-1).",
        examples=[0.912],
    )


# ---- image quality -------------------------------------------------------

class ImageQuality(BaseModel):
    """Quality gate result for the uploaded image."""

    status: str = Field(
        ...,
        description="'good' or 'poor'.",
        examples=["good"],
    )
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Engineering quality score (0-1). Higher is better.",
        examples=[1.0],
    )
    checks: dict[str, str] = Field(
        default_factory=dict,
        description="Per-check pass/fail status.",
        examples=[{"blur": "pass", "brightness": "pass", "contrast": "pass", "resolution": "pass", "tissue": "pass"}],
    )
    reasons: list[str] = Field(
        default_factory=list,
        description="List of failed check names (empty when quality is good).",
        examples=[[]],
    )


# ---- inference metadata --------------------------------------------------

class InferenceMetadata(BaseModel):
    """Metadata about the model and timing for a single inference call."""

    model: str = Field(..., description="Model identifier.", examples=["random_forest_color_baseline"])
    version: str = Field(..., description="Model version string.", examples=["1.0"])
    latency_ms: float = Field(..., description="Total inference latency in milliseconds.", examples=[58.4])


# ---- error body ----------------------------------------------------------

class ErrorDetail(BaseModel):
    """Structured error returned when screening fails."""

    code: str = Field(..., description="Machine-readable error code.", examples=["IMAGE_QUALITY_LOW"])
    message: str = Field(
        ...,
        description="Human-readable error message.",
        examples=["Image quality is insufficient. Please retake the image."],
    )


# ---- top-level responses -------------------------------------------------

class AnemiaScreenSuccess(BaseModel):
    """Successful screening response."""

    success: bool = Field(True, description="Whether the screening succeeded.")
    prediction: Prediction
    image_quality: ImageQuality
    inference: InferenceMetadata


class AnemiaScreenFailure(BaseModel):
    """Failed screening response (quality rejection)."""

    success: bool = Field(False, description="Whether the screening succeeded.")
    prediction: None = Field(None)
    image_quality: ImageQuality
    inference: None = Field(None)
    error: ErrorDetail


class AnemiaScreenResponse(BaseModel):
    """Union response — the actual API returns either success or failure shape.

    For OpenAPI docs we use a generic dict; the explicit models above are
    for client-side type generation and documentation.
    """

    class Config:
        # Allow arbitrary dict from the engine's analyse() output.
        arbitrary_types_allowed = True

    success: bool
    prediction: dict[str, Any] | None = None
    image_quality: dict[str, Any] | None = None
    inference: dict[str, Any] | None = None
    error: dict[str, Any] | None = None


# ---- health / models -----------------------------------------------------

class HealthResponse(BaseModel):
    """GET /health response."""

    status: str = Field(..., examples=["ok"])
    model_loaded: bool
    model: str = Field(..., examples=["random_forest_color_baseline"])
    version: str = Field(..., examples=["1.0"])


class ModelInfo(BaseModel):
    """GET /models response — metadata about the loaded model."""

    name: str
    version: str
    type: str
    dataset: str
    labels: list[str]
    feature_pipeline: str
    training_seed: int
    notes: str
