from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.dashboard_widget_schema import DashboardWidgetCreate, DashboardWidgetEvaluation, DashboardWidgetRead, DashboardWidgetUpdate
from app.services.dashboard_widget_service import DashboardWidgetService

router = APIRouter(prefix="/dashboard-widgets", tags=["dashboard widgets"])


@router.get("", response_model=list[DashboardWidgetRead])
def list_dashboard_widgets(include_inactive: bool = False, db: Session = Depends(get_db)):
    return DashboardWidgetService(db).list(include_inactive=include_inactive)


@router.get("/evaluate", response_model=list[DashboardWidgetEvaluation])
def evaluate_dashboard_widgets(
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    start_month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    end_month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    db: Session = Depends(get_db),
):
    return DashboardWidgetService(db).evaluate(month=month, start_month=start_month, end_month=end_month)


@router.post("", response_model=DashboardWidgetRead)
def create_dashboard_widget(payload: DashboardWidgetCreate, db: Session = Depends(get_db)):
    return DashboardWidgetService(db).create(payload)


@router.post("/seed-default", response_model=list[DashboardWidgetRead])
def seed_default_dashboard_widgets(db: Session = Depends(get_db)):
    return DashboardWidgetService(db).seed_defaults()


@router.put("/{widget_id}", response_model=DashboardWidgetRead)
def update_dashboard_widget(widget_id: int, payload: DashboardWidgetUpdate, db: Session = Depends(get_db)):
    return DashboardWidgetService(db).update(widget_id, payload)


@router.delete("/{widget_id}", response_model=DashboardWidgetRead)
def delete_dashboard_widget(widget_id: int, db: Session = Depends(get_db)):
    return DashboardWidgetService(db).delete(widget_id)
