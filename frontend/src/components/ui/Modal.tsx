import { X } from "lucide-react";
import type { ReactNode } from "react";
import { Button } from "./Button";

export function Modal({
  title,
  description,
  children,
  onClose,
  footer
}: {
  title: string;
  description?: string;
  children: ReactNode;
  onClose: () => void;
  footer?: ReactNode;
}) {
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-gray-950/45 px-4 py-6">
      <div className="max-h-[92vh] w-full max-w-3xl overflow-hidden rounded-xl border border-gray-200 bg-white shadow-2xl">
        <div className="flex items-start justify-between gap-4 border-b border-gray-200 px-5 py-4">
          <div>
            <h2 className="text-base font-bold text-gray-950">{title}</h2>
            {description && <p className="mt-1 text-sm text-gray-500">{description}</p>}
          </div>
          <Button type="button" variant="ghost" title="Fechar" icon={<X size={18} />} onClick={onClose} />
        </div>
        <div className="max-h-[68vh] overflow-y-auto px-5 py-4">{children}</div>
        {footer && <div className="flex justify-end gap-2 border-t border-gray-200 bg-gray-50 px-5 py-4">{footer}</div>}
      </div>
    </div>
  );
}
