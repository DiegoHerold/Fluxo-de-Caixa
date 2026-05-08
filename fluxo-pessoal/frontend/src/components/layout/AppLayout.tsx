import { BarChart3, FileInput, HandCoins, Home, Layers3, ListChecks, PiggyBank, ReceiptText, Repeat2, Scale, Settings2, SlidersHorizontal } from "lucide-react";
import { NavLink, Outlet, useLocation } from "react-router-dom";

const navItems = [
  { to: "/", label: "Dashboard", icon: Home },
  { to: "/accounts", label: "Contas", icon: PiggyBank },
  { to: "/imports", label: "Importar", icon: FileInput },
  { to: "/transactions", label: "Movimentações", icon: ReceiptText },
  { to: "/loans", label: "Emprestimos", icon: HandCoins },
  { to: "/pending", label: "Pendências", icon: ListChecks },
  { to: "/chart-accounts", label: "Plano", icon: Layers3 },
  { to: "/indicators", label: "Indicadores", icon: SlidersHorizontal },
  { to: "/rules", label: "Regras", icon: Repeat2 },
  { to: "/reports", label: "Relatórios", icon: BarChart3 },
  { to: "/balances", label: "Conciliação", icon: Scale }
];

const titles: Record<string, string> = {
  "/": "Dashboard mensal",
  "/accounts": "Contas financeiras",
  "/imports": "Importação de extratos",
  "/transactions": "Movimentações",
  "/loans": "Emprestimos",
  "/pending": "Pendências de classificação",
  "/chart-accounts": "Plano de contas",
  "/indicators": "Indicadores personalizados",
  "/rules": "Regras automáticas",
  "/reports": "Relatórios",
  "/balances": "Conciliação"
};

export function AppLayout() {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-slate-50 text-gray-950">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-gray-200 bg-white lg:block">
        <div className="flex h-20 items-center gap-3 border-b border-gray-200 px-5">
          <div className="grid h-11 w-11 place-items-center rounded-xl bg-emerald-600 text-white shadow-sm">
            <Settings2 size={20} />
          </div>
          <div>
            <div className="text-base font-black tracking-tight">Fluxo Pessoal</div>
            <div className="text-xs font-medium text-gray-500">financeiro mensal</div>
          </div>
        </div>
        <nav className="grid gap-1 p-3">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex min-h-11 items-center gap-3 rounded-xl px-3 py-2 text-sm font-bold transition ${
                  isActive ? "bg-emerald-600 text-white shadow-sm" : "text-gray-700 hover:bg-gray-100"
                }`
              }
            >
              <item.icon size={18} />
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 border-b border-gray-200 bg-white/95 px-4 py-3 backdrop-blur lg:px-8">
          <div>
            <h1 className="text-xl font-black tracking-tight text-gray-950">{titles[location.pathname] ?? "Fluxo Pessoal"}</h1>
            <p className="text-sm font-medium text-gray-500">Controle, classificação, conciliação e conferência em um só lugar.</p>
          </div>
          <nav className="mt-3 flex gap-2 overflow-x-auto pb-1 lg:hidden">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `inline-flex min-h-10 shrink-0 items-center gap-2 rounded-xl px-3 py-2 text-sm font-bold ${
                    isActive ? "bg-emerald-600 text-white" : "bg-gray-100 text-gray-700"
                  }`
                }
              >
                <item.icon size={16} />
                {item.label}
              </NavLink>
            ))}
          </nav>
        </header>

        <main className="mx-auto max-w-7xl px-4 py-6 lg:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
