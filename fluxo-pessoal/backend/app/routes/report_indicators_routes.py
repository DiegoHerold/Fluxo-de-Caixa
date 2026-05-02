from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.report_indicator_schema import (
    ReportIndicatorCreate,
    ReportIndicatorEvaluation,
    ReportIndicatorRead,
    ReportIndicatorUpdate,
)
from app.services.report_indicator_service import ReportIndicatorService

router = APIRouter(prefix="/report-indicators", tags=["report indicators"])


@router.get("", response_model=list[ReportIndicatorRead])
def list_indicators(include_inactive: bool = False, db: Session = Depends(get_db)):
    return ReportIndicatorService(db).list(include_inactive=include_inactive)


@router.post("", response_model=ReportIndicatorRead)
def create_indicator(payload: ReportIndicatorCreate, db: Session = Depends(get_db)):
    return ReportIndicatorService(db).create(payload)


@router.post("/seed-default", response_model=list[ReportIndicatorRead])
def seed_default_indicators(db: Session = Depends(get_db)):
    return ReportIndicatorService(db).seed_defaults()


@router.get("/evaluate", response_model=list[ReportIndicatorEvaluation])
def evaluate_indicators(
    month: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    surface: str | None = Query(default=None, pattern=r"^(dashboard|reports)$"),
    db: Session = Depends(get_db),
):
    return ReportIndicatorService(db).evaluate(month=month, surface=surface)


@router.get("/{indicator_id}", response_model=ReportIndicatorRead)
def get_indicator(indicator_id: int, db: Session = Depends(get_db)):
    return ReportIndicatorService(db)._to_read(ReportIndicatorService(db).get(indicator_id))


@router.put("/{indicator_id}", response_model=ReportIndicatorRead)
def update_indicator(indicator_id: int, payload: ReportIndicatorUpdate, db: Session = Depends(get_db)):
    return ReportIndicatorService(db).update(indicator_id, payload)


@router.delete("/{indicator_id}", response_model=ReportIndicatorRead)
def delete_indicator(indicator_id: int, db: Session = Depends(get_db)):
    return ReportIndicatorService(db).delete(indicator_id)
