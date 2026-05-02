import type { ReportIndicatorEvaluation } from "./reportIndicator";

export type DashboardWidgetType = "indicator" | "category_bars" | "account_balances" | "reserve_boxes" | "report_download";

export interface DashboardWidget {
  id: number;
  title: string;
  widget_type: DashboardWidgetType;
  indicator_id: number | null;
  saved_report_id: number | null;
  position: number;
  width: number;
  height: number;
  notes: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface DashboardWidgetPayload {
  title: string;
  widget_type: DashboardWidgetType;
  indicator_id: number | null;
  saved_report_id: number | null;
  position: number;
  width: number;
  height: number;
  notes: string | null;
  is_active: boolean;
}

export interface DashboardWidgetEvaluation extends DashboardWidget {
  indicator: ReportIndicatorEvaluation | null;
  export_url: string | null;
}
