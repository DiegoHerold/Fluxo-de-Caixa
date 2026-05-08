import type { ReactNode } from "react";

export function EmptyState({ title, description, action }: { title: string; description?: string; action?: ReactNode }) {
  return (
    <div className="rounded-xl border border-dashed border-gray-300 bg-white px-6 py-10 text-center">
      <div className="text-sm font-bold text-gray-900">{title}</div>
      {description && <p className="mx-auto mt-2 max-w-md text-sm text-gray-500">{description}</p>}
      {action && <div className="mt-4 flex justify-center">{action}</div>}
    </div>
  );
}
