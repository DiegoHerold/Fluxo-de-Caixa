"""transaction reserve_box_id

Revision ID: 0005_transaction_reserve_box
Revises: 0004_dash_reports
Create Date: 2026-05-02 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0005_transaction_reserve_box"
down_revision = "0004_dash_reports"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "transactions",
        sa.Column("reserve_box_id", sa.Integer(), sa.ForeignKey("reserve_boxes.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_transactions_reserve_box_id", "transactions", ["reserve_box_id"])


def downgrade() -> None:
    op.drop_index("ix_transactions_reserve_box_id", table_name="transactions")
    op.drop_column("transactions", "reserve_box_id")
