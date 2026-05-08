from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.balance_snapshot import BalanceSnapshot
from app.schemas.balance_schema import BalanceSnapshotRead, ReconcileRequest
from app.services.reconciliation_service import ReconciliationService

router = APIRouter(prefix="/balances", tags=["balances"])


@router.post("/reconcile", response_model=BalanceSnapshotRead)
def reconcile(payload: ReconcileRequest, db: Session = Depends(get_db)):
    try:
        return ReconciliationService(db).reconcile(payload.account_id, payload.period_month, payload.real_balance)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/snapshots", response_model=list[BalanceSnapshotRead])
def list_snapshots(db: Session = Depends(get_db)):
    return list(db.scalars(select(BalanceSnapshot).order_by(BalanceSnapshot.period_month.desc(), BalanceSnapshot.account_id)))


@router.get("/snapshots/{account_id}", response_model=list[BalanceSnapshotRead])
def list_account_snapshots(account_id: int, db: Session = Depends(get_db)):
    return list(
        db.scalars(
            select(BalanceSnapshot)
            .where(BalanceSnapshot.account_id == account_id)
            .order_by(BalanceSnapshot.period_month.desc())
        )
    )
