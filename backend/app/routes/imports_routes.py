from datetime import date, timedelta

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.account import Account
from app.models.enums import ClassificationStatus, ImportStatus
from app.models.import_batch import ImportBatch
from app.models.transaction import Transaction
from app.schemas.import_schema import ImportBatchRead, ImportPeriodDeleteRequest, ImportPeriodDeleteResult, ImportResult
from app.services.balance_service import BalanceService
from app.services.classifier_service import ClassifierService
from app.services.duplicate_service import DuplicateService
from app.services.importers.mercado_pago_xlsx_importer import MercadoPagoXLSXImporter
from app.services.importers.nubank_csv_importer import NubankCSVImporter
from app.services.importers.nubank_ofx_importer import NubankOFXImporter
from app.utils.dates import month_bounds

router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("/nubank-csv", response_model=ImportResult)
async def import_nubank_csv(account_id: int = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    return await _process_import(db, account_id, file, NubankCSVImporter(), "Nubank", "csv")


@router.post("/nubank-ofx", response_model=ImportResult)
async def import_nubank_ofx(account_id: int = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    return await _process_import(db, account_id, file, NubankOFXImporter(), "Nubank", "ofx")


@router.post("/mercado-pago-xlsx", response_model=ImportResult)
async def import_mercado_pago_xlsx(account_id: int = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    return await _process_import(db, account_id, file, MercadoPagoXLSXImporter(), "Mercado Pago", "xlsx")


@router.get("", response_model=list[ImportBatchRead])
def list_imports(db: Session = Depends(get_db)):
    return list(db.scalars(select(ImportBatch).order_by(ImportBatch.imported_at.desc())))


@router.post("/delete-months", response_model=ImportPeriodDeleteResult)
def delete_imported_months(payload: ImportPeriodDeleteRequest, db: Session = Depends(get_db)):
    if not db.get(Account, payload.account_id):
        raise HTTPException(status_code=404, detail="Conta nao encontrada")

    period_start, _ = month_bounds(payload.start_month)
    last_month_start, period_end_exclusive = month_bounds(payload.end_month)
    if period_start > last_month_start:
        raise HTTPException(status_code=400, detail="Mes inicial deve ser menor ou igual ao mes final")

    stmt = select(Transaction).where(
        Transaction.account_id == payload.account_id,
        Transaction.transaction_date >= period_start,
        Transaction.transaction_date < period_end_exclusive,
    )
    if not payload.include_manual:
        stmt = stmt.where(Transaction.import_batch_id.is_not(None))

    transactions = list(db.scalars(stmt))
    affected_batch_ids = {tx.import_batch_id for tx in transactions if tx.import_batch_id is not None}
    for transaction in transactions:
        db.delete(transaction)
    db.flush()

    deleted_batches, updated_batches = _refresh_import_batches(db, affected_batch_ids)
    db.commit()
    BalanceService(db).recalculate_balances()
    return ImportPeriodDeleteResult(
        deleted_transactions=len(transactions),
        deleted_import_batches=deleted_batches,
        updated_import_batches=updated_batches,
        period_start=period_start,
        period_end=period_end_exclusive - timedelta(days=1),
    )


@router.get("/{batch_id}", response_model=ImportBatchRead)
def get_import(batch_id: int, db: Session = Depends(get_db)):
    batch = db.get(ImportBatch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Importação não encontrada")
    return batch


@router.delete("/{batch_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_import_batch(batch_id: int, db: Session = Depends(get_db)):
    batch = db.get(ImportBatch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Importação não encontrada")
    transactions = list(db.scalars(select(Transaction).where(Transaction.import_batch_id == batch_id)))
    for transaction in transactions:
        db.delete(transaction)
    db.delete(batch)
    db.commit()
    BalanceService(db).recalculate_balances()
    return None


def _refresh_import_batches(db: Session, batch_ids: set[int]) -> tuple[int, int]:
    deleted = 0
    updated = 0
    for batch_id in batch_ids:
        batch = db.get(ImportBatch, batch_id)
        if not batch:
            continue
        remaining = list(db.scalars(select(Transaction).where(Transaction.import_batch_id == batch_id)))
        if not remaining:
            db.delete(batch)
            deleted += 1
            continue
        batch.imported_rows = len(remaining)
        batch.total_rows = max(batch.imported_rows + batch.duplicated_rows, batch.imported_rows)
        batch.period_start = min(tx.transaction_date for tx in remaining)
        batch.period_end = max(tx.transaction_date for tx in remaining)
        batch.status = ImportStatus.completed if batch.duplicated_rows == 0 else ImportStatus.partially_completed
        updated += 1
    return deleted, updated


async def _process_import(db: Session, account_id: int, file: UploadFile, importer, source_bank: str, file_type: str):
    account = db.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Conta não encontrada")

    batch = ImportBatch(
        filename=file.filename or "extrato",
        source_bank=source_bank,
        file_type=file_type,
        status=ImportStatus.processing,
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)

    try:
        content = await file.read()
        payloads = importer.parse(content, batch.filename, account_id)
        duplicate_service = DuplicateService(db)
        classifier = ClassifierService(db)
        dates: list[date] = []
        imported = 0
        duplicated = 0
        automatic = 0
        pending = 0

        for payload in payloads:
            dates.append(payload["transaction_date"])
            if duplicate_service.exists(payload["fingerprint"]):
                duplicated += 1
                continue
            payload["import_batch_id"] = batch.id
            classifier.apply_to_payload(payload)
            tx = Transaction(**payload)
            db.add(tx)
            imported += 1
            if tx.classification_status == ClassificationStatus.automatic:
                automatic += 1
            else:
                pending += 1

        batch.total_rows = len(payloads)
        batch.imported_rows = imported
        batch.duplicated_rows = duplicated
        batch.period_start = min(dates) if dates else None
        batch.period_end = max(dates) if dates else None
        batch.status = ImportStatus.completed if duplicated == 0 else ImportStatus.partially_completed
        db.commit()
        BalanceService(db).recalculate_balances()
        db.refresh(batch)
        return ImportResult(
            batch=batch,
            imported_rows=imported,
            duplicated_rows=duplicated,
            pending_rows=pending,
            automatic_rows=automatic,
        )
    except Exception as exc:
        batch.status = ImportStatus.failed
        batch.error_message = str(exc)
        db.commit()
        raise HTTPException(status_code=400, detail=f"Falha na importação: {exc}") from exc
