from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AccountType


class AccountBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    institution: str | None = Field(default=None, max_length=120)
    account_type: AccountType
    initial_balance: Decimal = Decimal("0.00")
    is_active: bool = True


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    institution: str | None = Field(default=None, max_length=120)
    account_type: AccountType | None = None
    initial_balance: Decimal | None = None
    is_active: bool | None = None


class AccountRead(AccountBase):
    id: int
    current_balance: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AccountBalance(BaseModel):
    id: int
    name: str
    institution: str | None
    account_type: AccountType
    initial_balance: Decimal
    calculated_balance: Decimal
    reserve_balance: Decimal
    balance_with_reserves: Decimal
    current_balance: Decimal
    is_active: bool


class ReserveBalance(BaseModel):
    account_id: int
    name: str
    balance: Decimal
    source: str = "detected"


class ConsolidatedBalance(BaseModel):
    available_balance: Decimal
    reserve_balance: Decimal
    consolidated_balance: Decimal
    accounts: list[AccountBalance]
    reserves: list[ReserveBalance]
