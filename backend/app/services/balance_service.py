from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.transaction import Transaction
from app.schemas.account_schema import AccountBalance, ConsolidatedBalance, ReserveBalance
from app.services.reserve_service import ReserveService
from app.utils.dates import month_bounds


class BalanceService:
    def __init__(self, db: Session):
        self.db = db

    def calculate_account_balance(self, account_id: int, until: date | None = None) -> Decimal:
        account = self.db.get(Account, account_id)
        if not account:
            raise ValueError("Conta não encontrada")

        stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(Transaction.account_id == account_id)
        if until:
            stmt = stmt.where(Transaction.transaction_date < until)
        total = self.db.scalar(stmt) or Decimal("0.00")
        return Decimal(account.initial_balance) + Decimal(total)

    def calculate_month_balance(self, account_id: int, period_month: str) -> Decimal:
        _, end = month_bounds(period_month)
        return self.calculate_account_balance(account_id, until=end)

    def calculate_all_balances(self) -> list[AccountBalance]:
        accounts = self.db.scalars(select(Account).order_by(Account.name)).all()
        balances: list[AccountBalance] = []
        reserve_service = ReserveService(self.db)
        for account in accounts:
            calculated = self.calculate_account_balance(account.id)
            reserve_balance = reserve_service.calculate_account_reserve_balance(account.id)
            balances.append(
                AccountBalance(
                    id=account.id,
                    name=account.name,
                    institution=account.institution,
                    account_type=account.account_type,
                    initial_balance=account.initial_balance,
                    calculated_balance=calculated,
                    reserve_balance=reserve_balance,
                    balance_with_reserves=calculated + reserve_balance,
                    current_balance=account.current_balance,
                    is_active=account.is_active,
                )
            )
        return balances

    def calculate_consolidated_balance(self) -> ConsolidatedBalance:
        balances = self.calculate_all_balances()
        reserves = [ReserveBalance(**item) for item in ReserveService(self.db).calculate_reserves()]
        available_total = sum((item.calculated_balance for item in balances), Decimal("0.00"))
        reserve_total = sum((max(item.balance, Decimal("0.00")) for item in reserves), Decimal("0.00"))
        return ConsolidatedBalance(
            available_balance=available_total,
            reserve_balance=reserve_total,
            consolidated_balance=available_total + reserve_total,
            accounts=balances,
            reserves=reserves,
        )

    def recalculate_balances(self) -> None:
        accounts = self.db.scalars(select(Account)).all()
        for account in accounts:
            account.current_balance = self.calculate_account_balance(account.id)
        self.db.commit()
