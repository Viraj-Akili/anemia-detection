from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ResultBase(BaseModel):
    screening_id: int
    anemia_risk: str = Field(..., pattern="^(LOW|MODERATE|HIGH|CRITICAL)$")
    nutrition_risk: str = Field(..., pattern="^(LOW|MODERATE|HIGH|CRITICAL)$")
    overall_priority: str = Field(..., pattern="^(LOW|MODERATE|HIGH|CRITICAL)$")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    trajectory: Optional[str] = Field(None, max_length=50)
    recommended_action: Optional[str] = None
    contributors: Optional[dict] = None
    model_name: Optional[str] = Field(None, max_length=100)
    model_version: Optional[str] = Field(None, max_length=50)


class ResultCreate(ResultBase):
    pass


class ResultRead(ResultBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)