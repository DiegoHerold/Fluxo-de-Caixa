import { api } from "./api";
import type { ReportIndicator, ReportIndicatorEvaluation, ReportIndicatorPayload } from "../types/reportIndicator";

export const reportIndicatorsService = {
  async list(includeInactive = false) {
    const { data } = await api.get<ReportIndicator[]>("/report-indicators", { params: { include_inactive: includeInactive } });
    return data;
  },
  async create(payload: ReportIndicatorPayload) {
    const { data } = await api.post<ReportIndicator>("/report-indicators", payload);
    return data;
  },
  async update(id: number, payload: ReportIndicatorPayload) {
    const { data } = await api.put<ReportIndicator>(`/report-indicators/${id}`, payload);
    return data;
  },
  async remove(id: number) {
    const { data } = await api.delete<ReportIndicator>(`/report-indicators/${id}`);
    return data;
  },
  async seedDefault() {
    const { data } = await api.post<ReportIndicator[]>("/report-indicators/seed-default");
    return data;
  },
  async evaluate(month: string, surface?: "dashboard" | "reports") {
    const { data } = await api.get<ReportIndicatorEvaluation[]>("/report-indicators/evaluate", { params: { month, surface } });
    return data;
  }
};
