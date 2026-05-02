import type { ReportIndicator, ReportIndicatorEvaluation } from "./reportIndicator";

export interface SavedReportIndicatorPayload {
  indicator_id: number;
  position: number;
}

export interface SavedReport {
  id: number;
  name: string;
  description: string | null;
  is_default_dashboard: boolean;
  is_active: boolean;
  display_order: number;
  indicators: ReportIndicator[];
  created_at: string;
  updated_at: string;
}

export interface SavedReportPayload {
  name: string;
  description: string | null;
  is_default_dashboard: boolean;
  is_active: boolean;
  display_order: number;
  indicators: SavedReportIndicatorPayload[];
}

export interface SavedReportEvaluation {
  id: number;
  name: string;
  description: string | null;
  is_default_dashboard: boolean;
  indicators: ReportIndicatorEvaluation[];
}
