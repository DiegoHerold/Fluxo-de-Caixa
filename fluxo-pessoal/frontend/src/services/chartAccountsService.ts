import { api } from "./api";
import type { ChartAccount, ChartAccountTree } from "../types/chartAccount";

export type ChartAccountPayload = {
  code: string;
  name: string;
  parent_id: number | null;
  account_nature: string;
  is_active: boolean;
};

export const chartAccountsService = {
  async list(includeInactive = false) {
    const { data } = await api.get<ChartAccount[]>("/chart-accounts", { params: { include_inactive: includeInactive } });
    return data;
  },
  async tree() {
    const { data } = await api.get<ChartAccountTree[]>("/chart-accounts/tree");
    return data;
  },
  async create(payload: ChartAccountPayload) {
    const { data } = await api.post<ChartAccount>("/chart-accounts", payload);
    return data;
  },
  async update(id: number, payload: Partial<ChartAccountPayload>) {
    const { data } = await api.put<ChartAccount>(`/chart-accounts/${id}`, payload);
    return data;
  },
  async remove(id: number) {
    const { data } = await api.delete<ChartAccount>(`/chart-accounts/${id}`);
    return data;
  },
  async cleanupDuplicates() {
    const { data } = await api.post<{ removed_duplicates: number }>("/chart-accounts/cleanup-duplicates");
    return data;
  },
  async seedDefault() {
    const { data } = await api.post<ChartAccount[]>("/chart-accounts/seed-default");
    return data;
  }
};
