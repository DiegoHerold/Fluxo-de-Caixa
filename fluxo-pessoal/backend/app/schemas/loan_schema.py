from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import LoanMovementEffect


class LoanPersonBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=160)
    document: str | None = Field(default=None, max_length=40)
    phone: str | None = Field(default=None, max_length=40)
    opening_balance: Decimal = Decimal("0.00")
    notes: str | None = None
    is_active: bool = True


class LoanPersonCreate(LoanPersonBase):
    pass


class LoanPersonUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    document: str | None = Field(default=None, max_length=40)
    phone: str | None = Field(default=None, max_length=40)
    opening_balance: Decimal | None = None
    notes: str | None = None
    is_active: bool | None = None


class LoanPersonRead(LoanPersonBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoanPersonSummary(LoanPersonRead):
    current_balance: Decimal
    movement_increase_total: Decimal
    movement_decrease_total: Decimal
    linked_accounts_count: int


class LoanAccountLinkBase(BaseModel):
    person_id: int
    chart_account_id: int
    effect: LoanMovementEffect
    notes: str | None = None
    is_active: bool = True


class LoanAccountLinkCreate(LoanAccountLinkBase):
    pass


class LoanAccountLinkUpdate(BaseModel):
    person_id: int | None = None
    chart_account_id: int | None = None
    effect: LoanMovementEffect | None = None
    notes: str | None = None
    is_active: bool | None = None


class LoanAccountLinkRead(LoanAccountLinkBase):
    id: int
    chart_account_code: str | None = None
    chart_account_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoanMovementRead(BaseModel):
    transaction_id: int
    transaction_date: date
    description: str
    account_name: str | None = None
    chart_account_id: int
    chart_account_code: str | None = None
    chart_account_name: str | None = None
    transaction_amount: Decimal
    effect: LoanMovementEffect
    debt_delta: Decimal
    balance_after: Decimal
