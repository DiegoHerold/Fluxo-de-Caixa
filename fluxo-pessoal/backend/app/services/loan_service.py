from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.chart_account import ChartAccount
from app.models.enums import AccountNature, LoanMovementEffect
from app.models.loan import LoanAccountLink, LoanLossWriteoff, LoanPerson, LoanSettings
from app.models.transaction import Transaction
from app.schemas.loan_schema import (
    LoanAccountLinkRead,
    LoanLossWriteoffCreate,
    LoanLossWriteoffRead,
    LoanMovementRead,
    LoanPersonRead,
    LoanPersonSummary,
    LoanSettingsRead,
)


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
        loss_total = self.loss_total_for_person(person_id)
        if not links:
            return Decimal("0.00"), loss_total, linked_count

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
        return increase_total, decrease_total + loss_total, linked_count

    def loss_total_for_person(self, person_id: int) -> Decimal:
        return self.db.scalar(
            select(func.coalesce(func.sum(LoanLossWriteoff.amount), 0)).where(LoanLossWriteoff.person_id == person_id)
        ) or Decimal("0.00")

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

        effects_by_chart_account = {link.chart_account_id: link.effect for link in links}
        running_balance = Decimal(person.opening_balance)
        movement_rows: list[tuple[object, LoanMovementRead]] = []
        if effects_by_chart_account:
            stmt = (
                select(Transaction, Account.name, ChartAccount.code, ChartAccount.name)
                .join(Account, Account.id == Transaction.account_id)
                .join(ChartAccount, ChartAccount.id == Transaction.chart_account_id)
                .where(Transaction.chart_account_id.in_(list(effects_by_chart_account)))
                .order_by(Transaction.transaction_date.asc(), Transaction.id.asc())
            )
            for tx, account_name, chart_code, chart_name in self.db.execute(stmt):
                effect = effects_by_chart_account[tx.chart_account_id]
                value = abs(Decimal(tx.amount))
                delta = value if effect == LoanMovementEffect.increase else -value
                movement_rows.append(
                    (
                        tx.transaction_date,
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
                            movement_kind="transaction",
                        ),
                    ),
                )
        for writeoff in self.db.scalars(
            select(LoanLossWriteoff)
            .where(LoanLossWriteoff.person_id == person.id)
            .order_by(LoanLossWriteoff.writeoff_date.asc(), LoanLossWriteoff.id.asc())
        ):
            delta = -abs(Decimal(writeoff.amount))
            running_balance += delta
            movement_rows.append(
                (
                    writeoff.writeoff_date,
                    LoanMovementRead(
                        transaction_id=None,
                        writeoff_id=writeoff.id,
                        transaction_date=writeoff.writeoff_date,
                        description=writeoff.notes or "Baixa por perda de emprestimo",
                        account_name=None,
                        chart_account_id=writeoff.chart_account_id,
                        chart_account_code=writeoff.chart_account.code if writeoff.chart_account else None,
                        chart_account_name=writeoff.chart_account.name if writeoff.chart_account else None,
                        transaction_amount=-abs(Decimal(writeoff.amount)),
                        effect=LoanMovementEffect.decrease,
                        debt_delta=delta,
                        balance_after=running_balance,
                        movement_kind="loss",
                    ),
                )
            )
        ordered_movements = [item for _, item in sorted(movement_rows, key=lambda row: (row[0], getattr(row[1], "transaction_id") or 0))]
        balance = Decimal(person.opening_balance)
        for movement in ordered_movements:
            balance += Decimal(movement.debt_delta)
            movement.balance_after = balance
        return list(reversed(ordered_movements))

    def settings(self) -> LoanSettingsRead:
        settings = self._settings()
        account = settings.loss_chart_account
        return LoanSettingsRead(
            loss_chart_account_id=settings.loss_chart_account_id,
            loss_chart_account_code=account.code if account else None,
            loss_chart_account_name=account.name if account else None,
        )

    def update_settings(self, loss_chart_account_id: int | None) -> LoanSettingsRead:
        settings = self._settings()
        if loss_chart_account_id is not None:
            account = self.db.get(ChartAccount, loss_chart_account_id)
            if not account:
                raise HTTPException(status_code=404, detail="Classificacao de perda nao encontrada")
            if account.account_nature != AccountNature.expense:
                raise HTTPException(status_code=400, detail="A perda precisa usar uma classificacao com natureza de despesa")
        settings.loss_chart_account_id = loss_chart_account_id
        self.db.commit()
        self.db.refresh(settings)
        return self.settings()

    def create_loss_writeoff(self, person: LoanPerson, payload: LoanLossWriteoffCreate) -> LoanLossWriteoffRead:
        settings = self._settings()
        if not settings.loss_chart_account_id:
            raise HTTPException(status_code=400, detail="Configure a classificacao de perda antes de baixar valores")
        current_balance = self.build_person_summary(person).current_balance
        amount = abs(Decimal(payload.amount))
        if amount > current_balance:
            raise HTTPException(status_code=400, detail="A perda nao pode ser maior que o saldo em aberto")
        writeoff = LoanLossWriteoff(
            person_id=person.id,
            chart_account_id=settings.loss_chart_account_id,
            writeoff_date=payload.writeoff_date,
            amount=amount,
            notes=payload.notes,
        )
        self.db.add(writeoff)
        self.db.commit()
        self.db.refresh(writeoff)
        return self._loss_to_read(writeoff)

    def list_losses(self, person_id: int | None = None) -> list[LoanLossWriteoffRead]:
        stmt = select(LoanLossWriteoff).order_by(LoanLossWriteoff.writeoff_date.desc(), LoanLossWriteoff.id.desc())
        if person_id:
            stmt = stmt.where(LoanLossWriteoff.person_id == person_id)
        return [self._loss_to_read(item) for item in self.db.scalars(stmt)]

    def _settings(self) -> LoanSettings:
        settings = self.db.get(LoanSettings, 1)
        if settings:
            return settings
        default_loss_account_id = self.db.scalar(
            select(ChartAccount.id).where(or_(ChartAccount.code == "3.10", ChartAccount.name.ilike("%perdas%emprest%")))
        )
        settings = LoanSettings(id=1, loss_chart_account_id=default_loss_account_id)
        self.db.add(settings)
        self.db.commit()
        self.db.refresh(settings)
        return settings

    def _loss_to_read(self, writeoff: LoanLossWriteoff) -> LoanLossWriteoffRead:
        item = LoanLossWriteoffRead.model_validate(writeoff)
        item.chart_account_code = writeoff.chart_account.code if writeoff.chart_account else None
        item.chart_account_name = writeoff.chart_account.name if writeoff.chart_account else None
        return item
