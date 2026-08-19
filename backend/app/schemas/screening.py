from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ScreeningBase(BaseModel):
    beneficiary_id: int
    worker_id: int
    started_at: datetime
    status: str = Field(default="IN_PROGRESS", pattern="^(IN_PROGRESS|COMPLETED|ABANDONED)$")
    device_id: Optional[str] = Field(None, max_length=100)


class ScreeningCreate(ScreeningBase):
    pass


class ScreeningRead(ScreeningBase):
    id: int
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)