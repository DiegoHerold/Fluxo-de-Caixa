from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.chart_account import ChartAccount
from app.models.classification_rule import ClassificationRule
from app.models.enums import AccountNature
from app.models.transaction import Transaction
from app.repositories.chart_account_repository import ChartAccountRepository
from app.schemas.chart_account_schema import ChartAccountCreate


DEFAULT_CHART_ACCOUNTS: list[tuple[str, str, str | None, AccountNature]] = [
    # 1 - Receitas
    ("1", "Receitas", None, AccountNature.income),
    ("1.1", "Salário", "1", AccountNature.income),
    ("1.2", "Extra / Bicos", "1", AccountNature.income),
    ("1.3", "Vendas", "1", AccountNature.income),
    ("1.4", "Outros recebimentos reais", "1", AccountNature.income),
    # 2 - Despesas Fixas
    ("2", "Despesas Fixas", None, AccountNature.expense),
    ("2.1", "Moradia", "2", AccountNature.expense),
    ("2.1.1", "Aluguel", "2.1", AccountNature.expense),
    ("2.1.2", "Água", "2.1", AccountNature.expense),
    ("2.1.3", "Luz", "2.1", AccountNature.expense),
    ("2.1.4", "Internet", "2.1", AccountNature.expense),
    ("2.2", "Recorrentes", "2", AccountNature.expense),
    ("2.2.1", "Telefone", "2.2", AccountNature.expense),
    ("2.2.2", "Academia", "2.2", AccountNature.expense),
    ("2.2.3", "Assinaturas", "2.2", AccountNature.expense),
    # 3 - Despesas Variáveis
    ("3", "Despesas Variáveis", None, AccountNature.expense),
    ("3.1", "Alimentação", "3", AccountNature.expense),
    ("3.1.1", "Mercado", "3.1", AccountNature.expense),
    ("3.1.2", "Restaurante / Lanche", "3.1", AccountNature.expense),
    ("3.2", "Transporte", "3", AccountNature.expense),
    ("3.2.1", "Combustível", "3.2", AccountNature.expense),
    ("3.2.2", "Aplicativo / Uber", "3.2", AccountNature.expense),
    ("3.2.3", "Manutenção", "3.2", AccountNature.expense),
    ("3.3", "Saúde", "3", AccountNature.expense),
    ("3.3.1", "Farmácia", "3.3", AccountNature.expense),
    ("3.3.2", "Consulta / Exames", "3.3", AccountNature.expense),
    ("3.4", "Pessoal", "3", AccountNature.expense),
    ("3.4.1", "Roupas", "3.4", AccountNature.expense),
    ("3.4.2", "Cabelo / Beleza", "3.4", AccountNature.expense),
    ("3.4.3", "Compras pessoais", "3.4", AccountNature.expense),
    ("3.5", "Lazer", "3", AccountNature.expense),
    ("3.6", "Casa", "3", AccountNature.expense),
    ("3.7", "Estudos / Cursos", "3", AccountNature.expense),
    ("3.8", "Tecnologia / Setup", "3", AccountNature.expense),
    ("3.9", "Outros variáveis", "3", AccountNature.expense),
    # 4 - Dívidas e Obrigações
    ("4", "Dívidas e Obrigações", None, AccountNature.liability),
    ("4.1", "Cartão de crédito", "4", AccountNature.liability),
    ("4.2", "Empréstimos", "4", AccountNature.liability),
    ("4.3", "Parcelamentos", "4", AccountNature.liability),
    ("4.4", "Juros / Multas", "4", AccountNature.liability),
    ("4.5", "Contas em atraso", "4", AccountNature.liability),
    # 5 - Transferências Internas
    ("5", "Transferências Internas", None, AccountNature.transfer),
    ("5.1", "Entre contas próprias", "5", AccountNature.transfer),
    ("5.2", "Conta para caixinha", "5", AccountNature.transfer),
    ("5.3", "Caixinha para conta", "5", AccountNature.transfer),
    ("5.4", "Entre caixinhas", "5", AccountNature.transfer),
    ("5.5", "Dinheiro físico", "5", AccountNature.transfer),
    # 6 - Ajustes, Estornos e Reembolsos
    ("6", "Ajustes, Estornos e Reembolsos", None, AccountNature.adjustment),
    ("6.1", "Ajuste de saldo", "6", AccountNature.adjustment),
    ("6.2", "Correção manual", "6", AccountNature.adjustment),
    ("6.3", "Estorno", "6", AccountNature.adjustment),
    ("6.4", "Reembolso recebido", "6", AccountNature.adjustment),
    ("6.5", "Cashback", "6", AccountNature.adjustment),
    # 7 - Valores a Receber
    ("7", "Valores a Receber", None, AccountNature.loan),
    ("7.1", "Dinheiro emprestado", "7", AccountNature.loan),
    ("7.2", "Recebimento de dinheiro emprestado", "7", AccountNature.loan),
    ("7.3", "Conta dividida a receber", "7", AccountNature.loan),
    ("7.4", "Conta dividida recebida", "7", AccountNature.loan),
    ("7.5", "Valor perdido / não recebido", "7", AccountNature.loan),
    # 8 - Gastos Planejados com Reservas
    ("8", "Gastos Planejados com Reservas", None, AccountNature.reserve),
    ("8.1", "Uso reserva emergência", "8", AccountNature.reserve),
    ("8.2", "Uso reserva casa", "8", AccountNature.reserve),
    ("8.3", "Uso reserva moto", "8", AccountNature.reserve),
    ("8.4", "Uso reserva roupas", "8", AccountNature.reserve),
    ("8.5", "Uso reserva setup", "8", AccountNature.reserve),
    ("8.6", "Uso reserva cabelo", "8", AccountNature.reserve),
    ("8.7", "Uso reserva presentes", "8", AccountNature.reserve),
    ("8.8", "Outros usos de reserva", "8", AccountNature.reserve),
]


def seed_default_chart_accounts(db: Session) -> list[ChartAccount]:
    cleanup_duplicate_chart_accounts(db)

    repo = ChartAccountRepository(db)
    code_to_item: dict[str, ChartAccount] = {}
    for item in repo.list(include_inactive=True):
        code_to_item.setdefault(item.code, item)
    created: list[ChartAccount] = []
    updated_existing = False

    for code, name, parent_code, nature in DEFAULT_CHART_ACCOUNTS:
        if code in code_to_item:
            if code.startswith("7") and code_to_item[code].account_nature != nature:
                code_to_item[code].account_nature = nature
                updated_existing = True
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
    if updated_existing:
        db.commit()
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
