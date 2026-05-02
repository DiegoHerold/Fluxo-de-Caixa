from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import BalanceStatus, enum_values


class BalanceSnapshot(Base):
    __tablename__ = "balance_snapshots"
    __table_args__ = (UniqueConstraint("account_id", "period_month", name="uq_balance_snapshot_account_period"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    period_month: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    initial_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    calculated_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    real_balance: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    difference: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    status: Mapped[BalanceStatus] = mapped_column(
        Enum(BalanceStatus, values_callable=enum_values), nullable=False, default=BalanceStatus.pending_review
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    account = relationship("Account", back_populates="balance_snapshots")
