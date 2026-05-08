export interface MonthlyReport {
  month: string;
  opening_balance: string;
  income: string;
  expenses: string;
  fixed_expenses: string;
  variable_expenses: string;
  obligations: string;
  other_expenses: string;
  total_real_expenses: string;
  transfers: string;
  reserves: string;
  adjustments: string;
  result: string;
  cash_result: string;
  pending_count: number;
  consolidated_balance: string;
}

export interface CategoryReportItem {
  chart_account_id: number | null;
  code: string | null;
  name: string;
  account_nature: string | null;
  total: string;
  count: number;
}

export interface ComparisonReportItem {
  month: string;
  income: string;
  expenses: string;
  fixed_expenses: string;
  variable_expenses: string;
  obligations: string;
  other_expenses: string;
  total_real_expenses: string;
  result: string;
  cash_result: string;
  pending_count: number;
}
