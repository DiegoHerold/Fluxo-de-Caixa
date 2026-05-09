import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "/api",
  timeout: 30000
});

export function money(value: string | number | null | undefined): string {
  const number = Number(value ?? 0);
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(number);
}

export function formatValue(value: string | number | null | undefined, format: "currency" | "number" | "percent" = "currency"): string {
  const number = Number(value ?? 0);
  if (format === "percent") return `${new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 2 }).format(number)}%`;
  if (format === "number") return new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 2 }).format(number);
  return money(number);
}

export function currentMonth(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

export function todayISODate(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
}

export function formatDateBR(value: string | null | undefined): string {
  if (!value) return "-";
  const [year, month, day] = value.slice(0, 10).split("-");
  if (year && month && day) return `${day}/${month}/${year}`;
  return value;
}

export function formatDateTimeBR(value: string | null | undefined): string {
  if (!value) return "-";
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short"
  }).format(new Date(value));
}
