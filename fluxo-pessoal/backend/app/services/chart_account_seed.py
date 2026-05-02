from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.chart_account import ChartAccount
from app.models.classification_rule import ClassificationRule
from app.models.enums import AccountNature
from app.models.transaction import Transaction
from app.repositories.chart_account_repository import ChartAccountRepository
from app.schemas.chart_account_schema import ChartAccountCreate


DEFAULT_CHART_ACCOUNTS: list[tuple[str, str, str | None, AccountNature]] = [
    ("1", "Receitas", None, AccountNature.income),
    ("1.1", "Salário", "1", AccountNature.income),
    ("1.2", "Adiantamento", "1", AccountNature.income),
    ("1.3", "Reembolso", "1", AccountNature.income),
    ("1.4", "Pix recebido", "1", AccountNature.income),
    ("1.5", "Venda", "1", AccountNature.income),
    ("1.6", "Outros recebimentos", "1", AccountNature.income),
    ("2", "Despesas Fixas", None, AccountNature.expense),
    ("2.1", "Aluguel", "2", AccountNature.expense),
    ("2.2", "Água", "2", AccountNature.expense),
    ("2.3", "Luz", "2", AccountNature.expense),
    ("2.4", "Internet", "2", AccountNature.expense),
    ("2.5", "Telefone", "2", AccountNature.expense),
    ("2.6", "Academia", "2", AccountNature.expense),
    ("2.7", "Assinaturas", "2", AccountNature.expense),
    ("3", "Despesas Variáveis", None, AccountNature.expense),
    ("3.1", "Alimentação", "3", AccountNature.expense),
    ("3.2", "Mercado", "3", AccountNature.expense),
    ("3.3", "Restaurante/Lanche", "3", AccountNature.expense),
    ("3.4", "Transporte", "3", AccountNature.expense),
    ("3.5", "Combustível", "3", AccountNature.expense),
    ("3.6", "Saúde", "3", AccountNature.expense),
    ("3.7", "Farmácia", "3", AccountNature.expense),
    ("3.8", "Roupas", "3", AccountNature.expense),
    ("3.9", "Lazer", "3", AccountNature.expense),
    ("3.10", "Compras pessoais", "3", AccountNature.expense),
    ("4", "Dívidas e Obrigações", None, AccountNature.liability),
    ("4.1", "Cartão de crédito", "4", AccountNature.liability),
    ("4.2", "Empréstimos", "4", AccountNature.liability),
    ("4.3", "Parcelamentos", "4", AccountNature.liability),
    ("4.4", "Financiamentos", "4", AccountNature.liability),
    ("4.5", "Contas em atraso", "4", AccountNature.liability),
    ("5", "Reservas e Objetivos", None, AccountNature.reserve),
    ("5.1", "Reserva de emergência", "5", AccountNature.reserve),
    ("5.2", "Reserva casa", "5", AccountNature.reserve),
    ("5.3", "Reserva moto", "5", AccountNature.reserve),
    ("5.4", "Reserva roupas", "5", AccountNature.reserve),
    ("5.5", "Reserva estudos", "5", AccountNature.reserve),
    ("5.6", "Reserva viagens", "5", AccountNature.reserve),
    ("5.7", "Reserva presentes", "5", AccountNature.reserve),
    ("6", "Transferências Internas", None, AccountNature.transfer),
    ("6.1", "Nubank para Mercado Pago", "6", AccountNature.transfer),
    ("6.2", "Mercado Pago para Nubank", "6", AccountNature.transfer),
    ("6.3", "Conta para reserva", "6", AccountNature.transfer),
    ("6.4", "Reserva para conta", "6", AccountNature.transfer),
    ("6.5", "Dinheiro físico para banco", "6", AccountNature.transfer),
    ("7", "Ajustes", None, AccountNature.adjustment),
    ("7.1", "Ajuste de saldo", "7", AccountNature.adjustment),
    ("7.2", "Correção manual", "7", AccountNature.adjustment),
    ("7.3", "Estorno", "7", AccountNature.adjustment),
    ("7.4", "Lançamento duplicado corrigido", "7", AccountNature.adjustment),
]


def seed_default_chart_accounts(db: Session) -> list[ChartAccount]:
    cleanup_duplicate_chart_accounts(db)

    repo = ChartAccountRepository(db)
    code_to_item: dict[str, ChartAccount] = {}
    for item in repo.list(include_inactive=True):
        code_to_item.setdefault(item.code, item)
    created: list[ChartAccount] = []

    for code, name, parent_code, nature in DEFAULT_CHART_ACCOUNTS:
        if code in code_to_item:
            continue
        parent_id = code_to_item[parent_code].id if parent_code and parent_code in code_to_item else None
        item = repo.create(
            ChartAccountCreate(
                code=code,
                name=name,
                parent_id=parent_id,
                account_nature=nature,
                is_active=True,
            )
        )
        code_to_item[code] = item
        created.append(item)
    return created


def cleanup_duplicate_chart_accounts(db: Session) -> int:
    duplicate_codes = list(
        db.scalars(
            select(ChartAccount.code)
            .group_by(ChartAccount.code)
            .having(func.count(ChartAccount.id) > 1)
        )
    )
    removed_count = 0

    for code in duplicate_codes:
        items = list(
            db.scalars(
                select(ChartAccount)
                .where(ChartAccount.code == code)
                .order_by(ChartAccount.is_active.desc(), ChartAccount.id.asc())
            )
        )
        if len(items) < 2:
            continue

        keeper = items[0]
        for duplicate in items[1:]:
            db.execute(
                update(Transaction)
                .where(Transaction.chart_account_id == duplicate.id)
                .values(chart_account_id=keeper.id)
            )
            db.execute(
                update(ClassificationRule)
                .where(ClassificationRule.chart_account_id == duplicate.id)
                .values(chart_account_id=keeper.id)
            )
            db.execute(
                update(ChartAccount)
                .where(ChartAccount.parent_id == duplicate.id)
                .values(parent_id=keeper.id)
            )
            db.delete(duplicate)
            removed_count += 1

    if removed_count:
        db.commit()

    return removed_count
