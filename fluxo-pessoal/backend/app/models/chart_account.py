from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import AccountNature, enum_values


class ChartAccount(Base):
    __tablename__ = "chart_accounts"
    __table_args__ = (UniqueConstraint("code", name="uq_chart_accounts_code"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("chart_accounts.id", ondelete="SET NULL"))
    account_nature: Mapped[AccountNature] = mapped_column(Enum(AccountNature, values_callable=enum_values), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    parent = relationship("ChartAccount", remote_side=[id], back_populates="children")
    children = relationship("ChartAccount", back_populates="parent")
    transactions = relationship("Transaction", back_populates="chart_account")
    rules = relationship("ClassificationRule", back_populates="chart_account")
