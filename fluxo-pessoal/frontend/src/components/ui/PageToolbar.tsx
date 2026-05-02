import type { ReactNode } from "react";

export function PageToolbar({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      {children}
    </div>
  );
}
