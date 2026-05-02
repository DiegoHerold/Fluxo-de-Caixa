from decimal import Decimal

from datetime import date

from sqlalchemy import and_, func, not_, or_, select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.balance_snapshot import BalanceSnapshot
from app.models.chart_account import ChartAccount
from app.models.enums import AccountNature, BalanceStatus, ClassificationStatus, TransactionType
from app.models.transaction import Transaction
from app.schemas.report_schema import CategoryReportItem, ComparisonReportItem, MonthlyReport
from app.services.balance_service import BalanceService
from app.utils.dates import month_bounds


class ReportService:
    def __init__(self, db: Session):
        self.db = db
        self.balance_service = BalanceService(db)

    def monthly(self, month: str) -> MonthlyReport:
        start, end = month_bounds(month)
        opening_balance = sum(
            (self.balance_service.calculate_account_balance(account.id, until=start) for account in self.db.scalars(select(Account))),
            Decimal("0.00"),
        )
        base = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.transaction_date >= start,
            Transaction.transaction_date < end,
        )
        income = self.db.scalar(
            base.where(Transaction.transaction_type == TransactionType.income, Transaction.is_internal_transfer.is_(False))
        ) or Decimal("0.00")
        expenses = self.db.scalar(
            base.where(Transaction.transaction_type == TransactionType.expense, Transaction.is_internal_transfer.is_(False))
        ) or Decimal("0.00")
        obligation_condition = self._obligation_condition()
        fixed_expenses = self._real_expense_total(start, end, and_(self._code_root_condition("2"), not_(obligation_condition)))
        variable_expenses = self._real_expense_total(start, end, and_(self._code_root_condition("3"), not_(obligation_condition)))
        obligations = self._real_expense_total(start, end, obligation_condition)
        known_real_expense_condition = or_(
            self._code_root_condition("2"),
            self._code_root_condition("3"),
            obligation_condition,
        )
        other_expenses = self._real_expense_total(start, end, or_(ChartAccount.id.is_(None), not_(known_real_expense_condition)))
        total_real_expenses = fixed_expenses + variable_expenses + obligations + other_expenses
        cash_result = income - total_real_expenses
        transfers = self.db.scalar(base.where(Transaction.transaction_type == TransactionType.transfer)) or Decimal("0.00")
        reserves = self.db.scalar(base.where(Transaction.transaction_type == TransactionType.reserve)) or Decimal("0.00")
        adjustments = self.db.scalar(base.where(Transaction.transaction_type == TransactionType.adjustment)) or Decimal("0.00")
        pending_count = self.db.scalar(
            select(func.count(Transaction.id)).where(
                Transaction.transaction_date >= start,
                Transaction.transaction_date < end,
                Transaction.classification_status == ClassificationStatus.pending,
            )
        ) or 0
        consolidated = self.balance_service.calculate_consolidated_balance().consolidated_balance
        return MonthlyReport(
            month=month,
            opening_balance=opening_balance,
            income=income,
            expenses=expenses,
            fixed_expenses=fixed_expenses,
            variable_expenses=variable_expenses,
            obligations=obligations,
            other_expenses=other_expenses,
            total_real_expenses=total_real_expenses,
            transfers=transfers,
            reserves=reserves,
            adjustments=adjustments,
            result=cash_result,
            cash_result=cash_result,
            pending_count=pending_count,
            consolidated_balance=consolidated,
        )

    def categories(self, month: str) -> list[CategoryReportItem]:
        start, end = month_bounds(month)
        stmt = (
            select(
                Transaction.chart_account_id,
                ChartAccount.code,
                ChartAccount.name,
                ChartAccount.account_nature,
                func.coalesce(func.sum(Transaction.amount), 0),
                func.count(Transaction.id),
            )
            .join(ChartAccount, ChartAccount.id == Transaction.chart_account_id, isouter=True)
            .where(
                Transaction.transaction_date >= start,
                Transaction.transaction_date < end,
                Transaction.is_internal_transfer.is_(False),
            )
            .group_by(Transaction.chart_account_id, ChartAccount.code, ChartAccount.name, ChartAccount.account_nature)
            .order_by(func.abs(func.coalesce(func.sum(Transaction.amount), 0)).desc())
        )
        return [
            CategoryReportItem(
                chart_account_id=row[0],
                code=row[1],
                name=row[2] or "Sem categoria",
                account_nature=row[3].value if row[3] else None,
                total=row[4],
                count=row[5],
            )
            for row in self.db.execute(stmt)
        ]

    def comparison(self, start_month: str, end_month: str) -> list[ComparisonReportItem]:
        items: list[ComparisonReportItem] = []
        for month in self._iter_months(start_month, end_month):
            report = self.monthly(month)
            items.append(
                ComparisonReportItem(
                    month=month,
                    income=report.income,
                    expenses=report.expenses,
                    fixed_expenses=report.fixed_expenses,
                    variable_expenses=report.variable_expenses,
                    obligations=report.obligations,
                    other_expenses=report.other_expenses,
                    total_real_expenses=report.total_real_expenses,
                    result=report.cash_result,
                    cash_result=report.cash_result,
                    pending_count=report.pending_count,
                )
            )
        return items

    def divergent_snapshots_count(self) -> int:
        return self.db.scalar(
            select(func.count(BalanceSnapshot.id)).where(BalanceSnapshot.status == BalanceStatus.divergent)
        ) or 0

    def _real_expense_total(self, start: date, end: date, bucket_condition) -> Decimal:
        stmt = (
            select(func.coalesce(func.sum(Transaction.amount), 0))
            .join(ChartAccount, ChartAccount.id == Transaction.chart_account_id, isouter=True)
            .where(
                Transaction.transaction_date >= start,
                Transaction.transaction_date < end,
                Transaction.is_internal_transfer.is_(False),
                Transaction.transaction_type.in_([TransactionType.expense, TransactionType.credit_card_payment]),
                bucket_condition,
            )
        )
        return -(self.db.scalar(stmt) or Decimal("0.00"))

    def _code_root_condition(self, root_code: str):
        return or_(ChartAccount.code == root_code, ChartAccount.code.like(f"{root_code}.%"))

    def _obligation_condition(self):
        return or_(
            self._code_root_condition("4"),
            ChartAccount.account_nature == AccountNature.liability,
            Transaction.transaction_type == TransactionType.credit_card_payment,
        )

    def _iter_months(self, start_month: str, end_month: str):
        start, _ = month_bounds(start_month)
        _, limit = month_bounds(end_month)
        current = date(start.year, start.month, 1)
        while current < limit:
            yield f"{current.year:04d}-{current.month:02d}"
            current = date(current.year + (1 if current.month == 12 else 0), 1 if current.month == 12 else current.month + 1, 1)
