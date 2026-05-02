"""reserve boxes

Revision ID: 0002_reserve_boxes
Revises: 0001_initial_schema
Create Date: 2026-05-02 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_reserve_boxes"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reserve_boxes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("current_balance", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("target_amount", sa.Numeric(14, 2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("account_id", "name", name="uq_reserve_boxes_account_name"),
    )
    op.create_index("ix_reserve_boxes_id", "reserve_boxes", ["id"])
    op.create_index("ix_reserve_boxes_account_id", "reserve_boxes", ["account_id"])


def downgrade() -> None:
    op.drop_index("ix_reserve_boxes_account_id", table_name="reserve_boxes")
    op.drop_index("ix_reserve_boxes_id", table_name="reserve_boxes")
    op.drop_table("reserve_boxes")
