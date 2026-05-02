from decimal import Decimal

from pydantic import BaseModel


class MonthlyReport(BaseModel):
    month: str
    opening_balance: Decimal
    income: Decimal
    expenses: Decimal
    fixed_expenses: Decimal
    variable_expenses: Decimal
    obligations: Decimal
    other_expenses: Decimal
    total_real_expenses: Decimal
    transfers: Decimal
    reserves: Decimal
    adjustments: Decimal
    result: Decimal
    cash_result: Decimal
    pending_count: int
    consolidated_balance: Decimal


class CategoryReportItem(BaseModel):
    chart_account_id: int | None
    code: str | None
    name: str
    account_nature: str | None
    total: Decimal
    count: int


class ComparisonReportItem(BaseModel):
    month: str
    income: Decimal
    expenses: Decimal
    fixed_expenses: Decimal
    variable_expenses: Decimal
    obligations: Decimal
    other_expenses: Decimal
    total_real_expenses: Decimal
    result: Decimal
    cash_result: Decimal
    pending_count: int
