import { api } from "./api";
import type { DashboardWidget, DashboardWidgetEvaluation, DashboardWidgetPayload } from "../types/dashboardWidget";

export const dashboardWidgetsService = {
  async list() {
    const { data } = await api.get<DashboardWidget[]>("/dashboard-widgets");
    return data;
  },
  async evaluate(month: string) {
    const { data } = await api.get<DashboardWidgetEvaluation[]>("/dashboard-widgets/evaluate", { params: { month } });
    return data;
  },
  async create(payload: DashboardWidgetPayload) {
    const { data } = await api.post<DashboardWidget>("/dashboard-widgets", payload);
    return data;
  },
  async update(id: number, payload: Partial<DashboardWidgetPayload>) {
    const { data } = await api.put<DashboardWidget>(`/dashboard-widgets/${id}`, payload);
    return data;
  },
  async remove(id: number) {
    const { data } = await api.delete<DashboardWidget>(`/dashboard-widgets/${id}`);
    return data;
  },
  async seedDefault() {
    const { data } = await api.post<DashboardWidget[]>("/dashboard-widgets/seed-default");
    return data;
  }
};
