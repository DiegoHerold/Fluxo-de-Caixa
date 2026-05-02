"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-02 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


account_type = postgresql.ENUM(
    "checking", "wallet", "credit_card", "reserve", "investment", "cash", "manual", name="accounttype", create_type=False
)
account_nature = postgresql.ENUM(
    "income", "expense", "transfer", "reserve", "adjustment", "liability", name="accountnature", create_type=False
)
transaction_type = postgresql.ENUM(
    "income",
    "expense",
    "transfer",
    "adjustment",
    "reserve",
    "credit_card_payment",
    name="transactiontype",
    create_type=False,
)
direction = postgresql.ENUM("in", "out", name="direction", create_type=False)
transaction_source = postgresql.ENUM(
    "manual", "nubank_csv", "nubank_ofx", "mercado_pago_xlsx", name="transactionsource", create_type=False
)
classification_status = postgresql.ENUM(
    "pending", "automatic", "manual", "reviewed", name="classificationstatus", create_type=False
)
match_type = postgresql.ENUM("contains", "equals", "starts_with", "regex", name="matchtype", create_type=False)
import_status = postgresql.ENUM(
    "processing", "completed", "failed", "partially_completed", name="importstatus", create_type=False
)
balance_status = postgresql.ENUM("balanced", "divergent", "pending_review", name="balancestatus", create_type=False)
transfer_status = postgresql.ENUM("pending", "linked", "ignored", name="transferstatus", create_type=False)


def upgrade() -> None:
    account_type.create(op.get_bind(), checkfirst=True)
    account_nature.create(op.get_bind(), checkfirst=True)
    transaction_type.create(op.get_bind(), checkfirst=True)
    direction.create(op.get_bind(), checkfirst=True)
    transaction_source.create(op.get_bind(), checkfirst=True)
    classification_status.create(op.get_bind(), checkfirst=True)
    match_type.create(op.get_bind(), checkfirst=True)
    import_status.create(op.get_bind(), checkfirst=True)
    balance_status.create(op.get_bind(), checkfirst=True)
    transfer_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("institution", sa.String(length=120), nullable=True),
        sa.Column("account_type", account_type, nullable=False),
        sa.Column("initial_balance", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("current_balance", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_accounts_id", "accounts", ["id"])

    op.create_table(
        "chart_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("chart_accounts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("account_nature", account_nature, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("code", name="uq_chart_accounts_code"),
    )
    op.create_index("ix_chart_accounts_id", "chart_accounts", ["id"])
    op.create_index("ix_chart_accounts_code", "chart_accounts", ["code"])

    op.create_table(
        "import_batches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("source_bank", sa.String(length=80), nullable=False),
        sa.Column("file_type", sa.String(length=20), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=True),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column("imported_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("total_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("imported_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duplicated_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", import_status, nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.create_index("ix_import_batches_id", "import_batches", ["id"])

    op.create_table(
        "classification_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("keyword", sa.String(length=180), nullable=False),
        sa.Column("match_type", match_type, nullable=False),
        sa.Column("chart_account_id", sa.Integer(), sa.ForeignKey("chart_accounts.id"), nullable=False),
        sa.Column("transaction_type", transaction_type, nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_classification_rules_id", "classification_rules", ["id"])
    op.create_index("ix_classification_rules_keyword", "classification_rules", ["keyword"])

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("chart_account_id", sa.Integer(), sa.ForeignKey("chart_accounts.id"), nullable=True),
        sa.Column("import_batch_id", sa.Integer(), sa.ForeignKey("import_batches.id"), nullable=True),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("description_original", sa.Text(), nullable=False),
        sa.Column("description_clean", sa.Text(), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("transaction_type", transaction_type, nullable=False),
        sa.Column("direction", direction, nullable=False),
        sa.Column("source", transaction_source, nullable=False),
        sa.Column("external_id", sa.String(length=160), nullable=True),
        sa.Column("fingerprint", sa.String(length=96), nullable=False),
        sa.Column("classification_status", classification_status, nullable=False),
        sa.Column("is_internal_transfer", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("fingerprint", name="uq_transactions_fingerprint"),
    )
    op.create_index("ix_transactions_id", "transactions", ["id"])
    op.create_index("ix_transactions_account_id", "transactions", ["account_id"])
    op.create_index("ix_transactions_transaction_date", "transactions", ["transaction_date"])
    op.create_index("ix_transactions_description_clean", "transactions", ["description_clean"])
    op.create_index("ix_transactions_external_id", "transactions", ["external_id"])
    op.create_index("ix_transactions_fingerprint", "transactions", ["fingerprint"])
    op.create_index("ix_transactions_date_account", "transactions", ["transaction_date", "account_id"])

    op.create_table(
        "balance_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("period_month", sa.String(length=7), nullable=False),
        sa.Column("initial_balance", sa.Numeric(14, 2), nullable=False),
        sa.Column("calculated_balance", sa.Numeric(14, 2), nullable=False),
        sa.Column("real_balance", sa.Numeric(14, 2), nullable=True),
        sa.Column("difference", sa.Numeric(14, 2), nullable=True),
        sa.Column("status", balance_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("account_id", "period_month", name="uq_balance_snapshot_account_period"),
    )
    op.create_index("ix_balance_snapshots_id", "balance_snapshots", ["id"])
    op.create_index("ix_balance_snapshots_account_id", "balance_snapshots", ["account_id"])
    op.create_index("ix_balance_snapshots_period_month", "balance_snapshots", ["period_month"])

    op.create_table(
        "transfer_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("origin_transaction_id", sa.Integer(), sa.ForeignKey("transactions.id"), nullable=False),
        sa.Column("destination_transaction_id", sa.Integer(), sa.ForeignKey("transactions.id"), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("transfer_date", sa.Date(), nullable=False),
        sa.Column("status", transfer_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_transfer_links_id", "transfer_links", ["id"])


def downgrade() -> None:
    op.drop_table("transfer_links")
    op.drop_table("balance_snapshots")
    op.drop_table("transactions")
    op.drop_table("classification_rules")
    op.drop_table("import_batches")
    op.drop_table("chart_accounts")
    op.drop_table("accounts")

    transfer_status.drop(op.get_bind(), checkfirst=True)
    balance_status.drop(op.get_bind(), checkfirst=True)
    import_status.drop(op.get_bind(), checkfirst=True)
    match_type.drop(op.get_bind(), checkfirst=True)
    classification_status.drop(op.get_bind(), checkfirst=True)
    transaction_source.drop(op.get_bind(), checkfirst=True)
    direction.drop(op.get_bind(), checkfirst=True)
    transaction_type.drop(op.get_bind(), checkfirst=True)
    account_nature.drop(op.get_bind(), checkfirst=True)
    account_type.drop(op.get_bind(), checkfirst=True)
