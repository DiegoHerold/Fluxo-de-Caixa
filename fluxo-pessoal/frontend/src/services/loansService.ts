import { api } from "./api";
import type { LoanAccountLink, LoanMovement, LoanMovementEffect, LoanPerson } from "../types/loan";

export type LoanPersonPayload = {
  name: string;
  document?: string | null;
  phone?: string | null;
  opening_balance: string;
  notes?: string | null;
  is_active: boolean;
};

export type LoanLinkPayload = {
  person_id: number;
  chart_account_id: number;
  effect: LoanMovementEffect;
  notes?: string | null;
  is_active: boolean;
};

export const loansService = {
  async people(include_inactive = true) {
    const { data } = await api.get<LoanPerson[]>("/loans/people", { params: { include_inactive } });
    return data;
  },
  async createPerson(payload: LoanPersonPayload) {
    const { data } = await api.post<LoanPerson>("/loans/people", payload);
    return data;
  },
  async updatePerson(id: number, payload: Partial<LoanPersonPayload>) {
    const { data } = await api.put<LoanPerson>(`/loans/people/${id}`, payload);
    return data;
  },
  async deactivatePerson(id: number) {
    const { data } = await api.delete<LoanPerson>(`/loans/people/${id}`);
    return data;
  },
  async links(person_id?: number, include_inactive = true) {
    const { data } = await api.get<LoanAccountLink[]>("/loans/links", {
      params: { person_id, include_inactive }
    });
    return data;
  },
  async createLink(payload: LoanLinkPayload) {
    const { data } = await api.post<LoanAccountLink>("/loans/links", payload);
    return data;
  },
  async updateLink(id: number, payload: Partial<LoanLinkPayload>) {
    const { data } = await api.put<LoanAccountLink>(`/loans/links/${id}`, payload);
    return data;
  },
  async deactivateLink(id: number) {
    const { data } = await api.delete<LoanAccountLink>(`/loans/links/${id}`);
    return data;
  },
  async movements(personId: number) {
    const { data } = await api.get<LoanMovement[]>(`/loans/people/${personId}/movements`);
    return data;
  }
};
