import { money } from "../../services/api";
import type { CategoryReportItem } from "../../types/report";

export function CategoryBars({ categories, title = "Maiores categorias" }: { categories: CategoryReportItem[]; title?: string }) {
  const max = Math.max(...categories.map((item) => Math.abs(Number(item.total))), 1);
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <h2 className="text-sm font-bold text-gray-900">{title}</h2>
      <div className="mt-4 grid gap-3">
        {categories.slice(0, 8).map((item) => {
          const value = Math.abs(Number(item.total));
          return (
            <div key={`${item.chart_account_id}-${item.name}`} className="grid gap-1">
              <div className="flex items-center justify-between gap-3 text-sm">
                <span className="truncate font-medium text-gray-700">{item.name}</span>
                <span className="whitespace-nowrap font-semibold text-gray-900">{money(value)}</span>
              </div>
              <div className="h-2 rounded-full bg-gray-100">
                <div className="h-2 rounded-full bg-sky-500" style={{ width: `${Math.max((value / max) * 100, 4)}%` }} />
              </div>
            </div>
          );
        })}
        {categories.length === 0 && <p className="text-sm text-gray-500">Sem dados para o mês.</p>}
      </div>
    </div>
  );
}
