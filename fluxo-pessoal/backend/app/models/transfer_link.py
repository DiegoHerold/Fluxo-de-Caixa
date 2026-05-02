from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import TransferStatus, enum_values


class TransferLink(Base):
    __tablename__ = "transfer_links"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    origin_transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id"), nullable=False)
    destination_transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    transfer_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[TransferStatus] = mapped_column(
        Enum(TransferStatus, values_callable=enum_values), nullable=False, default=TransferStatus.linked
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
