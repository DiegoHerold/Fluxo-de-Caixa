"""reserve transfer accounts

Revision ID: 0012_reserve_transfer_accounts
Revises: 0011_reserve_nature_transfer
Create Date: 2026-05-08 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0012_reserve_transfer_accounts"
down_revision = "0011_reserve_nature_transfer"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("reserve_boxes", sa.Column("withdrawal_chart_account_id", sa.Integer(), nullable=True))
    op.create_index("ix_reserve_boxes_withdrawal_chart_account_id", "reserve_boxes", ["withdrawal_chart_account_id"])
    op.create_foreign_key(
        "fk_reserve_boxes_withdrawal_chart_account_id_chart_accounts",
        "reserve_boxes",
        "chart_accounts",
        ["withdrawal_chart_account_id"],
        ["id"],
    )

    op.execute(
        """
        INSERT INTO chart_accounts (code, name, parent_id, account_nature, is_active, created_at, updated_at)
        SELECT '5.2', 'Para caixinhas', parent.id, 'transfer', true, now(), now()
        FROM chart_accounts parent
        WHERE parent.code = '5'
          AND NOT EXISTS (SELECT 1 FROM chart_accounts existing WHERE existing.code = '5.2')
        """
    )
    op.execute("UPDATE chart_accounts SET name = 'Para caixinhas', account_nature = 'transfer', is_active = true WHERE code = '5.2'")
    op.execute(
        """
        INSERT INTO chart_accounts (code, name, parent_id, account_nature, is_active, created_at, updated_at)
        SELECT '5.2.1', 'Para reserva emergencia', parent.id, 'transfer', true, now(), now()
        FROM chart_accounts parent
        WHERE parent.code = '5.2'
          AND NOT EXISTS (SELECT 1 FROM chart_accounts existing WHERE existing.code = '5.2.1')
        """
    )
    op.execute(
        """
        INSERT INTO chart_accounts (code, name, parent_id, account_nature, is_active, created_at, updated_at)
        SELECT '5.3', 'De caixinhas para conta', parent.id, 'transfer', true, now(), now()
        FROM chart_accounts parent
        WHERE parent.code = '5'
          AND NOT EXISTS (SELECT 1 FROM chart_accounts existing WHERE existing.code = '5.3')
        """
    )
    op.execute("UPDATE chart_accounts SET name = 'De caixinhas para conta', account_nature = 'transfer', is_active = true WHERE code = '5.3'")
    op.execute(
        """
        INSERT INTO chart_accounts (code, name, parent_id, account_nature, is_active, created_at, updated_at)
        SELECT '5.3.1', 'Da reserva emergencia', parent.id, 'transfer', true, now(), now()
        FROM chart_accounts parent
        WHERE parent.code = '5.3'
          AND NOT EXISTS (SELECT 1 FROM chart_accounts existing WHERE existing.code = '5.3.1')
        """
    )

    op.execute(
        """
        UPDATE transactions tx
        SET chart_account_id = CASE
            WHEN tx.amount >= 0 THEN (SELECT id FROM chart_accounts WHERE code = '5.3' LIMIT 1)
            ELSE (SELECT id FROM chart_accounts WHERE code = '5.2' LIMIT 1)
        END
        WHERE tx.chart_account_id IN (
            SELECT id FROM chart_accounts WHERE code = '8' OR code LIKE '8.%'
        )
        """
    )
    op.execute(
        """
        UPDATE classification_rules
        SET chart_account_id = (SELECT id FROM chart_accounts WHERE code = '5.2' LIMIT 1)
        WHERE chart_account_id IN (SELECT id FROM chart_accounts WHERE code = '8' OR code LIKE '8.%')
        """
    )
    op.execute(
        """
        UPDATE report_indicator_terms
        SET chart_account_id = (SELECT id FROM chart_accounts WHERE code = '5.2' LIMIT 1)
        WHERE chart_account_id IN (SELECT id FROM chart_accounts WHERE code = '8' OR code LIKE '8.%')
        """
    )
    op.execute(
        """
        UPDATE reserve_boxes
        SET chart_account_id = (SELECT id FROM chart_accounts WHERE code = '5.2' LIMIT 1)
        WHERE chart_account_id IN (SELECT id FROM chart_accounts WHERE code = '8' OR code LIKE '8.%')
        """
    )
    op.execute(
        """
        UPDATE loan_account_links
        SET chart_account_id = (SELECT id FROM chart_accounts WHERE code = '5.2' LIMIT 1)
        WHERE chart_account_id IN (SELECT id FROM chart_accounts WHERE code = '8' OR code LIKE '8.%')
        """
    )
    op.execute(
        """
        UPDATE loan_loss_writeoffs
        SET chart_account_id = (SELECT id FROM chart_accounts WHERE code = '5.2' LIMIT 1)
        WHERE chart_account_id IN (SELECT id FROM chart_accounts WHERE code = '8' OR code LIKE '8.%')
        """
    )
    op.execute("DELETE FROM chart_accounts WHERE code LIKE '8.%'")
    op.execute("DELETE FROM chart_accounts WHERE code = '8'")


def downgrade() -> None:
    op.execute(
        """
        INSERT INTO chart_accounts (code, name, parent_id, account_nature, is_active, created_at, updated_at)
        SELECT '8', 'Gastos Planejados com Reservas', NULL, 'transfer', true, now(), now()
        WHERE NOT EXISTS (SELECT 1 FROM chart_accounts WHERE code = '8')
        """
    )
    op.drop_constraint("fk_reserve_boxes_withdrawal_chart_account_id_chart_accounts", "reserve_boxes", type_="foreignkey")
    op.drop_index("ix_reserve_boxes_withdrawal_chart_account_id", table_name="reserve_boxes")
    op.drop_column("reserve_boxes", "withdrawal_chart_account_id")
