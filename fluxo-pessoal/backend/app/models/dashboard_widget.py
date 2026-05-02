from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import DashboardWidgetType, enum_values


class DashboardWidget(Base):
    __tablename__ = "dashboard_widgets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    widget_type: Mapped[DashboardWidgetType] = mapped_column(
        Enum(DashboardWidgetType, values_callable=enum_values, name="dashboard_widget_type"),
        nullable=False,
    )
    indicator_id: Mapped[int | None] = mapped_column(ForeignKey("report_indicators.id", ondelete="SET NULL"), index=True)
    saved_report_id: Mapped[int | None] = mapped_column(ForeignKey("saved_reports.id", ondelete="SET NULL"), index=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    width: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    height: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    indicator = relationship("ReportIndicator")
    saved_report = relationship("SavedReport")
