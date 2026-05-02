from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import ClassificationStatus, TransactionSource, TransactionType
from app.models.transaction import Transaction


class TransactionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, transaction_id: int) -> Transaction | None:
        return self.db.get(Transaction, transaction_id)

    def exists_fingerprint(self, fingerprint: str) -> bool:
        return self.db.scalar(select(Transaction.id).where(Transaction.fingerprint == fingerprint)) is not None

    def create(self, payload: dict) -> Transaction:
        transaction = Transaction(**payload)
        self.db.add(transaction)
        self.db.flush()
        return transaction

    def list(
        self,
        *,
        account_id: int | None = None,
        chart_account_id: int | None = None,
        status: ClassificationStatus | None = None,
        source: TransactionSource | None = None,
        transaction_type: TransactionType | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> list[Transaction]:
        stmt = select(Transaction).order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
        if account_id:
            stmt = stmt.where(Transaction.account_id == account_id)
        if chart_account_id:
            stmt = stmt.where(Transaction.chart_account_id == chart_account_id)
        if status:
            stmt = stmt.where(Transaction.classification_status == status)
        if source:
            stmt = stmt.where(Transaction.source == source)
        if transaction_type:
            stmt = stmt.where(Transaction.transaction_type == transaction_type)
        if start_date:
            stmt = stmt.where(Transaction.transaction_date >= start_date)
        if end_date:
            stmt = stmt.where(Transaction.transaction_date <= end_date)
        stmt = stmt.offset(offset).limit(limit)
        return list(self.db.scalars(stmt))

    def pending(self, limit: int = 500) -> list[Transaction]:
        stmt = (
            select(Transaction)
            .where(Transaction.classification_status == ClassificationStatus.pending)
            .order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt))
