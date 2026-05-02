from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.account import Account
from app.models.reserve_box import ReserveBox
from app.schemas.reserve_box_schema import ReserveBoxCreate, ReserveBoxRead, ReserveBoxUpdate

router = APIRouter(prefix="/reserve-boxes", tags=["reserve boxes"])


@router.post("", response_model=ReserveBoxRead, status_code=status.HTTP_201_CREATED)
def create_reserve_box(payload: ReserveBoxCreate, db: Session = Depends(get_db)):
    if not db.get(Account, payload.account_id):
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    item = ReserveBox(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("", response_model=list[ReserveBoxRead])
def list_reserve_boxes(account_id: int | None = None, include_inactive: bool = False, db: Session = Depends(get_db)):
    stmt = select(ReserveBox).order_by(ReserveBox.name)
    if account_id:
        stmt = stmt.where(ReserveBox.account_id == account_id)
    if not include_inactive:
        stmt = stmt.where(ReserveBox.is_active.is_(True))
    return list(db.scalars(stmt))


@router.put("/{reserve_box_id}", response_model=ReserveBoxRead)
def update_reserve_box(reserve_box_id: int, payload: ReserveBoxUpdate, db: Session = Depends(get_db)):
    item = db.get(ReserveBox, reserve_box_id)
    if not item:
        raise HTTPException(status_code=404, detail="Caixinha não encontrada")
    data = payload.model_dump(exclude_unset=True)
    if "account_id" in data and not db.get(Account, data["account_id"]):
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    for field, value in data.items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{reserve_box_id}", response_model=ReserveBoxRead)
def delete_reserve_box(reserve_box_id: int, db: Session = Depends(get_db)):
    item = db.get(ReserveBox, reserve_box_id)
    if not item:
        raise HTTPException(status_code=404, detail="Caixinha não encontrada")
    item.is_active = False
    db.commit()
    db.refresh(item)
    return item
