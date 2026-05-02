from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.balance_snapshot import BalanceSnapshot
from app.models.enums import BalanceStatus
from app.services.balance_service import BalanceService


class ReconciliationService:
    def __init__(self, db: Session):
        self.db = db
        self.balance_service = BalanceService(db)

    def reconcile(self, account_id: int, period_month: str, real_balance: Decimal) -> BalanceSnapshot:
        account = self.db.get(Account, account_id)
        if not account:
            raise ValueError("Conta não encontrada")

        calculated = self.balance_service.calculate_month_balance(account_id, period_month)
        difference = Decimal(real_balance) - Decimal(calculated)
        status = BalanceStatus.balanced if difference == 0 else BalanceStatus.divergent

        snapshot = self.db.scalar(
            select(BalanceSnapshot).where(
                BalanceSnapshot.account_id == account_id,
                BalanceSnapshot.period_month == period_month,
            )
        )
        if snapshot is None:
            snapshot = BalanceSnapshot(
                account_id=account_id,
                period_month=period_month,
                initial_balance=account.initial_balance,
                calculated_balance=calculated,
                real_balance=real_balance,
                difference=difference,
                status=status,
            )
            self.db.add(snapshot)
        else:
            snapshot.initial_balance = account.initial_balance
            snapshot.calculated_balance = calculated
            snapshot.real_balance = real_balance
            snapshot.difference = difference
            snapshot.status = status

        self.db.commit()
        self.db.refresh(snapshot)
        return snapshot
