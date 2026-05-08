export type ImportStatus = "processing" | "completed" | "failed" | "partially_completed";

export interface ImportBatch {
  id: number;
  filename: string;
  source_bank: string;
  file_type: string;
  period_start: string | null;
  period_end: string | null;
  imported_at: string;
  total_rows: number;
  imported_rows: number;
  duplicated_rows: number;
  status: ImportStatus;
  error_message: string | null;
}

export interface ImportResult {
  batch: ImportBatch;
  imported_rows: number;
  duplicated_rows: number;
  pending_rows: number;
  automatic_rows: number;
}
