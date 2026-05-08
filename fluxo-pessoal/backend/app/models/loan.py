from datetime import datetime
from decimal import Decimal

from datetime import date

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import LoanMovementEffect, enum_values


class LoanPerson(Base):
    __tablename__ = "loan_people"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    document: Mapped[str | None] = mapped_column(String(40), index=True)
    phone: Mapped[str | None] = mapped_column(String(40))
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    links = relationship("LoanAccountLink", back_populates="person")


class LoanAccountLink(Base):
    __tablename__ = "loan_account_links"
    __table_args__ = (
        Index(
            "ux_loan_account_links_active_chart_account",
            "chart_account_id",
            unique=True,
            postgresql_where=text("is_active = true"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("loan_people.id"), nullable=False, index=True)
    chart_account_id: Mapped[int] = mapped_column(ForeignKey("chart_accounts.id"), nullable=False, index=True)
    effect: Mapped[LoanMovementEffect] = mapped_column(
        Enum(LoanMovementEffect, values_callable=enum_values), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    person = relationship("LoanPerson", back_populates="links")
    chart_account = relationship("ChartAccount")


class LoanSettings(Base):
    __tablename__ = "loan_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    loss_chart_account_id: Mapped[int | None] = mapped_column(ForeignKey("chart_accounts.id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    loss_chart_account = relationship("ChartAccount")


class LoanLossWriteoff(Base):
    __tablename__ = "loan_loss_writeoffs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("loan_people.id"), nullable=False, index=True)
    chart_account_id: Mapped[int] = mapped_column(ForeignKey("chart_accounts.id"), nullable=False, index=True)
    writeoff_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    person = relationship("LoanPerson")
    chart_account = relationship("ChartAccount")
