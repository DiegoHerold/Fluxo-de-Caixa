from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.chart_account_repository import ChartAccountRepository
from app.schemas.chart_account_schema import ChartAccountCreate, ChartAccountRead, ChartAccountTree, ChartAccountUpdate
from app.services.chart_account_seed import cleanup_duplicate_chart_accounts, seed_default_chart_accounts

router = APIRouter(prefix="/chart-accounts", tags=["chart accounts"])


@router.post("/seed-default", response_model=list[ChartAccountRead])
def seed_default(db: Session = Depends(get_db)):
    return seed_default_chart_accounts(db)


@router.post("/cleanup-duplicates")
def cleanup_duplicates(db: Session = Depends(get_db)):
    removed_count = cleanup_duplicate_chart_accounts(db)
    return {"removed_duplicates": removed_count}


@router.get("/tree", response_model=list[ChartAccountTree])
def chart_accounts_tree(include_inactive: bool = False, db: Session = Depends(get_db)):
    items = ChartAccountRepository(db).list(include_inactive=include_inactive)
    nodes: dict[int, ChartAccountTree] = {}
    for item in items:
        node = ChartAccountTree.model_validate(item)
        node.children = []
        nodes[item.id] = node

    roots: list[ChartAccountTree] = []
    for item in items:
        node = nodes[item.id]
        if item.parent_id and item.parent_id in nodes:
            nodes[item.parent_id].children.append(node)
        else:
            roots.append(node)
    return roots


@router.post("", response_model=ChartAccountRead, status_code=status.HTTP_201_CREATED)
def create_chart_account(payload: ChartAccountCreate, db: Session = Depends(get_db)):
    try:
        return ChartAccountRepository(db).create(payload)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"Já existe uma conta com o código '{payload.code}'.")


@router.get("", response_model=list[ChartAccountRead])
def list_chart_accounts(include_inactive: bool = False, db: Session = Depends(get_db)):
    return ChartAccountRepository(db).list(include_inactive=include_inactive)


@router.put("/{chart_account_id}", response_model=ChartAccountRead)
def update_chart_account(chart_account_id: int, payload: ChartAccountUpdate, db: Session = Depends(get_db)):
    repo = ChartAccountRepository(db)
    item = repo.get(chart_account_id)
    if not item:
        raise HTTPException(status_code=404, detail="Conta do plano não encontrada")
    try:
        return repo.update(item, payload)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"Já existe uma conta com o código '{payload.code}'.")


@router.delete("/{chart_account_id}", response_model=ChartAccountRead)
def delete_chart_account(chart_account_id: int, db: Session = Depends(get_db)):
    repo = ChartAccountRepository(db)
    item = repo.get(chart_account_id)
    if not item:
        raise HTTPException(status_code=404, detail="Conta do plano não encontrada")

    return repo.deactivate_tree(item)
