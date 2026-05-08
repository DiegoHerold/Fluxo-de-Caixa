from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.transaction import Transaction


class DuplicateService:
    def __init__(self, db: Session):
        self.db = db

    def exists(self, fingerprint: str) -> bool:
        return self.db.scalar(select(Transaction.id).where(Transaction.fingerprint == fingerprint)) is not None
