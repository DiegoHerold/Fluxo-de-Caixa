from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.report_schema import CategoryReportItem, ComparisonReportItem, MonthlyReport
from app.services.export_excel_service import ExportExcelService
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/monthly", response_model=MonthlyReport)
def monthly_report(month: str = Query(..., pattern=r"^\d{4}-\d{2}$"), db: Session = Depends(get_db)):
    return ReportService(db).monthly(month)


@router.get("/categories", response_model=list[CategoryReportItem])
def categories_report(month: str = Query(..., pattern=r"^\d{4}-\d{2}$"), db: Session = Depends(get_db)):
    return ReportService(db).categories(month)


@router.get("/comparison", response_model=list[ComparisonReportItem])
def comparison_report(
    start_month: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    end_month: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    db: Session = Depends(get_db),
):
    return ReportService(db).comparison(start_month, end_month)


@router.get("/export-excel")
def export_excel(month: str = Query(..., pattern=r"^\d{4}-\d{2}$"), db: Session = Depends(get_db)):
    output = ExportExcelService(db).export_month(month)
    headers = {"Content-Disposition": f'attachment; filename="fluxo-pessoal-{month}.xlsx"'}
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )
