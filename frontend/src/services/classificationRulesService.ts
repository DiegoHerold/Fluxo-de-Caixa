import { api } from "./api";
import type { ClassificationRule } from "../types/classificationRule";
import type { TransactionType } from "../types/transaction";

export type ClassificationRulePayload = {
  keyword: string;
  match_type: string;
  chart_account_id: number;
  transaction_type: TransactionType;
  priority: number;
  active: boolean;
};

export const classificationRulesService = {
  async list() {
    const { data } = await api.get<ClassificationRule[]>("/classification-rules");
    return data;
  },
  async create(payload: ClassificationRulePayload) {
    const { data } = await api.post<ClassificationRule>("/classification-rules", payload);
    return data;
  },
  async update(id: number, payload: Partial<ClassificationRulePayload>) {
    const { data } = await api.put<ClassificationRule>(`/classification-rules/${id}`, payload);
    return data;
  },
  async deactivate(id: number) {
    const { data } = await api.delete<ClassificationRule>(`/classification-rules/${id}`);
    return data;
  },
  async remove(id: number) {
    await api.delete(`/classification-rules/${id}/permanent`);
  },
  async applyToPending() {
    const { data } = await api.post<{ updated: number; remaining_pending: number }>("/classification-rules/apply-to-pending");
    return data;
  }
};
