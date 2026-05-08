export type AccountType = "checking" | "wallet" | "credit_card" | "reserve" | "investment" | "cash" | "manual";

export interface Account {
  id: number;
  name: string;
  institution: string | null;
  account_type: AccountType;
  initial_balance: string;
  current_balance: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AccountBalance {
  id: number;
  name: string;
  institution: string | null;
  account_type: AccountType;
  initial_balance: string;
  calculated_balance: string;
  reserve_balance: string;
  balance_with_reserves: string;
  current_balance: string;
  is_active: boolean;
}

export interface ConsolidatedBalance {
  available_balance: string;
  reserve_balance: string;
  consolidated_balance: string;
  accounts: AccountBalance[];
  reserves: ReserveBalance[];
}

export interface ReserveBalance {
  account_id: number;
  name: string;
  balance: string;
  source: "manual" | "detected";
}
