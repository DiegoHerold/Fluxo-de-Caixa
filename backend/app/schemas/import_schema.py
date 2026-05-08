from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ImportStatus


class ImportBatchRead(BaseModel):
    id: int
    filename: str
    source_bank: str
    file_type: str
    period_start: date | None
    period_end: date | None
    imported_at: datetime
    total_rows: int
    imported_rows: int
    duplicated_rows: int
    status: ImportStatus
    error_message: str | None

    model_config = ConfigDict(from_attributes=True)


class ImportResult(BaseModel):
    batch: ImportBatchRead
    imported_rows: int
    duplicated_rows: int
    pending_rows: int
    automatic_rows: int


class ImportPeriodDeleteRequest(BaseModel):
    account_id: int
    start_month: str = Field(..., pattern=r"^\d{4}-\d{2}$")
    end_month: str = Field(..., pattern=r"^\d{4}-\d{2}$")
    include_manual: bool = False


class ImportPeriodDeleteResult(BaseModel):
    deleted_transactions: int
    deleted_import_batches: int
    updated_import_batches: int
    period_start: date
    period_end: date
