import { api } from "./api";
import type { ImportBatch, ImportResult } from "../types/importBatch";

export type ImportSource = "nubank-csv" | "nubank-ofx" | "mercado-pago-xlsx";

export type ImportMonthDeletePayload = {
  account_id: number;
  start_month: string;
  end_month: string;
  include_manual?: boolean;
};

export type ImportMonthDeleteResult = {
  deleted_transactions: number;
  deleted_import_batches: number;
  updated_import_batches: number;
  period_start: string;
  period_end: string;
};

export const importsService = {
  async upload(source: ImportSource, accountId: number, file: File) {
    const formData = new FormData();
    formData.append("account_id", String(accountId));
    formData.append("file", file);
    const { data } = await api.post<ImportResult>(`/imports/${source}`, formData, {
      headers: { "Content-Type": "multipart/form-data" }
    });
    return data;
  },
  async list() {
    const { data } = await api.get<ImportBatch[]>("/imports");
    return data;
  },
  async remove(id: number) {
    await api.delete(`/imports/${id}`);
  },
  async removeMonths(payload: ImportMonthDeletePayload) {
    const { data } = await api.post<ImportMonthDeleteResult>("/imports/delete-months", payload);
    return data;
  }
};
