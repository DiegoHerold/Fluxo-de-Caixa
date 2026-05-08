import type { ClassificationStatus } from "../../types/transaction";

const statusStyle: Record<string, string> = {
  pending: "bg-amber-50 text-amber-700 border-amber-200",
  automatic: "bg-sky-50 text-sky-700 border-sky-200",
  manual: "bg-emerald-50 text-emerald-700 border-emerald-200",
  reviewed: "bg-violet-50 text-violet-700 border-violet-200",
  balanced: "bg-emerald-50 text-emerald-700 border-emerald-200",
  divergent: "bg-rose-50 text-rose-700 border-rose-200",
  pending_review: "bg-amber-50 text-amber-700 border-amber-200",
  completed: "bg-emerald-50 text-emerald-700 border-emerald-200",
  partially_completed: "bg-amber-50 text-amber-700 border-amber-200",
  failed: "bg-rose-50 text-rose-700 border-rose-200",
  processing: "bg-sky-50 text-sky-700 border-sky-200"
};

export function Badge({ value }: { value: ClassificationStatus | string }) {
  return (
    <span className={`inline-flex rounded-full border px-2 py-1 text-xs font-semibold ${statusStyle[value] ?? "bg-gray-50 text-gray-700 border-gray-200"}`}>
      {value}
    </span>
  );
}
