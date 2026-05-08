"""formula operations

Revision ID: 0008_formula_operations
Revises: 0007_account_nature_loan
Create Date: 2026-05-08 00:00:00.000000
"""

from alembic import op


revision = "0008_formula_operations"
down_revision = "0007_account_nature_loan"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE formula_operation ADD VALUE IF NOT EXISTS 'multiply'")
        op.execute("ALTER TYPE formula_operation ADD VALUE IF NOT EXISTS 'divide'")


def downgrade() -> None:
    op.execute("UPDATE report_indicator_terms SET operation = 'add' WHERE operation IN ('multiply', 'divide')")
