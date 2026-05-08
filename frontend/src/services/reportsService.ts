import { api } from "./api";
import type { CategoryReportItem, ComparisonReportItem, MonthlyReport } from "../types/report";

export const reportsService = {
  async monthly(month: string) {
    const { data } = await api.get<MonthlyReport>("/reports/monthly", { params: { month } });
    return data;
  },
  async categories(month: string) {
    const { data } = await api.get<CategoryReportItem[]>("/reports/categories", { params: { month } });
    return data;
  },
  async comparison(start_month: string, end_month: string) {
    const { data } = await api.get<ComparisonReportItem[]>("/reports/comparison", {
      params: { start_month, end_month }
    });
    return data;
  },
  exportExcelUrl(month: string) {
    const base = api.defaults.baseURL ?? "";
    return `${base}/reports/export-excel?month=${encodeURIComponent(month)}`;
  }
};
