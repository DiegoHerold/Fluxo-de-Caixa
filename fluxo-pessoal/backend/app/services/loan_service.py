from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.chart_account import ChartAccount
from app.models.enums import LoanMovementEffect
from app.models.loan import LoanAccountLink, LoanPerson
from app.models.transaction import Transaction
from app.schemas.loan_schema import LoanAccountLinkRead, LoanMovementRead, LoanPersonRead, LoanPersonSummary


class LoanService:
    def __init__(self, db: Session):
        self.db = db

    def list_people(self, include_inactive: bool = False) -> list[LoanPersonSummary]:
        stmt = select(LoanPerson).order_by(LoanPerson.name)
        if not include_inactive:
            stmt = stmt.where(LoanPerson.is_active.is_(True))
        return [self.build_person_summary(person) for person in self.db.scalars(stmt)]

    def build_person_summary(self, person: LoanPerson) -> LoanPersonSummary:
        increase_total, decrease_total, linked_count = self.calculate_totals(person.id)
        return LoanPersonSummary(
            **LoanPersonRead.model_validate(person).model_dump(),
            current_balance=Decimal(person.opening_balance) + increase_total - decrease_total,
            movement_increase_total=increase_total,
            movement_decrease_total=decrease_total,
            linked_accounts_count=linked_count,
        )

    def calculate_totals(self, person_id: int) -> tuple[Decimal, Decimal, int]:
        links = self.active_links_for_person(person_id)
        linked_count = len(links)
        if not links:
            return Decimal("0.00"), Decimal("0.00"), linked_count

        effects_by_chart_account = {link.chart_account_id: link.effect for link in links}
        stmt = select(Transaction.amount, Transaction.chart_account_id).where(
            Transaction.chart_account_id.in_(list(effects_by_chart_account))
        )
        increase_total = Decimal("0.00")
        decrease_total = Decimal("0.00")
        for amount, chart_account_id in self.db.execute(stmt):
            value = abs(Decimal(amount))
            if effects_by_chart_account[chart_account_id] == LoanMovementEffect.increase:
                increase_total += value
            else:
                decrease_total += value
        return increase_total, decrease_total, linked_count

    def active_links_for_person(self, person_id: int) -> list[LoanAccountLink]:
        stmt = select(LoanAccountLink).where(
            LoanAccountLink.person_id == person_id,
            LoanAccountLink.is_active.is_(True),
        )
        return list(self.db.scalars(stmt))

    def list_links(self, person_id: int | None = None, include_inactive: bool = False) -> list[LoanAccountLinkRead]:
        stmt = (
            select(LoanAccountLink, ChartAccount.code, ChartAccount.name)
            .join(ChartAccount, ChartAccount.id == LoanAccountLink.chart_account_id)
            .order_by(LoanAccountLink.created_at.desc(), LoanAccountLink.id.desc())
        )
        if person_id:
            stmt = stmt.where(LoanAccountLink.person_id == person_id)
        if not include_inactive:
            stmt = stmt.where(LoanAccountLink.is_active.is_(True))

        items: list[LoanAccountLinkRead] = []
        for link, chart_code, chart_name in self.db.execute(stmt):
            item = LoanAccountLinkRead.model_validate(link)
            item.chart_account_code = chart_code
            item.chart_account_name = chart_name
            items.append(item)
        return items

    def list_movements(self, person: LoanPerson) -> list[LoanMovementRead]:
        links = self.active_links_for_person(person.id)
        if not links:
            return []

        effects_by_chart_account = {link.chart_account_id: link.effect for link in links}
        stmt = (
            select(Transaction, Account.name, ChartAccount.code, ChartAccount.name)
            .join(Account, Account.id == Transaction.account_id)
            .join(ChartAccount, ChartAccount.id == Transaction.chart_account_id)
            .where(Transaction.chart_account_id.in_(list(effects_by_chart_account)))
            .order_by(Transaction.transaction_date.asc(), Transaction.id.asc())
        )

        running_balance = Decimal(person.opening_balance)
        movements: list[LoanMovementRead] = []
        for tx, account_name, chart_code, chart_name in self.db.execute(stmt):
            effect = effects_by_chart_account[tx.chart_account_id]
            value = abs(Decimal(tx.amount))
            delta = value if effect == LoanMovementEffect.increase else -value
            running_balance += delta
            movements.append(
                LoanMovementRead(
                    transaction_id=tx.id,
                    transaction_date=tx.transaction_date,
                    description=tx.description_original,
                    account_name=account_name,
                    chart_account_id=tx.chart_account_id,
                    chart_account_code=chart_code,
                    chart_account_name=chart_name,
                    transaction_amount=tx.amount,
                    effect=effect,
                    debt_delta=delta,
                    balance_after=running_balance,
                )
            )
        return list(reversed(movements))
