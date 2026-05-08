"""dashboard reports advanced formulas

Revision ID: 0004_dash_reports
Revises: 0003_report_indicators
Create Date: 2026-05-02 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0004_dash_reports"
down_revision = "0003_report_indicators"
branch_labels = None
depends_on = None


indicator_result_format = postgresql.ENUM("currency", "number", "percent", name="indicator_result_format", create_type=False)
dashboard_widget_type = postgresql.ENUM(
    "indicator",
    "category_bars",
    "account_balances",
    "reserve_boxes",
    "report_download",
    name="dashboard_widget_type",
    create_type=False,
)


def upgrade() -> None:
    postgresql.ENUM("currency", "number", "percent", name="indicator_result_format").create(op.get_bind(), checkfirst=True)
    postgresql.ENUM(
        "indicator",
        "category_bars",
        "account_balances",
        "reserve_boxes",
        "report_download",
        name="dashboard_widget_type",
    ).create(op.get_bind(), checkfirst=True)

    op.add_column("report_indicators", sa.Column("result_format", indicator_result_format, nullable=False, server_default="currency"))
    op.add_column("report_indicators", sa.Column("formula_expression", sa.Text(), nullable=True))
    op.add_column("report_indicator_terms", sa.Column("variable_key", sa.String(length=64), nullable=True))
    op.add_column("report_indicator_terms", sa.Column("weight", sa.Numeric(12, 4), nullable=False, server_default="1"))
    op.add_column("report_indicator_terms", sa.Column("probability", sa.Numeric(6, 4), nullable=False, server_default="1"))

    op.create_table(
        "saved_reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_default_dashboard", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_saved_reports_id", "saved_reports", ["id"])
    op.create_index("ix_saved_reports_display_order", "saved_reports", ["display_order"])

    op.create_table(
        "saved_report_indicators",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("report_id", sa.Integer(), sa.ForeignKey("saved_reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("indicator_id", sa.Integer(), sa.ForeignKey("report_indicators.id", ondelete="CASCADE"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_saved_report_indicators_id", "saved_report_indicators", ["id"])
    op.create_index("ix_saved_report_indicators_report_id", "saved_report_indicators", ["report_id"])
    op.create_index("ix_saved_report_indicators_indicator_id", "saved_report_indicators", ["indicator_id"])

    op.create_table(
        "dashboard_widgets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("widget_type", dashboard_widget_type, nullable=False),
        sa.Column("indicator_id", sa.Integer(), sa.ForeignKey("report_indicators.id", ondelete="SET NULL"), nullable=True),
        sa.Column("saved_report_id", sa.Integer(), sa.ForeignKey("saved_reports.id", ondelete="SET NULL"), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("width", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("height", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_dashboard_widgets_id", "dashboard_widgets", ["id"])
    op.create_index("ix_dashboard_widgets_indicator_id", "dashboard_widgets", ["indicator_id"])
    op.create_index("ix_dashboard_widgets_saved_report_id", "dashboard_widgets", ["saved_report_id"])
    op.create_index("ix_dashboard_widgets_position", "dashboard_widgets", ["position"])


def downgrade() -> None:
    op.drop_index("ix_dashboard_widgets_position", table_name="dashboard_widgets")
    op.drop_index("ix_dashboard_widgets_saved_report_id", table_name="dashboard_widgets")
    op.drop_index("ix_dashboard_widgets_indicator_id", table_name="dashboard_widgets")
    op.drop_index("ix_dashboard_widgets_id", table_name="dashboard_widgets")
    op.drop_table("dashboard_widgets")
    op.drop_index("ix_saved_report_indicators_indicator_id", table_name="saved_report_indicators")
    op.drop_index("ix_saved_report_indicators_report_id", table_name="saved_report_indicators")
    op.drop_index("ix_saved_report_indicators_id", table_name="saved_report_indicators")
    op.drop_table("saved_report_indicators")
    op.drop_index("ix_saved_reports_display_order", table_name="saved_reports")
    op.drop_index("ix_saved_reports_id", table_name="saved_reports")
    op.drop_table("saved_reports")
    op.drop_column("report_indicator_terms", "probability")
    op.drop_column("report_indicator_terms", "weight")
    op.drop_column("report_indicator_terms", "variable_key")
    op.drop_column("report_indicators", "formula_expression")
    op.drop_column("report_indicators", "result_format")
    postgresql.ENUM(
        "indicator",
        "category_bars",
        "account_balances",
        "reserve_boxes",
        "report_download",
        name="dashboard_widget_type",
    ).drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM("currency", "number", "percent", name="indicator_result_format").drop(op.get_bind(), checkfirst=True)
