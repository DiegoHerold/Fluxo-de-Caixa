from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import AccountType, enum_values


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    institution: Mapped[str | None] = mapped_column(String(120))
    account_type: Mapped[AccountType] = mapped_column(Enum(AccountType, values_callable=enum_values), nullable=False)
    initial_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    current_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    transactions = relationship("Transaction", back_populates="account")
    balance_snapshots = relationship("BalanceSnapshot", back_populates="account")
    reserve_boxes = relationship("ReserveBox", back_populates="account")
