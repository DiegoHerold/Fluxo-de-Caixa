export type BalanceStatus = "balanced" | "divergent" | "pending_review";

export interface BalanceSnapshot {
  id: number;
  account_id: number;
  period_month: string;
  initial_balance: string;
  calculated_balance: string;
  real_balance: string | null;
  difference: string | null;
  status: BalanceStatus;
  created_at: string;
  updated_at: string;
}
