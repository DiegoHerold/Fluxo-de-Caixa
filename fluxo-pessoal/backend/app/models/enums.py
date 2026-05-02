from enum import StrEnum


def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [item.value for item in enum_cls]


class AccountType(StrEnum):
    checking = "checking"
    wallet = "wallet"
    credit_card = "credit_card"
    reserve = "reserve"
    investment = "investment"
    cash = "cash"
    manual = "manual"


class AccountNature(StrEnum):
    income = "income"
    expense = "expense"
    transfer = "transfer"
    reserve = "reserve"
    adjustment = "adjustment"
    liability = "liability"


class TransactionType(StrEnum):
    income = "income"
    expense = "expense"
    transfer = "transfer"
    adjustment = "adjustment"
    reserve = "reserve"
    credit_card_payment = "credit_card_payment"


class Direction(StrEnum):
    in_ = "in"
    out = "out"


class ClassificationStatus(StrEnum):
    pending = "pending"
    automatic = "automatic"
    manual = "manual"
    reviewed = "reviewed"


class TransactionSource(StrEnum):
    manual = "manual"
    nubank_csv = "nubank_csv"
    nubank_ofx = "nubank_ofx"
    mercado_pago_xlsx = "mercado_pago_xlsx"


class MatchType(StrEnum):
    contains = "contains"
    equals = "equals"
    starts_with = "starts_with"
    regex = "regex"


class ImportStatus(StrEnum):
    processing = "processing"
    completed = "completed"
    failed = "failed"
    partially_completed = "partially_completed"


class BalanceStatus(StrEnum):
    balanced = "balanced"
    divergent = "divergent"
    pending_review = "pending_review"


class TransferStatus(StrEnum):
    pending = "pending"
    linked = "linked"
    ignored = "ignored"


class FormulaOperation(StrEnum):
    add = "add"
    subtract = "subtract"


class FormulaValueMode(StrEnum):
    net = "net"
    inflow = "inflow"
    outflow = "outflow"
    absolute = "absolute"


class IndicatorResultFormat(StrEnum):
    currency = "currency"
    number = "number"
    percent = "percent"


class DashboardWidgetType(StrEnum):
    indicator = "indicator"
    category_bars = "category_bars"
    account_balances = "account_balances"
    reserve_boxes = "reserve_boxes"
    report_download = "report_download"
