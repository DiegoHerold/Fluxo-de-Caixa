from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import FormulaOperation, FormulaValueMode, IndicatorResultFormat


class ReportIndicatorTermBase(BaseModel):
    chart_account_id: int
    operation: FormulaOperation = FormulaOperation.add
    value_mode: FormulaValueMode = FormulaValueMode.outflow
    variable_key: str | None = Field(default=None, max_length=64)
    weight: Decimal = Decimal("1")
    probability: Decimal = Decimal("1")
    include_children: bool = True
    label: str | None = Field(default=None, max_length=120)
    position: int = 0


class ReportIndicatorTermCreate(ReportIndicatorTermBase):
    pass


class ReportIndicatorTermRead(ReportIndicatorTermBase):
    id: int
    chart_account_code: str | None = None
    chart_account_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ReportIndicatorBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    description: str | None = None
    result_label: str = Field(default="Resultado", max_length=80)
    result_format: IndicatorResultFormat = IndicatorResultFormat.currency
    formula_expression: str | None = None
    positive_is_good: bool = True
    include_internal_transfers: bool = False
    show_on_dashboard: bool = True
    show_on_reports: bool = True
    display_order: int = 100
    is_active: bool = True


class ReportIndicatorCreate(ReportIndicatorBase):
    terms: list[ReportIndicatorTermCreate] = Field(default_factory=list)


class ReportIndicatorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = None
    result_label: str | None = Field(default=None, max_length=80)
    result_format: IndicatorResultFormat | None = None
    formula_expression: str | None = None
    positive_is_good: bool | None = None
    include_internal_transfers: bool | None = None
    show_on_dashboard: bool | None = None
    show_on_reports: bool | None = None
    display_order: int | None = None
    is_active: bool | None = None
    terms: list[ReportIndicatorTermCreate] | None = None


class ReportIndicatorRead(ReportIndicatorBase):
    id: int
    terms: list[ReportIndicatorTermRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReportIndicatorTermEvaluation(BaseModel):
    label: str
    chart_account_id: int
    chart_account_code: str
    chart_account_name: str
    operation: FormulaOperation
    value_mode: FormulaValueMode
    include_children: bool
    variable_key: str | None
    weight: Decimal
    probability: Decimal
    amount: Decimal
    adjusted_amount: Decimal
    contribution: Decimal


class ReportIndicatorEvaluation(BaseModel):
    id: int
    name: str
    description: str | None
    result_label: str
    result_format: IndicatorResultFormat
    formula_expression: str | None
    positive_is_good: bool
    include_internal_transfers: bool
    show_on_dashboard: bool
    show_on_reports: bool
    display_order: int
    result: Decimal
    terms: list[ReportIndicatorTermEvaluation]
