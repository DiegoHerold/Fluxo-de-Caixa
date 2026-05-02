from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import MatchType, TransactionType, enum_values


class ClassificationRule(Base):
    __tablename__ = "classification_rules"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    keyword: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    match_type: Mapped[MatchType] = mapped_column(Enum(MatchType, values_callable=enum_values), nullable=False, default=MatchType.contains)
    chart_account_id: Mapped[int] = mapped_column(ForeignKey("chart_accounts.id"), nullable=False)
    transaction_type: Mapped[TransactionType] = mapped_column(Enum(TransactionType, values_callable=enum_values), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    chart_account = relationship("ChartAccount", back_populates="rules")
