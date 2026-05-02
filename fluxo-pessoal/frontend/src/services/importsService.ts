import { api } from "./api";
import type { ImportBatch, ImportResult } from "../types/importBatch";

export type ImportSource = "nubank-csv" | "nubank-ofx" | "mercado-pago-xlsx";

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
  }
};
