"""account nature loan

Revision ID: 0007_account_nature_loan
Revises: 0006_loans
Create Date: 2026-05-08 00:00:00.000000
"""

from alembic import op


revision = "0007_account_nature_loan"
down_revision = "0006_loans"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE accountnature ADD VALUE IF NOT EXISTS 'loan'")
    op.execute("UPDATE chart_accounts SET account_nature = 'loan' WHERE code = '7' OR code LIKE '7.%'")


def downgrade() -> None:
    op.execute("UPDATE chart_accounts SET account_nature = 'income' WHERE account_nature = 'loan'")
