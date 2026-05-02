export interface ReserveBox {
  id: number;
  account_id: number;
  name: string;
  current_balance: string;
  target_amount: string | null;
  notes: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
