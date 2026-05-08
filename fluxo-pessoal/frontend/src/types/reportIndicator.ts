export type FormulaOperation = "add" | "subtract" | "multiply" | "divide";
export type FormulaValueMode = "net" | "inflow" | "outflow" | "absolute";
export type IndicatorResultFormat = "currency" | "number" | "percent";

export interface ReportIndicatorTerm {
  id: number;
  chart_account_id: number;
  chart_account_code: string | null;
  chart_account_name: string | null;
  operation: FormulaOperation;
  value_mode: FormulaValueMode;
  variable_key: string | null;
  weight: string;
  probability: string;
  include_children: boolean;
  label: string | null;
  position: number;
}

export interface ReportIndicator {
  id: number;
  name: string;
  description: string | null;
  result_label: string;
  result_format: IndicatorResultFormat;
  formula_expression: string | null;
  positive_is_good: boolean;
  include_internal_transfers: boolean;
  show_on_dashboard: boolean;
  show_on_reports: boolean;
  display_order: number;
  is_active: boolean;
  terms: ReportIndicatorTerm[];
  created_at: string;
  updated_at: string;
}

export interface ReportIndicatorTermPayload {
  chart_account_id: number;
  operation: FormulaOperation;
  value_mode: FormulaValueMode;
  variable_key: string | null;
  weight: string;
  probability: string;
  include_children: boolean;
  label: string | null;
  position: number;
}

export interface ReportIndicatorPayload {
  name: string;
  description: string | null;
  result_label: string;
  result_format: IndicatorResultFormat;
  formula_expression: string | null;
  positive_is_good: boolean;
  include_internal_transfers: boolean;
  show_on_dashboard: boolean;
  show_on_reports: boolean;
  display_order: number;
  is_active: boolean;
  terms: ReportIndicatorTermPayload[];
}

export interface ReportIndicatorTermEvaluation {
  label: string;
  chart_account_id: number;
  chart_account_code: string;
  chart_account_name: string;
  operation: FormulaOperation;
  value_mode: FormulaValueMode;
  variable_key: string | null;
  weight: string;
  probability: string;
  include_children: boolean;
  amount: string;
  adjusted_amount: string;
  contribution: string;
}

export interface ReportIndicatorEvaluation {
  id: number;
  name: string;
  description: string | null;
  result_label: string;
  result_format: IndicatorResultFormat;
  formula_expression: string | null;
  positive_is_good: boolean;
  include_internal_transfers: boolean;
  show_on_dashboard: boolean;
  show_on_reports: boolean;
  display_order: number;
  result: string;
  terms: ReportIndicatorTermEvaluation[];
}
