from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.account import Account
from app.models.balance_snapshot import BalanceSnapshot
from app.models.reserve_box import ReserveBox
from app.models.transaction import Transaction
from app.repositories.account_repository import AccountRepository
from app.schemas.account_schema import AccountBalance, AccountCreate, AccountRead, AccountUpdate, ConsolidatedBalance, ReserveBalance
from app.services.balance_service import BalanceService
from app.services.reserve_service import ReserveService

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("/balances", response_model=list[AccountBalance])
def list_balances(db: Session = Depends(get_db)):
    return BalanceService(db).calculate_all_balances()


@router.get("/consolidated-balance", response_model=ConsolidatedBalance)
def consolidated_balance(db: Session = Depends(get_db)):
    return BalanceService(db).calculate_consolidated_balance()


@router.get("/reserves", response_model=list[ReserveBalance])
def reserve_balances(account_id: int | None = None, db: Session = Depends(get_db)):
    return ReserveService(db).calculate_reserves(account_id)


@router.post("", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(payload: AccountCreate, db: Session = Depends(get_db)):
    return AccountRepository(db).create(payload)


@router.get("", response_model=list[AccountRead])
def list_accounts(include_inactive: bool = False, db: Session = Depends(get_db)):
    return AccountRepository(db).list(include_inactive=include_inactive)


@router.get("/{account_id}", response_model=AccountRead)
def get_account(account_id: int, db: Session = Depends(get_db)):
    account = AccountRepository(db).get(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    return account


@router.put("/{account_id}", response_model=AccountRead)
def update_account(account_id: int, payload: AccountUpdate, db: Session = Depends(get_db)):
    repo = AccountRepository(db)
    account = repo.get(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    updated = repo.update(account, payload)
    BalanceService(db).recalculate_balances()
    db.refresh(updated)
    return updated


@router.delete("/{account_id}", response_model=AccountRead)
def delete_account(account_id: int, db: Session = Depends(get_db)):
    repo = AccountRepository(db)
    account = repo.get(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    blockers = _account_delete_blockers(db, account)
    if blockers:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Nao foi possivel apagar a conta porque existem vinculos.",
                "blockers": blockers,
            },
        )
    deleted = AccountRead.model_validate(account)
    for snapshot in db.scalars(select(BalanceSnapshot).where(BalanceSnapshot.account_id == account.id)):
        db.delete(snapshot)
    db.delete(account)
    db.commit()
    return deleted


def _account_delete_blockers(db: Session, account: Account) -> list[dict]:
    blockers: list[dict] = []
    transaction_count = db.scalar(select(func.count()).select_from(Transaction).where(Transaction.account_id == account.id)) or 0
    if transaction_count:
        sample = list(
            db.execute(
                select(Transaction.id, Transaction.transaction_date, Transaction.description_original, Transaction.amount)
                .where(Transaction.account_id == account.id)
                .order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
                .limit(8)
            )
        )
        blockers.append(
            {
                "type": "movimentacoes",
                "count": transaction_count,
                "items": [
                    {
                        "id": tx_id,
                        "date": tx_date.isoformat(),
                        "description": description,
                        "amount": str(amount),
                    }
                    for tx_id, tx_date, description, amount in sample
                ],
            }
        )

    reserve_count = db.scalar(select(func.count()).select_from(ReserveBox).where(ReserveBox.account_id == account.id)) or 0
    if reserve_count:
        sample_boxes = list(db.scalars(select(ReserveBox).where(ReserveBox.account_id == account.id).order_by(ReserveBox.name).limit(8)))
        blockers.append(
            {
                "type": "caixinhas",
                "count": reserve_count,
                "items": [{"id": box.id, "name": box.name, "balance": str(box.current_balance)} for box in sample_boxes],
            }
        )
    return blockers
