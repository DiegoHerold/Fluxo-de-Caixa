"""reserve box chart account

Revision ID: 0010_reserve_box_chart_account
Revises: 0009_loan_loss_writeoffs
Create Date: 2026-05-08 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0010_reserve_box_chart_account"
down_revision = "0009_loan_loss_writeoffs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("reserve_boxes", sa.Column("chart_account_id", sa.Integer(), nullable=True))
    op.create_index("ix_reserve_boxes_chart_account_id", "reserve_boxes", ["chart_account_id"])
    op.create_foreign_key(
        "fk_reserve_boxes_chart_account_id_chart_accounts",
        "reserve_boxes",
        "chart_accounts",
        ["chart_account_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_reserve_boxes_chart_account_id_chart_accounts", "reserve_boxes", type_="foreignkey")
    op.drop_index("ix_reserve_boxes_chart_account_id", table_name="reserve_boxes")
    op.drop_column("reserve_boxes", "chart_account_id")
