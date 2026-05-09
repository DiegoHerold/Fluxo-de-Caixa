from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ReserveBoxBase(BaseModel):
    account_id: int
    chart_account_id: int | None = None
    withdrawal_chart_account_id: int | None = None
    name: str = Field(..., min_length=2, max_length=120)
    current_balance: Decimal = Decimal("0.00")
    target_amount: Decimal | None = None
    notes: str | None = None
    is_active: bool = True


class ReserveBoxCreate(ReserveBoxBase):
    auto_create_chart_accounts: bool = False


class ReserveBoxUpdate(BaseModel):
    account_id: int | None = None
    chart_account_id: int | None = None
    withdrawal_chart_account_id: int | None = None
    name: str | None = Field(default=None, min_length=2, max_length=120)
    current_balance: Decimal | None = None
    target_amount: Decimal | None = None
    notes: str | None = None
    is_active: bool | None = None


class ReserveBoxRead(ReserveBoxBase):
    id: int
    calculated_balance: Decimal | None = None
    chart_account_code: str | None = None
    chart_account_name: str | None = None
    withdrawal_chart_account_code: str | None = None
    withdrawal_chart_account_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
