from datetime import datetime

from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import FormulaOperation, FormulaValueMode, IndicatorResultFormat, enum_values


class ReportIndicator(Base):
    __tablename__ = "report_indicators"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    result_label: Mapped[str] = mapped_column(String(80), nullable=False, default="Resultado")
    result_format: Mapped[IndicatorResultFormat] = mapped_column(
        Enum(IndicatorResultFormat, values_callable=enum_values, name="indicator_result_format"),
        nullable=False,
        default=IndicatorResultFormat.currency,
    )
    formula_expression: Mapped[str | None] = mapped_column(Text)
    positive_is_good: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    include_internal_transfers: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    show_on_dashboard: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    show_on_reports: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    terms = relationship(
        "ReportIndicatorTerm",
        back_populates="indicator",
        cascade="all, delete-orphan",
        order_by="ReportIndicatorTerm.position",
    )


class ReportIndicatorTerm(Base):
    __tablename__ = "report_indicator_terms"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    indicator_id: Mapped[int] = mapped_column(ForeignKey("report_indicators.id", ondelete="CASCADE"), nullable=False, index=True)
    chart_account_id: Mapped[int] = mapped_column(ForeignKey("chart_accounts.id"), nullable=False, index=True)
    operation: Mapped[FormulaOperation] = mapped_column(Enum(FormulaOperation, values_callable=enum_values, name="formula_operation"), nullable=False)
    value_mode: Mapped[FormulaValueMode] = mapped_column(Enum(FormulaValueMode, values_callable=enum_values, name="formula_value_mode"), nullable=False)
    variable_key: Mapped[str | None] = mapped_column(String(64))
    weight: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=Decimal("1"))
    probability: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False, default=Decimal("1"))
    include_children: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    label: Mapped[str | None] = mapped_column(String(120))
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    indicator = relationship("ReportIndicator", back_populates="terms")
    chart_account = relationship("ChartAccount")
