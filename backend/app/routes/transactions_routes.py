from datetime import date
from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.account import Account
from app.models.chart_account import ChartAccount
from app.models.classification_rule import ClassificationRule
from app.models.enums import ClassificationStatus, Direction, MatchType, TransactionSource, TransactionType
from app.models.reserve_box import ReserveBox
from app.models.transaction import Transaction
from app.schemas.classification_rule_schema import ClassificationRuleRead
from app.schemas.transaction_schema import (
    ManualTransactionCreate,
    RuleFromClassificationRequest,
    TransactionClassifyRequest,
    TransactionListItem,
    TransactionRead,
    TransactionSplitItem,
    TransactionSplitRequest,
    TransactionUpdate,
)
from app.services.balance_service import BalanceService
from app.services.classifier_service import ClassifierService
from app.utils.fingerprint import make_fingerprint
from app.utils.text_normalizer import normalize_text

router = APIRouter(prefix="/transactions", tags=["transactions"])
MONEY_QUANTUM = Decimal("0.01")


def _to_list_item(row) -> TransactionListItem:
    tx, account_name, chart_code, chart_name = row
    item = TransactionListItem.model_validate(tx)
    item.account_name = account_name
    item.chart_account_code = chart_code
    item.chart_account_name = chart_name
    return item


@router.post("/manual", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def create_manual_transaction(payload: ManualTransactionCreate, db: Session = Depends(get_db)):
    if not db.get(Account, payload.account_id):
        raise HTTPException(status_code=404, detail="Conta não encontrada")

    _ensure_reserve_box(db, payload.reserve_box_id, payload.account_id)

    description_clean = normalize_text(payload.description_original)
    amount = payload.amount
    direction = payload.direction or (Direction.in_ if amount >= 0 else Direction.out)
    transaction_type = payload.transaction_type or (TransactionType.income if amount >= 0 else TransactionType.expense)
    fingerprint = make_fingerprint(payload.account_id, payload.transaction_date, amount, description_clean)
    if db.scalar(select(Transaction.id).where(Transaction.fingerprint == fingerprint)):
        raise HTTPException(status_code=409, detail="Movimentação duplicada")

    tx_payload = {
        "account_id": payload.account_id,
        "chart_account_id": payload.chart_account_id,
        "transaction_date": payload.transaction_date,
        "description_original": payload.description_original,
        "description_clean": description_clean,
        "amount": amount,
        "direction": direction,
        "transaction_type": transaction_type,
        "source": TransactionSource.manual,
        "fingerprint": fingerprint,
        "classification_status": ClassificationStatus.manual if payload.chart_account_id else ClassificationStatus.pending,
        "is_internal_transfer": payload.is_internal_transfer,
        "reserve_box_id": payload.reserve_box_id,
        "notes": payload.notes,
    }

    if not payload.chart_account_id:
        ClassifierService(db).apply_to_payload(tx_payload)

    tx = Transaction(
        **tx_payload,
    )

    db.add(tx)
    db.commit()
    BalanceService(db).recalculate_balances()
    db.refresh(tx)
    return tx


@router.get("/pending", response_model=list[TransactionListItem])
def pending_transactions(limit: int = Query(500, le=1000), db: Session = Depends(get_db)):
    stmt = _base_query().where(Transaction.classification_status == ClassificationStatus.pending).limit(limit)
    return [_to_list_item(row) for row in db.execute(stmt)]


@router.get("", response_model=list[TransactionListItem])
def list_transactions(
    account_id: int | None = None,
    chart_account_id: int | None = None,
    status_filter: ClassificationStatus | None = Query(default=None, alias="status"),
    source: TransactionSource | None = None,
    transaction_type: TransactionType | None = None,
    uncategorized: bool = False,
    search: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = Query(200, le=1000),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    stmt = _base_query()
    if account_id:
        stmt = stmt.where(Transaction.account_id == account_id)
    if uncategorized:
        stmt = stmt.where(Transaction.chart_account_id.is_(None))
    elif chart_account_id:
        chart_account = db.get(ChartAccount, chart_account_id)
        if not chart_account:
            stmt = stmt.where(Transaction.chart_account_id == chart_account_id)
        else:
            descendant_ids = select(ChartAccount.id).where(
                or_(
                    ChartAccount.id == chart_account.id,
                    ChartAccount.code.like(f"{chart_account.code}.%"),
                )
            )
            stmt = stmt.where(Transaction.chart_account_id.in_(descendant_ids))
    if status_filter:
        stmt = stmt.where(Transaction.classification_status == status_filter)
    if source:
        stmt = stmt.where(Transaction.source == source)
    if transaction_type:
        stmt = stmt.where(Transaction.transaction_type == transaction_type)
    if search:
        query = f"%{normalize_text(search)}%"
        stmt = stmt.where(
            or_(
                Transaction.description_clean.like(query),
                Transaction.notes.ilike(f"%{search.strip()}%"),
            )
        )
    if start_date:
        stmt = stmt.where(Transaction.transaction_date >= start_date)
    if end_date:
        stmt = stmt.where(Transaction.transaction_date <= end_date)
    stmt = stmt.offset(offset).limit(limit)
    return [_to_list_item(row) for row in db.execute(stmt)]


@router.get("/{transaction_id}", response_model=TransactionRead)
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    tx = db.get(Transaction, transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Movimentação não encontrada")
    return tx


@router.put("/{transaction_id}", response_model=TransactionRead)
def update_transaction(transaction_id: int, payload: TransactionUpdate, db: Session = Depends(get_db)):
    tx = db.get(Transaction, transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Movimentação não encontrada")

    data = payload.model_dump(exclude_unset=True)
    target_account_id = data.get("account_id", tx.account_id)
    _ensure_reserve_box(db, data.get("reserve_box_id"), target_account_id)
    for field, value in data.items():
        setattr(tx, field, value)

    if {"account_id", "transaction_date", "description_original", "amount"} & set(data):
        tx.description_clean = normalize_text(tx.description_original)
        tx.direction = payload.direction or (Direction.in_ if tx.amount >= 0 else Direction.out)
        tx.fingerprint = make_fingerprint(tx.account_id, tx.transaction_date, tx.amount, tx.description_clean, tx.external_id)
    if {"chart_account_id", "transaction_type"} & set(data):
        tx.classification_status = ClassificationStatus.manual if tx.chart_account_id else ClassificationStatus.pending
        tx.is_internal_transfer = tx.is_internal_transfer or tx.transaction_type in {
            TransactionType.transfer,
            TransactionType.reserve,
        }

    db.commit()
    BalanceService(db).recalculate_balances()
    db.refresh(tx)
    return tx


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    tx = db.get(Transaction, transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Movimentação não encontrada")
    db.delete(tx)
    db.commit()
    BalanceService(db).recalculate_balances()
    return None


@router.post("/{transaction_id}/split", response_model=list[TransactionRead])
def split_transaction(transaction_id: int, payload: TransactionSplitRequest, db: Session = Depends(get_db)):
    tx = db.get(Transaction, transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Movimentacao nao encontrada")

    original_amount = _money(tx.amount)
    part_amounts = [_money(part.amount) for part in payload.parts]
    if any(amount == 0 for amount in part_amounts):
        raise HTTPException(status_code=400, detail="Partes da divisao nao podem ter valor zero")
    if sum(part_amounts, Decimal("0.00")) != original_amount:
        raise HTTPException(status_code=400, detail="A soma das partes precisa ser igual ao valor original")

    _validate_split_references(db, tx.account_id, payload.parts)
    original = {
        "account_id": tx.account_id,
        "transaction_date": tx.transaction_date,
        "description_original": tx.description_original,
        "amount": original_amount,
        "transaction_type": tx.transaction_type,
        "source": tx.source,
        "external_id": tx.external_id,
        "fingerprint": tx.fingerprint,
        "import_batch_id": tx.import_batch_id,
        "is_internal_transfer": tx.is_internal_transfer,
        "notes": tx.notes,
    }

    first_values = _split_values(payload.parts[0], part_amounts[0], original)
    for field, value in first_values.items():
        setattr(tx, field, value)
    tx.external_id = original["external_id"]
    tx.fingerprint = original["fingerprint"]

    split_transactions = [tx]
    for index, part in enumerate(payload.parts[1:], start=1):
        values = _split_values(part, part_amounts[index], original)
        external_id = f"split:{transaction_id}:{index}:{uuid4().hex[:8]}"
        values["external_id"] = external_id
        values["fingerprint"] = make_fingerprint(
            original["account_id"],
            original["transaction_date"],
            values["amount"],
            values["description_clean"],
            external_id,
        )
        new_tx = Transaction(
            account_id=original["account_id"],
            transaction_date=original["transaction_date"],
            source=original["source"],
            import_batch_id=original["import_batch_id"],
            **values,
        )
        db.add(new_tx)
        split_transactions.append(new_tx)

    db.commit()
    BalanceService(db).recalculate_balances()
    for split_tx in split_transactions:
        db.refresh(split_tx)
    return split_transactions


@router.put("/{transaction_id}/classify", response_model=TransactionRead)
def classify_transaction(transaction_id: int, payload: TransactionClassifyRequest, db: Session = Depends(get_db)):
    tx = db.get(Transaction, transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Movimentação não encontrada")
    if not db.get(ChartAccount, payload.chart_account_id):
        raise HTTPException(status_code=404, detail="Conta do plano não encontrada")

    _ensure_reserve_box(db, payload.reserve_box_id, tx.account_id)

    tx.chart_account_id = payload.chart_account_id
    tx.transaction_type = payload.transaction_type
    tx.is_internal_transfer = payload.is_internal_transfer or payload.transaction_type in {
        TransactionType.transfer,
        TransactionType.reserve,
    }
    tx.reserve_box_id = payload.reserve_box_id
    tx.notes = payload.notes
    tx.classification_status = ClassificationStatus.manual
    if payload.create_rule:
        _ensure_rule_from_transaction(
            db,
            tx,
            keyword=payload.rule_keyword or tx.description_clean,
            match_type=payload.rule_match_type,
            priority=payload.rule_priority,
        )
        _apply_classification_to_equal_pending(db, tx)
    db.commit()
    db.refresh(tx)
    return tx


@router.post("/{transaction_id}/create-rule-from-classification", response_model=ClassificationRuleRead)
def create_rule_from_transaction(
    transaction_id: int,
    payload: RuleFromClassificationRequest,
    db: Session = Depends(get_db),
):
    tx = db.get(Transaction, transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Movimentação não encontrada")
    if not tx.chart_account_id:
        raise HTTPException(status_code=400, detail="Classifique a movimentação antes de criar uma regra")

    rule = _ensure_rule_from_transaction(
        db,
        tx,
        keyword=payload.keyword,
        match_type=payload.match_type,
        priority=payload.priority,
    )
    db.commit()
    db.refresh(rule)
    return rule


def _ensure_rule_from_transaction(
    db: Session,
    tx: Transaction,
    *,
    keyword: str,
    match_type: MatchType,
    priority: int,
) -> ClassificationRule:
    normalized_keyword = normalize_text(keyword) if match_type != MatchType.regex else keyword.strip()
    rule = db.scalar(
        select(ClassificationRule).where(
            ClassificationRule.keyword == normalized_keyword,
            ClassificationRule.match_type == match_type,
            ClassificationRule.chart_account_id == tx.chart_account_id,
            ClassificationRule.transaction_type == tx.transaction_type,
            ClassificationRule.active.is_(True),
        )
    )
    if rule:
        return rule
    rule = ClassificationRule(
        keyword=normalized_keyword,
        match_type=match_type,
        chart_account_id=tx.chart_account_id,
        transaction_type=tx.transaction_type,
        priority=priority,
        active=True,
    )
    db.add(rule)
    db.flush()
    return rule


def _apply_classification_to_equal_pending(db: Session, tx: Transaction) -> int:
    matches = db.scalars(
        select(Transaction).where(
            Transaction.id != tx.id,
            Transaction.description_clean == tx.description_clean,
            Transaction.classification_status == ClassificationStatus.pending,
        )
    ).all()
    for match in matches:
        match.chart_account_id = tx.chart_account_id
        match.transaction_type = tx.transaction_type
        match.is_internal_transfer = tx.is_internal_transfer
        match.reserve_box_id = tx.reserve_box_id
        match.classification_status = ClassificationStatus.automatic
    return len(matches)


def _base_query():
    return (
        select(Transaction, Account.name, ChartAccount.code, ChartAccount.name)
        .join(Account, Account.id == Transaction.account_id)
        .join(ChartAccount, ChartAccount.id == Transaction.chart_account_id, isouter=True)
        .order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
    )


def _ensure_reserve_box(db: Session, reserve_box_id: int | None, account_id: int) -> None:
    if reserve_box_id is None:
        return
    reserve_box = db.get(ReserveBox, reserve_box_id)
    if not reserve_box or reserve_box.account_id != account_id:
        raise HTTPException(status_code=404, detail="Reserva nao encontrada para esta conta")


def _validate_split_references(db: Session, account_id: int, parts: list[TransactionSplitItem]) -> None:
    for part in parts:
        if part.chart_account_id is not None and not db.get(ChartAccount, part.chart_account_id):
            raise HTTPException(status_code=404, detail="Conta do plano nao encontrada")
        _ensure_reserve_box(db, part.reserve_box_id, account_id)


def _money(value: Decimal) -> Decimal:
    return Decimal(value).quantize(MONEY_QUANTUM)


def _split_values(part: TransactionSplitItem, amount: Decimal, original: dict) -> dict:
    description = part.description_original or original["description_original"]
    description_clean = normalize_text(description)
    transaction_type = part.transaction_type or _default_transaction_type(
        original["transaction_type"],
        original["amount"],
        amount,
    )
    is_internal_transfer = (
        bool(part.is_internal_transfer)
        if part.is_internal_transfer is not None
        else bool(original["is_internal_transfer"])
    )
    is_internal_transfer = is_internal_transfer or transaction_type in {TransactionType.transfer, TransactionType.reserve}
    chart_account_id = part.chart_account_id
    return {
        "chart_account_id": chart_account_id,
        "reserve_box_id": part.reserve_box_id,
        "description_original": description,
        "description_clean": description_clean,
        "amount": amount,
        "transaction_type": transaction_type,
        "direction": part.direction or (Direction.in_ if amount >= 0 else Direction.out),
        "classification_status": ClassificationStatus.manual if chart_account_id else ClassificationStatus.pending,
        "is_internal_transfer": is_internal_transfer,
        "notes": part.notes if part.notes is not None else original["notes"],
    }


def _default_transaction_type(original_type: TransactionType, original_amount: Decimal, amount: Decimal) -> TransactionType:
    if (original_amount >= 0) == (amount >= 0):
        return original_type
    return TransactionType.income if amount >= 0 else TransactionType.expense
