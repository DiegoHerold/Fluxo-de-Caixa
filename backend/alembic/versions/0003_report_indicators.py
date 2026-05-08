"""report indicators

Revision ID: 0003_report_indicators
Revises: 0002_reserve_boxes
Create Date: 2026-05-02 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0003_report_indicators"
down_revision = "0002_reserve_boxes"
branch_labels = None
depends_on = None


formula_operation = postgresql.ENUM("add", "subtract", name="formula_operation", create_type=False)
formula_value_mode = postgresql.ENUM("net", "inflow", "outflow", "absolute", name="formula_value_mode", create_type=False)


def upgrade() -> None:
    postgresql.ENUM("add", "subtract", name="formula_operation").create(op.get_bind(), checkfirst=True)
    postgresql.ENUM("net", "inflow", "outflow", "absolute", name="formula_value_mode").create(op.get_bind(), checkfirst=True)

    op.create_table(
        "report_indicators",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("result_label", sa.String(length=80), nullable=False, server_default="Resultado"),
        sa.Column("positive_is_good", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("include_internal_transfers", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("show_on_dashboard", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("show_on_reports", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_report_indicators_id", "report_indicators", ["id"])
    op.create_index("ix_report_indicators_display_order", "report_indicators", ["display_order"])

    op.create_table(
        "report_indicator_terms",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("indicator_id", sa.Integer(), sa.ForeignKey("report_indicators.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chart_account_id", sa.Integer(), sa.ForeignKey("chart_accounts.id"), nullable=False),
        sa.Column("operation", formula_operation, nullable=False),
        sa.Column("value_mode", formula_value_mode, nullable=False),
        sa.Column("include_children", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("label", sa.String(length=120), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_report_indicator_terms_id", "report_indicator_terms", ["id"])
    op.create_index("ix_report_indicator_terms_indicator_id", "report_indicator_terms", ["indicator_id"])
    op.create_index("ix_report_indicator_terms_chart_account_id", "report_indicator_terms", ["chart_account_id"])


def downgrade() -> None:
    op.drop_index("ix_report_indicator_terms_chart_account_id", table_name="report_indicator_terms")
    op.drop_index("ix_report_indicator_terms_indicator_id", table_name="report_indicator_terms")
    op.drop_index("ix_report_indicator_terms_id", table_name="report_indicator_terms")
    op.drop_table("report_indicator_terms")
    op.drop_index("ix_report_indicators_display_order", table_name="report_indicators")
    op.drop_index("ix_report_indicators_id", table_name="report_indicators")
    op.drop_table("report_indicators")
    postgresql.ENUM("net", "inflow", "outflow", "absolute", name="formula_value_mode").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM("add", "subtract", name="formula_operation").drop(op.get_bind(), checkfirst=True)
