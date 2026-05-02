from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.chart_account import ChartAccount
from app.models.classification_rule import ClassificationRule
from app.schemas.chart_account_schema import ChartAccountCreate, ChartAccountUpdate


class ChartAccountRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payload: ChartAccountCreate) -> ChartAccount:
        item = ChartAccount(**payload.model_dump())
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def list(self, include_inactive: bool = False) -> list[ChartAccount]:
        stmt = select(ChartAccount).order_by(ChartAccount.code)
        if not include_inactive:
            stmt = stmt.where(ChartAccount.is_active.is_(True))
        return list(self.db.scalars(stmt))

    def get(self, chart_account_id: int) -> ChartAccount | None:
        return self.db.get(ChartAccount, chart_account_id)

    def get_by_code(self, code: str) -> ChartAccount | None:
        return self.db.scalar(select(ChartAccount).where(ChartAccount.code == code))

    def update(self, item: ChartAccount, payload: ChartAccountUpdate) -> ChartAccount:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        self.db.commit()
        self.db.refresh(item)
        return item

    def deactivate(self, item: ChartAccount) -> ChartAccount:
        item.is_active = False
        self.db.commit()
        self.db.refresh(item)
        return item

    def deactivate_tree(self, item: ChartAccount) -> ChartAccount:
        ids = self._descendant_ids(item.id)
        self.db.execute(update(ChartAccount).where(ChartAccount.id.in_(ids)).values(is_active=False))
        self.db.execute(update(ClassificationRule).where(ClassificationRule.chart_account_id.in_(ids)).values(active=False))
        self.db.commit()
        self.db.refresh(item)
        return item

    def _descendant_ids(self, root_id: int) -> list[int]:
        ids = [root_id]
        frontier = [root_id]
        while frontier:
            children = list(
                self.db.scalars(
                    select(ChartAccount.id).where(ChartAccount.parent_id.in_(frontier))
                )
            )
            ids.extend(children)
            frontier = children
        return ids
