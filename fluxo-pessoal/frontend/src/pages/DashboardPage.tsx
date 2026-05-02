import { AlertTriangle, ArrowDownToLine, Calculator, EyeOff, Landmark, Maximize2, Minimize2, PiggyBank, Settings2, WalletCards } from "lucide-react";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button } from "../components/ui/Button";
import { StatCard } from "../components/ui/StatCard";
import { currentMonth, formatValue, money } from "../services/api";
import { accountsService } from "../services/accountsService";
import { balancesService } from "../services/balancesService";
import { dashboardWidgetsService } from "../services/dashboardWidgetsService";
import { savedReportsService } from "../services/savedReportsService";
import type { DashboardWidgetEvaluation } from "../types/dashboardWidget";

export function DashboardPage() {
  const queryClient = useQueryClient();
  const [month, setMonth] = useState(currentMonth());
  const [organizing, setOrganizing] = useState(false);
  const widgets = useQuery({ queryKey: ["dashboard-widgets", month], queryFn: () => dashboardWidgetsService.evaluate(month) });
  const balances = useQuery({ queryKey: ["account-balances"], queryFn: accountsService.balances });
  const consolidated = useQuery({ queryKey: ["consolidated-balance"], queryFn: accountsService.consolidated });
  const snapshots = useQuery({ queryKey: ["snapshots"], queryFn: balancesService.snapshots });

  const updateWidget = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Partial<DashboardWidgetEvaluation> }) => dashboardWidgetsService.update(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["dashboard-widgets"] })
  });

  const seedWidgets = useMutation({
    mutationFn: dashboardWidgetsService.seedDefault,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["dashboard-widgets"] })
  });

  const divergent = snapshots.data?.filter((item) => item.status === "divergent").length ?? 0;
  const reserves = consolidated.data?.reserves ?? [];

  return (
    <div className="grid gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <input
            type="month"
            value={month}
            onChange={(event) => setMonth(event.target.value)}
            className="min-h-10 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium"
          />
          <a href={savedReportsService.defaultExportExcelUrl(month)}>
            <Button variant="secondary" icon={<ArrowDownToLine size={16} />}>Baixar relatorio padrao</Button>
          </a>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" icon={<Settings2 size={16} />} onClick={() => setOrganizing((value) => !value)}>
            {organizing ? "Concluir organizacao" : "Organizar dashboard"}
          </Button>
          {!widgets.data?.length && (
            <Button icon={<Calculator size={16} />} onClick={() => seedWidgets.mutate()} disabled={seedWidgets.isPending}>
              Montar dashboard
            </Button>
          )}
        </div>
      </div>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {widgets.data?.map((widget, index) => (
          <DashboardWidgetCard
            key={widget.id}
            widget={widget}
            organizing={organizing}
            onMove={(direction) => {
              const nextPosition = widget.position + (direction === "up" ? -15 : 15);
              updateWidget.mutate({ id: widget.id, payload: { position: nextPosition } });
            }}
            onResize={(width) => updateWidget.mutate({ id: widget.id, payload: { width } })}
            onHide={() => updateWidget.mutate({ id: widget.id, payload: { is_active: false } })}
            isFirst={index === 0}
          />
        ))}
        {!widgets.data?.length && (
          <div className="rounded-xl border border-dashed border-gray-300 bg-white p-6 text-sm text-gray-500 md:col-span-2 xl:col-span-3">
            O dashboard ainda nao tem widgets. Use "Montar dashboard" para criar uma primeira organizacao com seus indicadores.
          </div>
        )}
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <StatCard label="Total com caixinhas" value={money(consolidated.data?.consolidated_balance)} icon={<WalletCards size={18} />} tone="emerald" />
        <StatCard label="Disponivel em contas" value={money(consolidated.data?.available_balance)} icon={<Landmark size={18} />} tone="sky" />
        <StatCard label="Caixinhas estimadas" value={money(consolidated.data?.reserve_balance)} icon={<PiggyBank size={18} />} tone="violet" />
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <h2 className="text-sm font-black text-gray-900">Saldos por conta</h2>
          <div className="mt-4 grid gap-3">
            {balances.data?.map((account) => (
              <div key={account.id} className="grid gap-2 border-b border-gray-100 pb-3 last:border-0 last:pb-0">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <div className="font-bold text-gray-900">{account.name}</div>
                    <div className="text-sm text-gray-500">{account.institution ?? account.account_type}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs font-semibold text-gray-500">Total</div>
                    <div className="font-black text-gray-950">{money(account.balance_with_reserves)}</div>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs font-semibold text-gray-500">
                  <span>Disponivel: {money(account.calculated_balance)}</span>
                  <span>Caixinhas: {money(account.reserve_balance)}</span>
                </div>
              </div>
            ))}
            {!balances.data?.length && <p className="text-sm text-gray-500">Cadastre uma conta para comecar.</p>}
          </div>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <h2 className="text-sm font-black text-gray-900">Caixinhas detectadas</h2>
          <div className="mt-4 grid gap-3">
            {reserves.map((reserve) => (
              <div key={`${reserve.account_id}-${reserve.name}`} className="flex items-center justify-between gap-3 border-b border-gray-100 pb-3 last:border-0 last:pb-0">
                <div>
                  <div className="font-bold text-gray-900">{reserve.name}</div>
                  <div className="text-xs text-gray-500">Calculada por movimentacoes de reserva/retirada</div>
                </div>
                <div className={`font-black ${Number(reserve.balance) < 0 ? "text-amber-700" : "text-gray-950"}`}>{money(reserve.balance)}</div>
              </div>
            ))}
            {!reserves.length && <p className="text-sm text-gray-500">Nenhuma caixinha detectada nos extratos importados.</p>}
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <StatCard label="Pendencias de classificacao" value={0} icon={<AlertTriangle size={18} />} tone="amber" />
        <StatCard label="Diferencas de conciliacao" value={divergent} icon={<AlertTriangle size={18} />} tone={divergent ? "rose" : "emerald"} />
      </section>
    </div>
  );
}

function DashboardWidgetCard({
  widget,
  organizing,
  onMove,
  onResize,
  onHide,
  isFirst
}: {
  widget: DashboardWidgetEvaluation;
  organizing: boolean;
  onMove: (direction: "up" | "down") => void;
  onResize: (width: number) => void;
  onHide: () => void;
  isFirst: boolean;
}) {
  const indicator = widget.indicator;
  const result = Number(indicator?.result ?? 0);
  const good = indicator ? (indicator.positive_is_good ? result >= 0 : result <= 0) : true;
  const widthClass = widget.width >= 3 ? "xl:col-span-3" : widget.width === 2 ? "xl:col-span-2" : "";

  if (widget.widget_type === "report_download") {
    return (
      <article className={`rounded-xl border border-gray-200 bg-white p-4 shadow-sm ${widthClass}`}>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="text-sm font-black text-gray-950">{widget.title}</div>
            <div className="text-sm text-gray-500">Exportacao rapida do relatorio marcado como padrao.</div>
          </div>
          {widget.export_url && (
            <a href={widget.export_url}>
              <Button icon={<ArrowDownToLine size={16} />}>Baixar Excel</Button>
            </a>
          )}
        </div>
        {organizing && <WidgetControls widget={widget} onMove={onMove} onResize={onResize} onHide={onHide} />}
      </article>
    );
  }

  return (
    <article className={`rounded-xl border border-gray-200 bg-white p-4 shadow-sm ${widthClass}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="truncate text-sm font-black text-gray-950">{widget.title}</div>
          <div className="mt-1 text-xs font-semibold text-gray-500">{indicator?.result_label ?? "Indicador"}</div>
        </div>
        <span className={`grid h-9 w-9 shrink-0 place-items-center rounded-lg ${good ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700"}`}>
          <Calculator size={17} />
        </span>
      </div>
      <div className={`mt-3 ${isFirst ? "text-4xl" : "text-2xl"} font-black ${good ? "text-emerald-700" : "text-rose-700"}`}>
        {formatValue(indicator?.result, indicator?.result_format)}
      </div>
      {indicator?.terms?.length ? (
        <div className="mt-3 grid gap-1">
          {indicator.terms.slice(0, widget.width >= 2 ? 6 : 3).map((term) => (
            <div key={`${widget.id}-${term.chart_account_id}-${term.label}`} className="flex justify-between gap-3 text-xs">
              <span className="truncate font-semibold text-gray-500">{term.label}</span>
              <span className="font-bold text-gray-700">{formatValue(term.contribution, indicator.result_format === "percent" ? "number" : "currency")}</span>
            </div>
          ))}
        </div>
      ) : null}
      {organizing && <WidgetControls widget={widget} onMove={onMove} onResize={onResize} onHide={onHide} />}
    </article>
  );
}

function WidgetControls({
  widget,
  onMove,
  onResize,
  onHide
}: {
  widget: DashboardWidgetEvaluation;
  onMove: (direction: "up" | "down") => void;
  onResize: (width: number) => void;
  onHide: () => void;
}) {
  return (
    <div className="mt-4 flex flex-wrap gap-2 border-t border-gray-100 pt-3">
      <Button type="button" variant="secondary" onClick={() => onMove("up")}>Subir</Button>
      <Button type="button" variant="secondary" onClick={() => onMove("down")}>Descer</Button>
      <Button type="button" variant="ghost" icon={<Minimize2 size={15} />} onClick={() => onResize(Math.max(1, widget.width - 1))}>Menor</Button>
      <Button type="button" variant="ghost" icon={<Maximize2 size={15} />} onClick={() => onResize(Math.min(3, widget.width + 1))}>Maior</Button>
      <Button type="button" variant="ghost" icon={<EyeOff size={15} />} onClick={onHide}>Ocultar</Button>
    </div>
  );
}
