import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "danger" | "ghost";
  icon?: ReactNode;
};

const variants = {
  primary: "bg-emerald-600 text-white hover:bg-emerald-700",
  secondary: "bg-white text-gray-800 border border-gray-300 hover:bg-gray-50",
  danger: "bg-rose-600 text-white hover:bg-rose-700",
  ghost: "bg-transparent text-gray-700 hover:bg-gray-100"
};

export function Button({ children, variant = "primary", icon, className = "", ...props }: ButtonProps) {
  return (
    <button
      className={`inline-flex min-h-10 items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${variants[variant]} ${className}`}
      {...props}
    >
      {icon}
      {children}
    </button>
  );
}
