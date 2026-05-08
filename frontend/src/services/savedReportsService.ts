import { api } from "./api";
import type { SavedReport, SavedReportEvaluation, SavedReportPayload } from "../types/savedReport";

export const savedReportsService = {
  async list(includeInactive = false) {
    const { data } = await api.get<SavedReport[]>("/saved-reports", { params: { include_inactive: includeInactive } });
    return data;
  },
  async create(payload: SavedReportPayload) {
    const { data } = await api.post<SavedReport>("/saved-reports", payload);
    return data;
  },
  async update(id: number, payload: SavedReportPayload) {
    const { data } = await api.put<SavedReport>(`/saved-reports/${id}`, payload);
    return data;
  },
  async remove(id: number) {
    const { data } = await api.delete<SavedReport>(`/saved-reports/${id}`);
    return data;
  },
  async seedDefault() {
    const { data } = await api.post<SavedReport[]>("/saved-reports/seed-default");
    return data;
  },
  async evaluate(id: number, month: string) {
    const { data } = await api.get<SavedReportEvaluation>(`/saved-reports/${id}/evaluate`, { params: { month } });
    return data;
  },
  exportExcelUrl(id: number, month: string) {
    const base = api.defaults.baseURL ?? "";
    return `${base}/saved-reports/${id}/export-excel?month=${encodeURIComponent(month)}`;
  },
  defaultExportExcelUrl(month: string) {
    const base = api.defaults.baseURL ?? "";
    return `${base}/saved-reports/default/export-excel?month=${encodeURIComponent(month)}`;
  }
};
