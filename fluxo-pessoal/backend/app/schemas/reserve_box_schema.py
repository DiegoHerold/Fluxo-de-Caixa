from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ReserveBoxBase(BaseModel):
    account_id: int
    name: str = Field(..., min_length=2, max_length=120)
    current_balance: Decimal = Decimal("0.00")
    target_amount: Decimal | None = None
    notes: str | None = None
    is_active: bool = True


class ReserveBoxCreate(ReserveBoxBase):
    pass


class ReserveBoxUpdate(BaseModel):
    account_id: int | None = None
    name: str | None = Field(default=None, min_length=2, max_length=120)
    current_balance: Decimal | None = None
    target_amount: Decimal | None = None
    notes: str | None = None
    is_active: bool | None = None


class ReserveBoxRead(ReserveBoxBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
