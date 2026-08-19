from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class FollowUpBase(BaseModel):
    beneficiary_id: int
    assigned_user_id: int
    due_date: datetime
    reason: str = Field(..., min_length=1)
    screening_id: Optional[int] = None
    status: str = Field(default="PENDING", pattern="^(PENDING|COMPLETED|OVERDUE|CANCELLED)$")
    notes: Optional[str] = None


class FollowUpCreate(FollowUpBase):
    pass


class FollowUpRead(FollowUpBase):
    id: int
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)