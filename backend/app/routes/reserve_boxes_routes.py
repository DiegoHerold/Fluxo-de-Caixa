from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.account import Account
from app.models.chart_account import ChartAccount
from app.models.enums import AccountNature
from app.models.reserve_box import ReserveBox
from app.schemas.reserve_box_schema import ReserveBoxCreate, ReserveBoxRead, ReserveBoxUpdate

router = APIRouter(prefix="/reserve-boxes", tags=["reserve boxes"])


@router.post("", response_model=ReserveBoxRead, status_code=status.HTTP_201_CREATED)
def create_reserve_box(payload: ReserveBoxCreate, db: Session = Depends(get_db)):
    if not db.get(Account, payload.account_id):
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    data = payload.model_dump(exclude={"auto_create_chart_accounts"})
    if payload.auto_create_chart_accounts:
        data["chart_account_id"] = _find_or_create_child_chart_account(db, "5.2", f"Para {payload.name}").id
        data["withdrawal_chart_account_id"] = _find_or_create_child_chart_account(db, "5.3", f"Uso da Reserva {payload.name}").id
    _ensure_reserve_chart_account(db, data.get("chart_account_id"))
    _ensure_reserve_chart_account(db, data.get("withdrawal_chart_account_id"))
    item = ReserveBox(**data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return _to_read(item)


@router.get("", response_model=list[ReserveBoxRead])
def list_reserve_boxes(account_id: int | None = None, include_inactive: bool = False, db: Session = Depends(get_db)):
    stmt = select(ReserveBox).order_by(ReserveBox.name)
    if account_id:
        stmt = stmt.where(ReserveBox.account_id == account_id)
    if not include_inactive:
        stmt = stmt.where(ReserveBox.is_active.is_(True))
    return [_to_read(item) for item in db.scalars(stmt)]


@router.put("/{reserve_box_id}", response_model=ReserveBoxRead)
def update_reserve_box(reserve_box_id: int, payload: ReserveBoxUpdate, db: Session = Depends(get_db)):
    item = db.get(ReserveBox, reserve_box_id)
    if not item:
        raise HTTPException(status_code=404, detail="Caixinha não encontrada")
    data = payload.model_dump(exclude_unset=True)
    if "account_id" in data and not db.get(Account, data["account_id"]):
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    if "chart_account_id" in data:
        _ensure_reserve_chart_account(db, data["chart_account_id"])
    if "withdrawal_chart_account_id" in data:
        _ensure_reserve_chart_account(db, data["withdrawal_chart_account_id"])
    for field, value in data.items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return _to_read(item)


@router.delete("/{reserve_box_id}", response_model=ReserveBoxRead)
def delete_reserve_box(reserve_box_id: int, db: Session = Depends(get_db)):
    item = db.get(ReserveBox, reserve_box_id)
    if not item:
        raise HTTPException(status_code=404, detail="Caixinha não encontrada")
    item.is_active = False
    db.commit()
    db.refresh(item)
    return _to_read(item)


def _ensure_reserve_chart_account(db: Session, chart_account_id: int | None) -> None:
    if chart_account_id is None:
        return
    account = db.get(ChartAccount, chart_account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Classificacao da caixinha nao encontrada")
    if account.account_nature != AccountNature.transfer:
        raise HTTPException(status_code=400, detail="A caixinha precisa usar uma classificacao com natureza transferencia interna")


def _find_or_create_child_chart_account(db: Session, parent_code: str, name: str) -> ChartAccount:
    parent = db.scalar(select(ChartAccount).where(ChartAccount.code == parent_code))
    if not parent:
        raise HTTPException(status_code=400, detail=f"Classificacao base {parent_code} nao encontrada")
    existing = db.scalar(select(ChartAccount).where(ChartAccount.parent_id == parent.id, ChartAccount.name == name))
    if existing:
        if not existing.is_active:
            existing.is_active = True
        existing.account_nature = AccountNature.transfer
        db.flush()
        return existing

    item = ChartAccount(
        code=_next_child_code(db, parent_code),
        name=name,
        parent_id=parent.id,
        account_nature=AccountNature.transfer,
        is_active=True,
    )
    db.add(item)
    db.flush()
    return item


def _next_child_code(db: Session, parent_code: str) -> str:
    prefix = f"{parent_code}."
    codes = list(db.scalars(select(ChartAccount.code).where(ChartAccount.code.like(f"{prefix}%"))))
    numbers: list[int] = []
    for code in codes:
        suffix = code.removeprefix(prefix)
        if suffix.isdigit():
            numbers.append(int(suffix))
    return f"{parent_code}.{(max(numbers) if numbers else 0) + 1}"


def _to_read(item: ReserveBox) -> ReserveBoxRead:
    data = ReserveBoxRead.model_validate(item)
    data.chart_account_code = item.chart_account.code if item.chart_account else None
    data.chart_account_name = item.chart_account.name if item.chart_account else None
    data.withdrawal_chart_account_code = item.withdrawal_chart_account.code if item.withdrawal_chart_account else None
    data.withdrawal_chart_account_name = item.withdrawal_chart_account.name if item.withdrawal_chart_account else None
    return data
