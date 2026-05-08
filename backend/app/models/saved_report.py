from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SavedReport(Base):
    __tablename__ = "saved_reports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_default_dashboard: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    indicators = relationship(
        "SavedReportIndicator",
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="SavedReportIndicator.position",
    )


class SavedReportIndicator(Base):
    __tablename__ = "saved_report_indicators"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("saved_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    indicator_id: Mapped[int] = mapped_column(ForeignKey("report_indicators.id", ondelete="CASCADE"), nullable=False, index=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    report = relationship("SavedReport", back_populates="indicators")
    indicator = relationship("ReportIndicator")
