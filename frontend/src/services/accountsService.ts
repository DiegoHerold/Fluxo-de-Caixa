import { api } from "./api";
import type { Account, AccountBalance, ConsolidatedBalance, ReserveBalance } from "../types/account";

export type AccountPayload = {
  name: string;
  institution?: string | null;
  account_type: string;
  initial_balance: string;
  is_active: boolean;
};

export const accountsService = {
  async list() {
    const { data } = await api.get<Account[]>("/accounts", { params: { include_inactive: true } });
    return data;
  },
  async create(payload: AccountPayload) {
    const { data } = await api.post<Account>("/accounts", payload);
    return data;
  },
  async update(id: number, payload: Partial<AccountPayload>) {
    const { data } = await api.put<Account>(`/accounts/${id}`, payload);
    return data;
  },
  async deactivate(id: number) {
    const { data } = await api.delete<Account>(`/accounts/${id}`);
    return data;
  },
  async balances() {
    const { data } = await api.get<AccountBalance[]>("/accounts/balances");
    return data;
  },
  async consolidated() {
    const { data } = await api.get<ConsolidatedBalance>("/accounts/consolidated-balance");
    return data;
  },
  async reserves() {
    const { data } = await api.get<ReserveBalance[]>("/accounts/reserves");
    return data;
  }
};
