from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.report_indicator import ReportIndicator
from app.routes.accounts_routes import router as accounts_router
from app.routes.balances_routes import router as balances_router
from app.routes.chart_accounts_routes import router as chart_accounts_router
from app.routes.classification_rules_routes import router as classification_rules_router
from app.routes.dashboard_widgets_routes import router as dashboard_widgets_router
from app.routes.imports_routes import router as imports_router
from app.routes.report_indicators_routes import router as report_indicators_router
from app.routes.reports_routes import router as reports_router
from app.routes.reserve_boxes_routes import router as reserve_boxes_router
from app.routes.saved_reports_routes import router as saved_reports_router
from app.routes.transactions_routes import router as transactions_router
from app.services.chart_account_seed import seed_default_chart_accounts
from app.services.dashboard_widget_service import DashboardWidgetService
from app.services.report_indicator_service import ReportIndicatorService
from app.services.saved_report_service import SavedReportService

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(accounts_router, prefix=settings.api_prefix)
app.include_router(chart_accounts_router, prefix=settings.api_prefix)
app.include_router(transactions_router, prefix=settings.api_prefix)
app.include_router(imports_router, prefix=settings.api_prefix)
app.include_router(classification_rules_router, prefix=settings.api_prefix)
app.include_router(reports_router, prefix=settings.api_prefix)
app.include_router(report_indicators_router, prefix=settings.api_prefix)
app.include_router(saved_reports_router, prefix=settings.api_prefix)
app.include_router(dashboard_widgets_router, prefix=settings.api_prefix)
app.include_router(balances_router, prefix=settings.api_prefix)
app.include_router(reserve_boxes_router, prefix=settings.api_prefix)


@app.on_event("startup")
def seed_defaults_on_empty_database() -> None:
    db = SessionLocal()
    try:
        has_indicators = db.scalar(select(ReportIndicator.id).limit(1))
        if has_indicators:
            return
        seed_default_chart_accounts(db)
        ReportIndicatorService(db).seed_defaults()
        SavedReportService(db).seed_defaults()
        DashboardWidgetService(db).seed_defaults()
    finally:
        db.close()


@app.get("/")
def root():
    return {"name": settings.app_name, "docs": "/docs", "api_prefix": settings.api_prefix}


@app.get("/health")
def health():
    return {"status": "ok"}
