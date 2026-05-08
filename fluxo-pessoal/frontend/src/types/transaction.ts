export type TransactionType = "income" | "expense" | "transfer" | "adjustment" | "reserve" | "credit_card_payment";
export type Direction = "in" | "out";
export type ClassificationStatus = "pending" | "automatic" | "manual" | "reviewed";
export type TransactionSource = "manual" | "nubank_csv" | "nubank_ofx" | "mercado_pago_xlsx";

export interface Transaction {
  id: number;
  account_id: number;
  chart_account_id: number | null;
  import_batch_id: number | null;
  reserve_box_id: number | null;
  transaction_date: string;
  description_original: string;
  description_clean: string;
  amount: string;
  transaction_type: TransactionType;
  direction: Direction;
  source: TransactionSource;
  external_id: string | null;
  fingerprint: string;
  classification_status: ClassificationStatus;
  is_internal_transfer: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
  account_name?: string | null;
  chart_account_code?: string | null;
  chart_account_name?: string | null;
}
