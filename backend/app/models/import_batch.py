from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ImportStatus, enum_values


class ImportBatch(Base):
    __tablename__ = "import_batches"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    source_bank: Mapped[str] = mapped_column(String(80), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    period_start: Mapped[date | None] = mapped_column(Date)
    period_end: Mapped[date | None] = mapped_column(Date)
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    imported_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duplicated_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[ImportStatus] = mapped_column(
        Enum(ImportStatus, values_callable=enum_values), nullable=False, default=ImportStatus.processing
    )
    error_message: Mapped[str | None] = mapped_column(Text)

    transactions = relationship("Transaction", back_populates="import_batch")
