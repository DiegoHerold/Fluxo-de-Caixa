export type LoanMovementEffect = "increase" | "decrease";

export interface LoanPerson {
  id: number;
  name: string;
  document: string | null;
  phone: string | null;
  opening_balance: string;
  current_balance: string;
  movement_increase_total: string;
  movement_decrease_total: string;
  linked_accounts_count: number;
  notes: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LoanAccountLink {
  id: number;
  person_id: number;
  chart_account_id: number;
  chart_account_code: string | null;
  chart_account_name: string | null;
  effect: LoanMovementEffect;
  notes: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LoanMovement {
  transaction_id: number;
  transaction_date: string;
  description: string;
  account_name: string | null;
  chart_account_id: number;
  chart_account_code: string | null;
  chart_account_name: string | null;
  transaction_amount: string;
  effect: LoanMovementEffect;
  debt_delta: string;
  balance_after: string;
}
