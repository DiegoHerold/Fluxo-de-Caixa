export interface ReserveBox {
  id: number;
  account_id: number;
  chart_account_id: number | null;
  chart_account_code: string | null;
  chart_account_name: string | null;
  withdrawal_chart_account_id: number | null;
  withdrawal_chart_account_code: string | null;
  withdrawal_chart_account_name: string | null;
  name: string;
  current_balance: string;
  target_amount: string | null;
  notes: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
