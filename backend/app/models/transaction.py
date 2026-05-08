from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Index, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ClassificationStatus, Direction, TransactionSource, TransactionType, enum_values


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint("fingerprint", name="uq_transactions_fingerprint"),
        Index("ix_transactions_date_account", "transaction_date", "account_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    chart_account_id: Mapped[int | None] = mapped_column(ForeignKey("chart_accounts.id"))
    import_batch_id: Mapped[int | None] = mapped_column(ForeignKey("import_batches.id"))
    reserve_box_id: Mapped[int | None] = mapped_column(ForeignKey("reserve_boxes.id", ondelete="SET NULL"), index=True)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    description_original: Mapped[str] = mapped_column(Text, nullable=False)
    description_clean: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    transaction_type: Mapped[TransactionType] = mapped_column(Enum(TransactionType, values_callable=enum_values), nullable=False)
    direction: Mapped[Direction] = mapped_column(Enum(Direction, values_callable=enum_values), nullable=False)
    source: Mapped[TransactionSource] = mapped_column(Enum(TransactionSource, values_callable=enum_values), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(160), index=True)
    fingerprint: Mapped[str] = mapped_column(String(96), nullable=False, index=True)
    classification_status: Mapped[ClassificationStatus] = mapped_column(
        Enum(ClassificationStatus, values_callable=enum_values), nullable=False, default=ClassificationStatus.pending
    )
    is_internal_transfer: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    account = relationship("Account", back_populates="transactions")
    chart_account = relationship("ChartAccount", back_populates="transactions")
    import_batch = relationship("ImportBatch", back_populates="transactions")
    reserve_box = relationship("ReserveBox")
