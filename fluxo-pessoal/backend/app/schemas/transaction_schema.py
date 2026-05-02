from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ClassificationStatus, Direction, TransactionSource, TransactionType
from app.models.enums import MatchType


class TransactionBase(BaseModel):
    account_id: int
    chart_account_id: int | None = None
    transaction_date: date
    description_original: str = Field(..., min_length=1)
    amount: Decimal
    transaction_type: TransactionType | None = None
    direction: Direction | None = None
    notes: str | None = None
    is_internal_transfer: bool = False


class ManualTransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    account_id: int | None = None
    chart_account_id: int | None = None
    transaction_date: date | None = None
    description_original: str | None = None
    amount: Decimal | None = None
    transaction_type: TransactionType | None = None
    direction: Direction | None = None
    classification_status: ClassificationStatus | None = None
    is_internal_transfer: bool | None = None
    notes: str | None = None


class TransactionRead(BaseModel):
    id: int
    account_id: int
    chart_account_id: int | None
    import_batch_id: int | None
    transaction_date: date
    description_original: str
    description_clean: str
    amount: Decimal
    transaction_type: TransactionType
    direction: Direction
    source: TransactionSource
    external_id: str | None
    fingerprint: str
    classification_status: ClassificationStatus
    is_internal_transfer: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransactionListItem(TransactionRead):
    account_name: str | None = None
    chart_account_code: str | None = None
    chart_account_name: str | None = None


class TransactionClassifyRequest(BaseModel):
    chart_account_id: int
    transaction_type: TransactionType
    is_internal_transfer: bool = False
    notes: str | None = None
    create_rule: bool = False
    rule_keyword: str | None = Field(default=None, min_length=2)
    rule_match_type: MatchType = MatchType.equals
    rule_priority: int = 10


class RuleFromClassificationRequest(BaseModel):
    keyword: str = Field(..., min_length=2)
    match_type: MatchType = MatchType.contains
    priority: int = 100
