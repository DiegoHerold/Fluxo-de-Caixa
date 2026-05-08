from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import MatchType, TransactionType


class ClassificationRuleBase(BaseModel):
    keyword: str = Field(..., min_length=2, max_length=180)
    match_type: MatchType = MatchType.contains
    chart_account_id: int
    transaction_type: TransactionType
    priority: int = 100
    active: bool = True


class ClassificationRuleCreate(ClassificationRuleBase):
    pass


class ClassificationRuleUpdate(BaseModel):
    keyword: str | None = Field(default=None, min_length=2, max_length=180)
    match_type: MatchType | None = None
    chart_account_id: int | None = None
    transaction_type: TransactionType | None = None
    priority: int | None = None
    active: bool | None = None


class ClassificationRuleRead(ClassificationRuleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplyRulesSummary(BaseModel):
    updated: int
    remaining_pending: int
