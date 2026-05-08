import { api } from "./api";
import type { ReserveBox } from "../types/reserveBox";

export type ReserveBoxPayload = {
  account_id: number;
  chart_account_id?: number | null;
  withdrawal_chart_account_id?: number | null;
  auto_create_chart_accounts?: boolean;
  name: string;
  current_balance: string;
  target_amount?: string | null;
  notes?: string | null;
  is_active: boolean;
};

export const reserveBoxesService = {
  async list(account_id?: number) {
    const { data } = await api.get<ReserveBox[]>("/reserve-boxes", {
      params: { account_id, include_inactive: true }
    });
    return data;
  },
  async create(payload: ReserveBoxPayload) {
    const { data } = await api.post<ReserveBox>("/reserve-boxes", payload);
    return data;
  },
  async update(id: number, payload: Partial<ReserveBoxPayload>) {
    const { data } = await api.put<ReserveBox>(`/reserve-boxes/${id}`, payload);
    return data;
  },
  async deactivate(id: number) {
    const { data } = await api.delete<ReserveBox>(`/reserve-boxes/${id}`);
    return data;
  }
};
