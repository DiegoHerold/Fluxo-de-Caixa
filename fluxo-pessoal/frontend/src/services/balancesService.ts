import { api } from "./api";
import type { BalanceSnapshot } from "../types/balance";

export const balancesService = {
  async snapshots() {
    const { data } = await api.get<BalanceSnapshot[]>("/balances/snapshots");
    return data;
  },
  async reconcile(payload: { account_id: number; period_month: string; real_balance: string }) {
    const { data } = await api.post<BalanceSnapshot>("/balances/reconcile", payload);
    return data;
  }
};
