from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BeneficiaryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    date_of_birth: datetime
    sex: str = Field(..., pattern="^(MALE|FEMALE|OTHER)$")
    category: str = Field(..., pattern="^(CHILD|PREGNANT_WOMAN)$")
    is_pregnant: bool = False
    trimester: Optional[int] = Field(None, ge=1, le=3)


class BeneficiaryCreate(BeneficiaryBase):
    pass


class BeneficiaryRead(BeneficiaryBase):
    id: int
    created_by_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)