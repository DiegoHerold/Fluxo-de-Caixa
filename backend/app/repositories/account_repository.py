from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.schemas.account_schema import AccountCreate, AccountUpdate


class AccountRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payload: AccountCreate) -> Account:
        account = Account(
            **payload.model_dump(),
            current_balance=payload.initial_balance,
        )
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account

    def list(self, include_inactive: bool = False) -> list[Account]:
        stmt = select(Account).order_by(Account.name)
        if not include_inactive:
            stmt = stmt.where(Account.is_active.is_(True))
        return list(self.db.scalars(stmt))

    def get(self, account_id: int) -> Account | None:
        return self.db.get(Account, account_id)

    def update(self, account: Account, payload: AccountUpdate) -> Account:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(account, field, value)
        self.db.commit()
        self.db.refresh(account)
        return account

    def deactivate(self, account: Account) -> Account:
        account.is_active = False
        self.db.commit()
        self.db.refresh(account)
        return account
