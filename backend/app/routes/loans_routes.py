from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.chart_account import ChartAccount
from app.models.loan import LoanAccountLink, LoanPerson
from app.schemas.loan_schema import (
    LoanAccountLinkCreate,
    LoanAccountLinkRead,
    LoanAccountLinkUpdate,
    LoanLossWriteoffCreate,
    LoanLossWriteoffRead,
    LoanMovementRead,
    LoanPersonCreate,
    LoanPersonRead,
    LoanPersonSummary,
    LoanPersonUpdate,
    LoanSettingsRead,
    LoanSettingsUpdate,
)
from app.services.loan_service import LoanService

router = APIRouter(prefix="/loans", tags=["loans"])


@router.post("/people", response_model=LoanPersonRead, status_code=status.HTTP_201_CREATED)
def create_person(payload: LoanPersonCreate, db: Session = Depends(get_db)):
    return LoanService(db).create_person_with_default_accounts(payload)


@router.get("/people", response_model=list[LoanPersonSummary])
def list_people(include_inactive: bool = False, db: Session = Depends(get_db)):
    return LoanService(db).list_people(include_inactive)


@router.get("/settings", response_model=LoanSettingsRead)
def get_settings(db: Session = Depends(get_db)):
    return LoanService(db).settings()


@router.put("/settings", response_model=LoanSettingsRead)
def update_settings(payload: LoanSettingsUpdate, db: Session = Depends(get_db)):
    return LoanService(db).update_settings(payload.loss_chart_account_id)


@router.get("/people/{person_id}", response_model=LoanPersonSummary)
def get_person(person_id: int, db: Session = Depends(get_db)):
    person = _get_person(db, person_id)
    return LoanService(db).build_person_summary(person)


@router.put("/people/{person_id}", response_model=LoanPersonRead)
def update_person(person_id: int, payload: LoanPersonUpdate, db: Session = Depends(get_db)):
    person = _get_person(db, person_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(person, field, value)
    db.commit()
    db.refresh(person)
    return person


@router.delete("/people/{person_id}", response_model=LoanPersonRead)
def deactivate_person(person_id: int, db: Session = Depends(get_db)):
    person = _get_person(db, person_id)
    person.is_active = False
    links = db.scalars(select(LoanAccountLink).where(LoanAccountLink.person_id == person_id)).all()
    for link in links:
        link.is_active = False
    db.commit()
    db.refresh(person)
    return person


@router.get("/people/{person_id}/movements", response_model=list[LoanMovementRead])
def list_person_movements(person_id: int, db: Session = Depends(get_db)):
    person = _get_person(db, person_id)
    return LoanService(db).list_movements(person)


@router.post("/people/{person_id}/losses", response_model=LoanLossWriteoffRead, status_code=status.HTTP_201_CREATED)
def create_loss_writeoff(person_id: int, payload: LoanLossWriteoffCreate, db: Session = Depends(get_db)):
    person = _get_person(db, person_id)
    return LoanService(db).create_loss_writeoff(person, payload)


@router.get("/losses", response_model=list[LoanLossWriteoffRead])
def list_losses(person_id: int | None = None, db: Session = Depends(get_db)):
    if person_id:
        _get_person(db, person_id)
    return LoanService(db).list_losses(person_id)


@router.post("/links", response_model=LoanAccountLinkRead, status_code=status.HTTP_201_CREATED)
def create_link(payload: LoanAccountLinkCreate, db: Session = Depends(get_db)):
    _get_person(db, payload.person_id)
    _ensure_chart_account(db, payload.chart_account_id)
    _ensure_chart_account_available(db, payload.chart_account_id)

    link = LoanAccountLink(**payload.model_dump())
    db.add(link)
    db.commit()
    db.refresh(link)
    return next(item for item in LoanService(db).list_links(person_id=link.person_id, include_inactive=True) if item.id == link.id)


@router.get("/links", response_model=list[LoanAccountLinkRead])
def list_links(person_id: int | None = None, include_inactive: bool = False, db: Session = Depends(get_db)):
    if person_id:
        _get_person(db, person_id)
    return LoanService(db).list_links(person_id, include_inactive)


@router.put("/links/{link_id}", response_model=LoanAccountLinkRead)
def update_link(link_id: int, payload: LoanAccountLinkUpdate, db: Session = Depends(get_db)):
    link = _get_link(db, link_id)
    data = payload.model_dump(exclude_unset=True)
    if "person_id" in data:
        if data["person_id"] is None:
            raise HTTPException(status_code=400, detail="Pessoa obrigatoria")
        _get_person(db, data["person_id"])
    if "chart_account_id" in data:
        if data["chart_account_id"] is None:
            raise HTTPException(status_code=400, detail="Conta do plano obrigatoria")
        _ensure_chart_account(db, data["chart_account_id"])
        if data.get("is_active", link.is_active):
            _ensure_chart_account_available(db, data["chart_account_id"], ignore_link_id=link.id)
    elif data.get("is_active") is True:
        _ensure_chart_account_available(db, link.chart_account_id, ignore_link_id=link.id)

    for field, value in data.items():
        setattr(link, field, value)
    db.commit()
    db.refresh(link)
    return next(item for item in LoanService(db).list_links(person_id=link.person_id, include_inactive=True) if item.id == link.id)


@router.delete("/links/{link_id}", response_model=LoanAccountLinkRead)
def deactivate_link(link_id: int, db: Session = Depends(get_db)):
    link = _get_link(db, link_id)
    link.is_active = False
    db.commit()
    db.refresh(link)
    return next(item for item in LoanService(db).list_links(person_id=link.person_id, include_inactive=True) if item.id == link.id)


def _get_person(db: Session, person_id: int) -> LoanPerson:
    person = db.get(LoanPerson, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Pessoa nao encontrada")
    return person


def _get_link(db: Session, link_id: int) -> LoanAccountLink:
    link = db.get(LoanAccountLink, link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Vinculo nao encontrado")
    return link


def _ensure_chart_account(db: Session, chart_account_id: int) -> None:
    if not db.get(ChartAccount, chart_account_id):
        raise HTTPException(status_code=404, detail="Conta do plano nao encontrada")


def _ensure_chart_account_available(db: Session, chart_account_id: int, ignore_link_id: int | None = None) -> None:
    stmt = select(LoanAccountLink.id).where(
        LoanAccountLink.chart_account_id == chart_account_id,
        LoanAccountLink.is_active.is_(True),
    )
    if ignore_link_id is not None:
        stmt = stmt.where(LoanAccountLink.id != ignore_link_id)
    if db.scalar(stmt):
        raise HTTPException(status_code=409, detail="Esta conta do plano ja esta vinculada a outro emprestimo ativo")
