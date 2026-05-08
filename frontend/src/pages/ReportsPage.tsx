import { Download, Edit3, FileText, Plus, Sparkles, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button } from "../components/ui/Button";
import { EmptyState } from "../components/ui/EmptyState";
import { Input } from "../components/ui/Input";
import { Modal } from "../components/ui/Modal";
import { currentMonth, formatValue } from "../services/api";
import { reportIndicatorsService } from "../services/reportIndicatorsService";
import { savedReportsService } from "../services/savedReportsService";
import type { SavedReport, SavedReportPayload } from "../types/savedReport";

const emptyForm: SavedReportPayload = {
  name: "",
  description: "",
  is_default_dashboard: false,
  is_active: true,
  display_order: 100,
  indicators: []
};

export function ReportsPage() {
  const queryClient = useQueryClient();
  const [month, setMonth] = useState(currentMonth());
  const [selectedReportId, setSelectedReportId] = useState<number | null>(null);
  const [editing, setEditing] = useState<SavedReport | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [form, setForm] = useState<SavedReportPayload>(emptyForm);
  const reports = useQuery({ queryKey: ["saved-reports"], queryFn: () => savedReportsService.list() });
  const indicators = useQuery({ queryKey: ["report-indicators"], queryFn: () => reportIndicatorsService.list() });
  const selectedReport = useMemo(
    () => reports.data?.find((report) => report.id === selectedReportId) ?? reports.data?.[0],
    [reports.data, selectedReportId]
  );
  const evaluation = useQuery({
    queryKey: ["saved-report-evaluation", selectedReport?.id, month],
    queryFn: () => savedReportsService.evaluate(selectedReport!.id, month),
    enabled: Boolean(selectedReport?.id)
  });

  useEffect(() => {
    if (!selectedReportId && reports.data?.length) setSelectedReportId(reports.data[0].id);
  }, [reports.data, selectedReportId]);

  const seedMutation = useMutation({
    mutationFn: savedReportsService.seedDefault,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["saved-reports"] })
  });

  const saveMutation = useMutation({
    mutationFn: () => {
      const payload = normalizeReportPayload(form);
      return editing ? savedReportsService.update(editing.id, payload) : savedReportsService.create(payload);
    },
    onSuccess: (report) => {
      setSelectedReportId(report.id);
      setEditing(null);
      setFormOpen(false);
      queryClient.invalidateQueries({ queryKey: ["saved-reports"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-widgets"] });
    }
  });

  const deleteMutation = useMutation({
    mutationFn: savedReportsService.remove,
    onSuccess: () => {
      setSelectedReportId(null);
      queryClient.invalidateQueries({ queryKey: ["saved-reports"] });
    }
  });

  const openForm = (report?: SavedReport) => {
    setEditing(report ?? null);
    setForm(
      report
        ? {
            name: report.name,
            description: report.description ?? "",
            is_default_dashboard: report.is_default_dashboard,
            is_active: report.is_active,
            display_order: report.display_order,
            indicators: report.indicators.map((indicator, position) => ({ indicator_id: indicator.id, position }))
          }
        : {
            ...emptyForm,
            indicators: (indicators.data ?? []).slice(0, 5).map((indicator, position) => ({ indicator_id: indicator.id, position }))
          }
    );
    setFormOpen(true);
  };

  return (
    <div className="grid gap-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <label className="grid gap-1 text-sm font-medium text-gray-700">
          <span>Mes</span>
          <input type="month" value={month} onChange={(event) => setMonth(event.target.value)} className="min-h-10 rounded-lg border border-gray-300 bg-white px-3 py-2" />
        </label>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" icon={<Sparkles size={16} />} onClick={() => seedMutation.mutate()} disabled={seedMutation.isPending}>
            Criar modelos
          </Button>
          <Button icon={<Plus size={16} />} onClick={() => openForm()}>
            Novo relatorio
          </Button>
        </div>
      </div>

      {!reports.data?.length ? (
        <EmptyState
          title="Nenhum relatorio salvo"
          description="Crie modelos iniciais ou monte relatorios com os indicadores que quiser."
          action={<Button icon={<Sparkles size={16} />} onClick={() => seedMutation.mutate()}>Criar modelos</Button>}
        />
      ) : (
        <section className="grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
          <div className="grid gap-3">
            {reports.data.map((report) => (
              <button
                key={report.id}
                type="button"
                className={`rounded-xl border p-4 text-left shadow-sm transition ${selectedReport?.id === report.id ? "border-emerald-300 bg-emerald-50" : "border-gray-200 bg-white hover:bg-gray-50"}`}
                onClick={() => setSelectedReportId(report.id)}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-sm font-black text-gray-950">{report.name}</div>
                    <div className="mt-1 text-sm text-gray-500">{report.description || "Sem descricao."}</div>
                  </div>
                  {report.is_default_dashboard && <span className="rounded-full bg-emerald-600 px-2 py-1 text-xs font-bold text-white">Padrao</span>}
                </div>
                <div className="mt-3 text-xs font-semibold text-gray-500">{report.indicators.length} indicadores</div>
              </button>
            ))}
          </div>

          <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
            {selectedReport ? (
              <>
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2 text-sm font-black text-gray-950">
                      <FileText size={17} />
                      {selectedReport.name}
                    </div>
                    <p className="mt-1 text-sm text-gray-500">{selectedReport.description}</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <a href={savedReportsService.exportExcelUrl(selectedReport.id, month)}>
                      <Button icon={<Download size={16} />}>Baixar Excel</Button>
                    </a>
                    <Button variant="secondary" icon={<Edit3 size={16} />} onClick={() => openForm(selectedReport)}>Editar</Button>
                    <Button
                      variant="danger"
                      icon={<Trash2 size={16} />}
                      onClick={() => {
                        if (confirm("Apagar este relatorio salvo?")) deleteMutation.mutate(selectedReport.id);
                      }}
                    >
                      Apagar
                    </Button>
                  </div>
                </div>

                <div className="mt-5 grid gap-3">
                  {evaluation.data?.indicators.map((indicator) => {
                    const result = Number(indicator.result);
                    const good = indicator.positive_is_good ? result >= 0 : result <= 0;
                    return (
                      <div key={indicator.id} className="rounded-lg border border-gray-200 p-3">
                        <div className="flex items-center justify-between gap-3">
                          <div>
                            <div className="text-sm font-black text-gray-900">{indicator.name}</div>
                            <div className="text-xs font-semibold text-gray-500">{indicator.formula_expression || "Soma/subtracao dos termos"}</div>
                          </div>
                          <div className={`text-right text-lg font-black ${good ? "text-emerald-700" : "text-rose-700"}`}>{formatValue(indicator.result, indicator.result_format)}</div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </>
            ) : (
              <p className="text-sm text-gray-500">Selecione um relatorio.</p>
            )}
          </div>
        </section>
      )}

      {formOpen && (
        <Modal
          title={editing ? "Editar relatorio salvo" : "Novo relatorio salvo"}
          description="Relatorios sao conjuntos salvos de indicadores. O relatorio marcado como padrao fica disponivel para download rapido no Dashboard."
          onClose={() => setFormOpen(false)}
          footer={
            <>
              <Button type="button" variant="secondary" onClick={() => setFormOpen(false)}>Cancelar</Button>
              <Button type="button" icon={<FileText size={16} />} onClick={() => saveMutation.mutate()} disabled={!form.name || !form.indicators.length || saveMutation.isPending}>
                {editing ? "Salvar alteracoes" : "Cadastrar relatorio"}
              </Button>
            </>
          }
        >
          <ReportForm form={form} indicators={indicators.data ?? []} onChange={setForm} />
        </Modal>
      )}
    </div>
  );
}

function ReportForm({
  form,
  indicators,
  onChange
}: {
  form: SavedReportPayload;
  indicators: Awaited<ReturnType<typeof reportIndicatorsService.list>>;
  onChange: (form: SavedReportPayload) => void;
}) {
  const selectedIds = new Set(form.indicators.map((indicator) => indicator.indicator_id));
  return (
    <div className="grid gap-4">
      <div className="grid gap-3 md:grid-cols-2">
        <Input label="Nome" value={form.name} onChange={(event) => onChange({ ...form, name: event.target.value })} />
        <Input label="Ordem" type="number" value={form.display_order} onChange={(event) => onChange({ ...form, display_order: Number(event.target.value) })} />
        <label className="grid gap-1 text-sm font-medium text-gray-700 md:col-span-2">
          <span>Descricao</span>
          <textarea
            className="min-h-20 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
            value={form.description ?? ""}
            onChange={(event) => onChange({ ...form, description: event.target.value })}
          />
        </label>
      </div>
      <div className="grid gap-2 rounded-xl border border-gray-200 bg-gray-50 p-3 md:grid-cols-2">
        <CheckItem label="Relatorio padrao do Dashboard" checked={form.is_default_dashboard} onChange={(checked) => onChange({ ...form, is_default_dashboard: checked })} />
        <CheckItem label="Relatorio ativo" checked={form.is_active} onChange={(checked) => onChange({ ...form, is_active: checked })} />
      </div>
      <div className="grid gap-2">
        <div className="text-sm font-black text-gray-950">Indicadores</div>
        {indicators.map((indicator) => (
          <label key={indicator.id} className="flex items-center justify-between gap-3 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm">
            <span className="font-semibold text-gray-700">{indicator.name}</span>
            <input
              type="checkbox"
              checked={selectedIds.has(indicator.id)}
              onChange={(event) => {
                const checked = event.target.checked;
                const next = checked
                  ? [...form.indicators, { indicator_id: indicator.id, position: form.indicators.length }]
                  : form.indicators.filter((item) => item.indicator_id !== indicator.id).map((item, position) => ({ ...item, position }));
                onChange({ ...form, indicators: next });
              }}
            />
          </label>
        ))}
      </div>
    </div>
  );
}

function CheckItem({ label, checked, onChange }: { label: string; checked: boolean; onChange: (checked: boolean) => void }) {
  return (
    <label className="flex min-h-10 items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-semibold text-gray-700">
      <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} />
      {label}
    </label>
  );
}

function normalizeReportPayload(form: SavedReportPayload): SavedReportPayload {
  return {
    ...form,
    description: form.description?.trim() || null,
    indicators: form.indicators.map((indicator, position) => ({ ...indicator, position }))
  };
}
