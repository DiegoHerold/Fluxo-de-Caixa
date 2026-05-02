import type { InputHTMLAttributes, SelectHTMLAttributes } from "react";

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
};

export function Input({ label, className = "", ...props }: InputProps) {
  return (
    <label className="grid gap-1 text-sm font-medium text-gray-700">
      <span>{label}</span>
      <input
        className={`min-h-10 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100 ${className}`}
        {...props}
      />
    </label>
  );
}

type SelectProps = SelectHTMLAttributes<HTMLSelectElement> & {
  label: string;
};

export function Select({ label, className = "", children, ...props }: SelectProps) {
  return (
    <label className="grid gap-1 text-sm font-medium text-gray-700">
      <span>{label}</span>
      <select
        className={`min-h-10 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100 ${className}`}
        {...props}
      >
        {children}
      </select>
    </label>
  );
}
