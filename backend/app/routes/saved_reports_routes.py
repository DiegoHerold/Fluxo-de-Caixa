from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.saved_report_schema import SavedReportCreate, SavedReportEvaluation, SavedReportRead, SavedReportUpdate
from app.services.saved_report_service import SavedReportService

router = APIRouter(prefix="/saved-reports", tags=["saved reports"])


@router.get("", response_model=list[SavedReportRead])
def list_saved_reports(include_inactive: bool = False, db: Session = Depends(get_db)):
    return SavedReportService(db).list(include_inactive=include_inactive)


@router.post("", response_model=SavedReportRead)
def create_saved_report(payload: SavedReportCreate, db: Session = Depends(get_db)):
    return SavedReportService(db).create(payload)


@router.post("/seed-default", response_model=list[SavedReportRead])
def seed_default_saved_reports(db: Session = Depends(get_db)):
    return SavedReportService(db).seed_defaults()


@router.get("/default/export-excel")
def export_default_saved_report(month: str = Query(..., pattern=r"^\d{4}-\d{2}$"), db: Session = Depends(get_db)):
    service = SavedReportService(db)
    report = service.default()
    if not report:
        service.seed_defaults()
        report = service.default()
    output = service.export_excel(report.id, month)
    headers = {"Content-Disposition": f'attachment; filename="fluxo-pessoal-relatorio-padrao-{month}.xlsx"'}
    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)


@router.get("/{report_id}", response_model=SavedReportRead)
def get_saved_report(report_id: int, db: Session = Depends(get_db)):
    service = SavedReportService(db)
    return service._to_read(service.get(report_id))


@router.get("/{report_id}/evaluate", response_model=SavedReportEvaluation)
def evaluate_saved_report(report_id: int, month: str = Query(..., pattern=r"^\d{4}-\d{2}$"), db: Session = Depends(get_db)):
    return SavedReportService(db).evaluate(report_id, month)


@router.get("/{report_id}/export-excel")
def export_saved_report(report_id: int, month: str = Query(..., pattern=r"^\d{4}-\d{2}$"), db: Session = Depends(get_db)):
    service = SavedReportService(db)
    report = service.get(report_id)
    output = service.export_excel(report_id, month)
    headers = {"Content-Disposition": f'attachment; filename="fluxo-pessoal-{report.name}-{month}.xlsx"'}
    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)


@router.put("/{report_id}", response_model=SavedReportRead)
def update_saved_report(report_id: int, payload: SavedReportUpdate, db: Session = Depends(get_db)):
    return SavedReportService(db).update(report_id, payload)


@router.delete("/{report_id}", response_model=SavedReportRead)
def delete_saved_report(report_id: int, db: Session = Depends(get_db)):
    return SavedReportService(db).delete(report_id)
