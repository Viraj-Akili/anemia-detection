from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MeasurementBase(BaseModel):
    screening_id: int
    weight_kg: Optional[float] = Field(None, ge=0, le=300)
    height_cm: Optional[float] = Field(None, ge=0, le=250)
    muac_mm: Optional[float] = Field(None, ge=0, le=500)


class MeasurementCreate(MeasurementBase):
    pass


class MeasurementRead(MeasurementBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)