from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
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
    return repo.deactivate(account)
