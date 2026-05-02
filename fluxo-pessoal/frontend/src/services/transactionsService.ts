import { api } from "./api";
import type { ClassificationStatus, Transaction, TransactionType } from "../types/transaction";

export type TransactionFilters = {
  account_id?: number;
  chart_account_id?: number;
  status?: ClassificationStatus;
  transaction_type?: TransactionType;
  start_date?: string;
  end_date?: string;
};

export type ManualTransactionPayload = {
  account_id: number;
  chart_account_id?: number | null;
  transaction_date: string;
  description_original: string;
  amount: string;
  transaction_type?: TransactionType;
  direction?: "in" | "out";
  notes?: string | null;
  is_internal_transfer: boolean;
};

export const transactionsService = {
  async list(filters: TransactionFilters = {}) {
    const { data } = await api.get<Transaction[]>("/transactions", { params: filters });
    return data;
  },
  async pending() {
    const { data } = await api.get<Transaction[]>("/transactions/pending");
    return data;
  },
  async createManual(payload: ManualTransactionPayload) {
    const { data } = await api.post<Transaction>("/transactions/manual", payload);
    return data;
  },
  async update(id: number, payload: Partial<ManualTransactionPayload>) {
    const { data } = await api.put<Transaction>(`/transactions/${id}`, payload);
    return data;
  },
  async remove(id: number) {
    await api.delete(`/transactions/${id}`);
  },
  async classify(
    id: number,
    payload: {
      chart_account_id: number;
      transaction_type: TransactionType;
      is_internal_transfer: boolean;
      notes?: string | null;
      create_rule?: boolean;
      rule_keyword?: string | null;
      rule_match_type?: string;
      rule_priority?: number;
    }
  ) {
    const { data } = await api.put<Transaction>(`/transactions/${id}/classify`, payload);
    return data;
  },
  async createRuleFromClassification(id: number, payload: { keyword: string; match_type: string; priority: number }) {
    const { data } = await api.post(`/transactions/${id}/create-rule-from-classification`, payload);
    return data;
  }
};
