"""loan loss writeoffs

Revision ID: 0009_loan_loss_writeoffs
Revises: 0008_formula_operations
Create Date: 2026-05-08 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0009_loan_loss_writeoffs"
down_revision = "0008_formula_operations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO chart_accounts (code, name, parent_id, account_nature, is_active, created_at, updated_at)
        SELECT '3.10', 'Perdas com emprestimos', parent.id, 'expense', true, now(), now()
        FROM chart_accounts parent
        WHERE parent.code = '3'
          AND NOT EXISTS (SELECT 1 FROM chart_accounts existing WHERE existing.code = '3.10')
        """
    )
    op.create_table(
        "loan_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("loss_chart_account_id", sa.Integer(), sa.ForeignKey("chart_accounts.id"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "loan_loss_writeoffs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("person_id", sa.Integer(), sa.ForeignKey("loan_people.id"), nullable=False),
        sa.Column("chart_account_id", sa.Integer(), sa.ForeignKey("chart_accounts.id"), nullable=False),
        sa.Column("writeoff_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_loan_loss_writeoffs_id", "loan_loss_writeoffs", ["id"])
    op.create_index("ix_loan_loss_writeoffs_person_id", "loan_loss_writeoffs", ["person_id"])
    op.create_index("ix_loan_loss_writeoffs_chart_account_id", "loan_loss_writeoffs", ["chart_account_id"])
    op.create_index("ix_loan_loss_writeoffs_writeoff_date", "loan_loss_writeoffs", ["writeoff_date"])
    op.execute(
        """
        INSERT INTO loan_settings (id, loss_chart_account_id, updated_at)
        SELECT 1, id, now()
        FROM chart_accounts
        WHERE code = '3.10'
        ON CONFLICT (id) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_index("ix_loan_loss_writeoffs_writeoff_date", table_name="loan_loss_writeoffs")
    op.drop_index("ix_loan_loss_writeoffs_chart_account_id", table_name="loan_loss_writeoffs")
    op.drop_index("ix_loan_loss_writeoffs_person_id", table_name="loan_loss_writeoffs")
    op.drop_index("ix_loan_loss_writeoffs_id", table_name="loan_loss_writeoffs")
    op.drop_table("loan_loss_writeoffs")
    op.drop_table("loan_settings")
