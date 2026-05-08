"""reserve nature transfer

Revision ID: 0011_reserve_nature_transfer
Revises: 0010_reserve_box_chart_account
Create Date: 2026-05-08 00:00:00.000000
"""

from alembic import op


revision = "0011_reserve_nature_transfer"
down_revision = "0010_reserve_box_chart_account"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE chart_accounts SET account_nature = 'transfer' WHERE account_nature = 'reserve'")


def downgrade() -> None:
    op.execute("UPDATE chart_accounts SET account_nature = 'reserve' WHERE code = '8' OR code LIKE '8.%'")
