import type { TransactionType } from "./transaction";

export type MatchType = "contains" | "equals" | "starts_with" | "regex";

export interface ClassificationRule {
  id: number;
  keyword: string;
  match_type: MatchType;
  chart_account_id: number;
  transaction_type: TransactionType;
  priority: number;
  active: boolean;
  created_at: string;
  updated_at: string;
}
