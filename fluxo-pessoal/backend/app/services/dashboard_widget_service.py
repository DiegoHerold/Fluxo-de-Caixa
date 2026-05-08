from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.dashboard_widget import DashboardWidget
from app.models.enums import DashboardWidgetType
from app.models.report_indicator import ReportIndicator
from app.models.saved_report import SavedReport
from app.schemas.dashboard_widget_schema import DashboardWidgetCreate, DashboardWidgetEvaluation, DashboardWidgetRead, DashboardWidgetUpdate
from app.services.report_indicator_service import ReportIndicatorService
from app.services.saved_report_service import SavedReportService


class DashboardWidgetService:
    def __init__(self, db: Session):
        self.db = db
        self.indicator_service = ReportIndicatorService(db)

    def list(self, include_inactive: bool = False) -> list[DashboardWidgetRead]:
        stmt = select(DashboardWidget).order_by(DashboardWidget.position, DashboardWidget.id)
        if not include_inactive:
            stmt = stmt.where(DashboardWidget.is_active.is_(True))
        return [DashboardWidgetRead.model_validate(item) for item in self.db.scalars(stmt)]

    def evaluate(self, month: str | None = None, start_month: str | None = None, end_month: str | None = None) -> list[DashboardWidgetEvaluation]:
        start = end = None
        if start_month or end_month:
            start, end = self.indicator_service._period_bounds(month, start_month, end_month)
        stmt = (
            select(DashboardWidget)
            .options(selectinload(DashboardWidget.indicator), selectinload(DashboardWidget.saved_report))
            .where(DashboardWidget.is_active.is_(True))
            .order_by(DashboardWidget.position, DashboardWidget.id)
        )
        widgets: list[DashboardWidgetEvaluation] = []
        for widget in self.db.scalars(stmt):
            indicator = None
            export_url = None
            if widget.widget_type == DashboardWidgetType.indicator and widget.indicator:
                indicator = self.indicator_service._evaluate_indicator(widget.indicator, month, start=start, end=end)
            if widget.widget_type == DashboardWidgetType.report_download and widget.saved_report_id:
                export_month = month or end_month or start_month
                export_url = f"/api/saved-reports/{widget.saved_report_id}/export-excel?month={export_month}"
            widgets.append(
                DashboardWidgetEvaluation(
                    **DashboardWidgetRead.model_validate(widget).model_dump(),
                    indicator=indicator,
                    export_url=export_url,
                )
            )
        return widgets

    def get(self, widget_id: int) -> DashboardWidget:
        widget = self.db.get(DashboardWidget, widget_id)
        if not widget:
            raise HTTPException(status_code=404, detail="Widget não encontrado")
        return widget

    def create(self, payload: DashboardWidgetCreate) -> DashboardWidgetRead:
        widget = DashboardWidget(**payload.model_dump())
        self.db.add(widget)
        self.db.commit()
        self.db.refresh(widget)
        return DashboardWidgetRead.model_validate(widget)

    def update(self, widget_id: int, payload: DashboardWidgetUpdate) -> DashboardWidgetRead:
        widget = self.get(widget_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(widget, field, value)
        self.db.commit()
        self.db.refresh(widget)
        return DashboardWidgetRead.model_validate(widget)

    def delete(self, widget_id: int) -> DashboardWidgetRead:
        widget = self.get(widget_id)
        deleted = DashboardWidgetRead.model_validate(widget)
        self.db.delete(widget)
        self.db.commit()
        return deleted

    def seed_defaults(self) -> list[DashboardWidgetRead]:
        self.indicator_service.seed_defaults()
        SavedReportService(self.db).seed_defaults()

        created: list[DashboardWidgetRead] = []
        default_report = SavedReportService(self.db).default()
        has_report_download = self.db.scalar(
            select(DashboardWidget.id).where(
                DashboardWidget.widget_type == DashboardWidgetType.report_download,
                DashboardWidget.saved_report_id == (default_report.id if default_report else None),
            )
        )
        if default_report and not has_report_download:
            created.append(
                self.create(
                    DashboardWidgetCreate(
                        title="Baixar relatório padrão",
                        widget_type=DashboardWidgetType.report_download,
                        saved_report_id=default_report.id,
                        position=0,
                        width=1,
                    )
                )
            )
        existing_indicator_ids = set(
            self.db.scalars(
                select(DashboardWidget.indicator_id).where(
                    DashboardWidget.widget_type == DashboardWidgetType.indicator,
                    DashboardWidget.indicator_id.is_not(None),
                )
            )
        )
        indicators = list(
            self.db.scalars(
                select(ReportIndicator)
                .where(ReportIndicator.is_active.is_(True), ReportIndicator.show_on_dashboard.is_(True))
                .order_by(ReportIndicator.display_order)
                .limit(8)
            )
        )
        for position, indicator in enumerate(indicators, start=1):
            if indicator.id in existing_indicator_ids:
                continue
            created.append(
                self.create(
                    DashboardWidgetCreate(
                        title=indicator.name,
                        widget_type=DashboardWidgetType.indicator,
                        indicator_id=indicator.id,
                        position=position,
                        width=2 if position == 1 else 1,
                    )
                )
            )
        return created
