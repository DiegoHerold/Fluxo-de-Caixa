import type { ReactNode } from "react";

export function StatCard({ label, value, icon, tone = "emerald" }: { label: string; value: ReactNode; icon?: ReactNode; tone?: "emerald" | "sky" | "rose" | "amber" | "violet" }) {
  const tones = {
    emerald: "border-emerald-100 bg-emerald-50 text-emerald-700",
    sky: "border-sky-100 bg-sky-50 text-sky-700",
    rose: "border-rose-100 bg-rose-50 text-rose-700",
    amber: "border-amber-100 bg-amber-50 text-amber-700",
    violet: "border-violet-100 bg-violet-50 text-violet-700"
  };
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="flex items-center justify-between gap-3">
        <span className="text-sm font-medium text-gray-500">{label}</span>
        {icon && <span className={`grid h-9 w-9 place-items-center rounded-lg border ${tones[tone]}`}>{icon}</span>}
      </div>
      <div className="mt-3 text-2xl font-bold text-gray-950">{value}</div>
    </div>
  );
}
