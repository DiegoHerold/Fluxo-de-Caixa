"""loans

Revision ID: 0006_loans
Revises: 0005_transaction_reserve_box
Create Date: 2026-05-08 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0006_loans"
down_revision = "0005_transaction_reserve_box"
branch_labels = None
depends_on = None


loan_movement_effect = postgresql.ENUM("increase", "decrease", name="loanmovementeffect", create_type=False)


def upgrade() -> None:
    loan_movement_effect.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "loan_people",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("document", sa.String(length=40), nullable=True),
        sa.Column("phone", sa.String(length=40), nullable=True),
        sa.Column("opening_balance", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_loan_people_id", "loan_people", ["id"])
    op.create_index("ix_loan_people_name", "loan_people", ["name"])
    op.create_index("ix_loan_people_document", "loan_people", ["document"])

    op.create_table(
        "loan_account_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("person_id", sa.Integer(), sa.ForeignKey("loan_people.id"), nullable=False),
        sa.Column("chart_account_id", sa.Integer(), sa.ForeignKey("chart_accounts.id"), nullable=False),
        sa.Column("effect", loan_movement_effect, nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_loan_account_links_id", "loan_account_links", ["id"])
    op.create_index("ix_loan_account_links_person_id", "loan_account_links", ["person_id"])
    op.create_index("ix_loan_account_links_chart_account_id", "loan_account_links", ["chart_account_id"])
    op.create_index(
        "ux_loan_account_links_active_chart_account",
        "loan_account_links",
        ["chart_account_id"],
        unique=True,
        postgresql_where=sa.text("is_active = true"),
    )


def downgrade() -> None:
    op.drop_index("ux_loan_account_links_active_chart_account", table_name="loan_account_links")
    op.drop_index("ix_loan_account_links_chart_account_id", table_name="loan_account_links")
    op.drop_index("ix_loan_account_links_person_id", table_name="loan_account_links")
    op.drop_index("ix_loan_account_links_id", table_name="loan_account_links")
    op.drop_table("loan_account_links")
    op.drop_index("ix_loan_people_document", table_name="loan_people")
    op.drop_index("ix_loan_people_name", table_name="loan_people")
    op.drop_index("ix_loan_people_id", table_name="loan_people")
    op.drop_table("loan_people")
    loan_movement_effect.drop(op.get_bind(), checkfirst=True)
