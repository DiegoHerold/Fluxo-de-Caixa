from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import BalanceStatus


class ReconcileRequest(BaseModel):
    account_id: int
    period_month: str = Field(..., pattern=r"^\d{4}-\d{2}$")
    real_balance: Decimal


class BalanceSnapshotRead(BaseModel):
    id: int
    account_id: int
    period_month: str
    initial_balance: Decimal
    calculated_balance: Decimal
    real_balance: Decimal | None
    difference: Decimal | None
    status: BalanceStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
