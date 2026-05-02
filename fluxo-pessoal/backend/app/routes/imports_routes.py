from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.account import Account
from app.models.enums import ClassificationStatus, ImportStatus
from app.models.import_batch import ImportBatch
from app.models.transaction import Transaction
from app.schemas.import_schema import ImportBatchRead, ImportResult
from app.services.balance_service import BalanceService
from app.services.classifier_service import ClassifierService
from app.services.duplicate_service import DuplicateService
from app.services.importers.mercado_pago_xlsx_importer import MercadoPagoXLSXImporter
from app.services.importers.nubank_csv_importer import NubankCSVImporter
from app.services.importers.nubank_ofx_importer import NubankOFXImporter

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
