import { Calculator, Divide, Edit3, Eye, EyeOff, FunctionSquare, ListTree, Plus, Sparkles, Trash2 } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button } from "../components/ui/Button";
import { EmptyState } from "../components/ui/EmptyState";
import { Input, Select } from "../components/ui/Input";
import { Modal } from "../components/ui/Modal";
import { PageToolbar } from "../components/ui/PageToolbar";
import { chartAccountsService } from "../services/chartAccountsService";
import { money } from "../services/api";
import { reportIndicatorsService } from "../services/reportIndicatorsService";
import type { ChartAccount } from "../types/chartAccount";
import type { FormulaOperation, FormulaValueMode, ReportIndicator, ReportIndicatorPayload, ReportIndicatorTermPayload } from "../types/reportIndicator";

const emptyForm: ReportIndicatorPayload = {
  name: "",
  description: "",
  result_label: "Resultado",
  result_format: "currency",
  formula_expression: null,
  positive_is_good: true,
  include_internal_transfers: false,
  show_on_dashboard: true,
  show_on_reports: true,
  display_order: 100,
  is_active: true,
  terms: []
};

const operationLabels: Record<FormulaOperation, string> = {
  add: "Somar",
  subtract: "Subtrair",
  multiply: "Multiplicar",
  divide: "Dividir"
};

const formulaExamples = [
  {
    title: "Sobra real",
    expression: "[1 - Receitas] - [2 - Despesas fixas] - [3 - Despesas variaveis] - [4 - Dividas e obrigacoes]"
  },
  {
    title: "% comprometido",
    expression: "pct([2 - Despesas fixas] + [3 - Despesas variaveis] + [4 - Dividas e obrigacoes], [1 - Receitas])"
  },
  {
    title: "Limite de alerta",
    expression: "ifelse([3 - Despesas variaveis] > [1 - Receitas] * 0.35, 1, 0)"
  }
];

const functionHelp = [
  "pct(a,b): transforma a / b em percentual.",
  "safe_div(a,b): divide sem erro quando b for zero.",
  "min/max/abs/round: menor, maior, absoluto e arredondamento.",
  "clamp(valor,min,max): prende um valor dentro de uma faixa.",
  "ifelse(condicao,a,b): retorna a se a condicao for verdadeira, senao b."
];

const valueModeLabels: Record<FormulaValueMode, string> = {
  inflow: "Entradas",
  outflow: "Saídas",
  net: "Saldo líquido",
  absolute: "Valor absoluto"
};

export function ReportIndicatorsPage() {
  const queryClient = useQueryClient();
  const [selected, setSelected] = useState<ReportIndicator | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [form, setForm] = useState<ReportIndicatorPayload>(emptyForm);
  const indicators = useQuery({ queryKey: ["report-indicators"], queryFn: () => reportIndicatorsService.list() });
  const evaluations = useQuery({ queryKey: ["report-indicators-evaluation-preview"], queryFn: () => reportIndicatorsService.evaluate(new Date().toISOString().slice(0, 7)) });
  const chartAccounts = useQuery({ queryKey: ["chart-accounts"], queryFn: () => chartAccountsService.list() });

  useEffect(() => {
    if (!selected) {
      setForm(emptyForm);
      return;
    }
    setForm({
      name: selected.name,
      description: selected.description ?? "",
      result_label: selected.result_label,
      result_format: selected.result_format,
      formula_expression: selected.formula_expression ?? null,
      positive_is_good: selected.positive_is_good,
      include_internal_transfers: selected.include_internal_transfers,
      show_on_dashboard: selected.show_on_dashboard,
      show_on_reports: selected.show_on_reports,
      display_order: selected.display_order,
      is_active: selected.is_active,
      terms: selected.terms.map((term, index) => ({
        chart_account_id: term.chart_account_id,
        operation: term.operation,
        value_mode: term.value_mode,
        variable_key: term.variable_key ?? "",
        weight: term.weight ?? "1",
        probability: term.probability ?? "1",
        include_children: term.include_children,
        label: term.label ?? "",
        position: index
      }))
    });
  }, [selected, formOpen]);

  const saveMutation = useMutation({
    mutationFn: () => {
      const payload = normalizePayload(form);
      return selected ? reportIndicatorsService.update(selected.id, payload) : reportIndicatorsService.create(payload);
    },
    onSuccess: () => {
      setSelected(null);
      setFormOpen(false);
      queryClient.invalidateQueries({ queryKey: ["report-indicators"] });
      queryClient.invalidateQueries({ queryKey: ["report-indicators-evaluation-preview"] });
      queryClient.invalidateQueries({ queryKey: ["report-indicator-evaluations"] });
    }
  });

  const deleteMutation = useMutation({
    mutationFn: reportIndicatorsService.remove,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["report-indicators"] });
      queryClient.invalidateQueries({ queryKey: ["report-indicators-evaluation-preview"] });
      queryClient.invalidateQueries({ queryKey: ["report-indicator-evaluations"] });
    }
  });

  const seedMutation = useMutation({
    mutationFn: reportIndicatorsService.seedDefault,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["report-indicators"] });
      queryClient.invalidateQueries({ queryKey: ["report-indicators-evaluation-preview"] });
    }
  });

  const firstAccountId = chartAccounts.data?.[0]?.id;

  return (
    <div className="grid gap-6">
      <PageToolbar>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="text-sm font-black text-gray-950">Indicadores personalizados</div>
            <div className="text-sm text-gray-500">Monte fórmulas com o plano de contas e escolha o que aparece no Dashboard e nos Relatórios.</div>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" icon={<Sparkles size={16} />} onClick={() => seedMutation.mutate()} disabled={seedMutation.isPending}>
              Criar modelos
            </Button>
            <Button
              icon={<Plus size={16} />}
              onClick={() => {
                setSelected(null);
                setForm({
                  ...emptyForm,
                  terms: firstAccountId ? [newTerm(firstAccountId)] : []
                });
                setFormOpen(true);
              }}
            >
              Novo indicador
            </Button>
          </div>
        </div>
      </PageToolbar>

      {!indicators.data?.length ? (
        <EmptyState
          title="Nenhum indicador criado"
          description="Crie modelos iniciais ou monte uma fórmula própria usando as contas do plano."
          action={<Button icon={<Sparkles size={16} />} onClick={() => seedMutation.mutate()}>Criar modelos</Button>}
        />
      ) : (
        <section className="grid gap-4 xl:grid-cols-3">
          {indicators.data.map((indicator) => {
            const evaluation = evaluations.data?.find((item) => item.id === indicator.id);
            const result = Number(evaluation?.result ?? 0);
            const good = indicator.positive_is_good ? result >= 0 : result <= 0;
            return (
              <article key={indicator.id} className="grid gap-4 rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="truncate text-sm font-black text-gray-950">{indicator.name}</div>
                    <div className="mt-1 line-clamp-2 text-sm text-gray-500">{indicator.description || "Sem descrição."}</div>
                  </div>
                  <span className={`grid h-9 w-9 shrink-0 place-items-center rounded-lg ${good ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700"}`}>
                    <Calculator size={17} />
                  </span>
                </div>

                <div>
                  <div className="text-xs font-bold uppercase text-gray-500">{indicator.result_label}</div>
                  <div className={`mt-1 text-2xl font-black ${good ? "text-emerald-700" : "text-rose-700"}`}>{money(evaluation?.result)}</div>
                </div>

                <div className="grid gap-2">
                  {indicator.terms.map((term) => (
                    <div key={term.id} className="flex items-center justify-between gap-2 rounded-lg bg-gray-50 px-3 py-2 text-xs">
                      <span className="min-w-0 truncate font-semibold text-gray-700">
                        {operationLabels[term.operation]} {term.label || term.chart_account_name}
                      </span>
                      <span className="shrink-0 text-gray-500">{valueModeLabels[term.value_mode]}</span>
                    </div>
                  ))}
                </div>

                <div className="flex flex-wrap items-center justify-between gap-2 border-t border-gray-100 pt-3">
                  <div className="flex gap-2 text-xs font-bold text-gray-500">
                    <span className="inline-flex items-center gap-1">{indicator.show_on_dashboard ? <Eye size={14} /> : <EyeOff size={14} />} Dashboard</span>
                    <span className="inline-flex items-center gap-1">{indicator.show_on_reports ? <Eye size={14} /> : <EyeOff size={14} />} Relatórios</span>
                  </div>
                  <div className="flex gap-1">
                    <Button title="Editar" variant="ghost" icon={<Edit3 size={15} />} onClick={() => { setSelected(indicator); setFormOpen(true); }} />
                    <Button
                      title="Apagar"
                      variant="ghost"
                      icon={<Trash2 size={15} />}
                      onClick={() => {
                        if (confirm("Apagar este indicador personalizado?")) deleteMutation.mutate(indicator.id);
                      }}
                    />
                  </div>
                </div>
              </article>
            );
          })}
        </section>
      )}

      {formOpen && (
        <Modal
          title={selected ? "Editar indicador" : "Novo indicador"}
          description="Cada linha da fórmula usa uma categoria do plano de contas. Você pode somar receita, subtrair gastos, incluir subcontas e controlar onde o resultado aparece."
          onClose={() => {
            setSelected(null);
            setFormOpen(false);
          }}
          footer={
            <>
              <Button type="button" variant="secondary" onClick={() => setFormOpen(false)}>Cancelar</Button>
              <Button type="button" icon={<Calculator size={16} />} onClick={() => saveMutation.mutate()} disabled={!canSave(form) || saveMutation.isPending}>
                {selected ? "Salvar alterações" : "Cadastrar indicador"}
              </Button>
            </>
          }
        >
          <IndicatorForm form={form} chartAccounts={chartAccounts.data ?? []} onChange={setForm} />
        </Modal>
      )}
    </div>
  );
}

function IndicatorForm({
  form,
  chartAccounts,
  onChange
}: {
  form: ReportIndicatorPayload;
  chartAccounts: ChartAccount[];
  onChange: (form: ReportIndicatorPayload) => void;
}) {
  const advancedMode = form.formula_expression !== null;
  const variableOptions = useMemo(() => buildVariableOptions(chartAccounts), [chartAccounts]);
  const addTerm = () => {
    const chartAccountId = chartAccounts[0]?.id;
    if (!chartAccountId) return;
    onChange({ ...form, terms: [...form.terms, newTerm(chartAccountId, form.terms.length)] });
  };
  const switchToManual = () => {
    const firstChartAccountId = chartAccounts[0]?.id;
    onChange({
      ...form,
      formula_expression: null,
      terms: form.terms.length || !firstChartAccountId ? form.terms : [newTerm(firstChartAccountId)]
    });
  };
  const switchToAdvanced = () => {
    onChange({ ...form, formula_expression: form.formula_expression ?? "", terms: [] });
  };

  return (
    <div className="grid gap-5">
      <div className="grid gap-3 md:grid-cols-2">
        <Input label="Nome" value={form.name} onChange={(event) => onChange({ ...form, name: event.target.value })} />
        <Input label="Rótulo do resultado" value={form.result_label} onChange={(event) => onChange({ ...form, result_label: event.target.value })} />
        <Input label="Ordem" type="number" value={form.display_order} onChange={(event) => onChange({ ...form, display_order: Number(event.target.value) })} />
        <Select label="Formato do resultado" value={form.result_format} onChange={(event) => onChange({ ...form, result_format: event.target.value as ReportIndicatorPayload["result_format"] })}>
          <option value="currency">Moeda</option>
          <option value="number">Número</option>
          <option value="percent">Percentual</option>
        </Select>
        <Select label="Resultado positivo significa" value={form.positive_is_good ? "good" : "bad"} onChange={(event) => onChange({ ...form, positive_is_good: event.target.value === "good" })}>
          <option value="good">Bom</option>
          <option value="bad">Atenção</option>
        </Select>
        <label className="grid gap-1 text-sm font-medium text-gray-700 md:col-span-2">
          <span>Descrição</span>
          <textarea
            className="min-h-20 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
            value={form.description ?? ""}
            onChange={(event) => onChange({ ...form, description: event.target.value })}
          />
        </label>
        <div className="grid gap-2 rounded-xl border border-gray-200 bg-gray-50 p-3 md:col-span-2">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="text-sm font-black text-gray-950">Modo de calculo</div>
              <div className="text-xs text-gray-500">Escolha termos manuais ou uma formula avancada. Um modo substitui o outro.</div>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button type="button" variant={!advancedMode ? "primary" : "secondary"} icon={<ListTree size={15} />} onClick={switchToManual}>
                Manual
              </Button>
              <Button type="button" variant={advancedMode ? "primary" : "secondary"} icon={<FunctionSquare size={15} />} onClick={switchToAdvanced}>
                Formula
              </Button>
            </div>
          </div>
        </div>
        {advancedMode && (
        <label className="grid gap-1 text-sm font-medium text-gray-700 md:col-span-2">
          <span>Expressão avançada</span>
          <FormulaExpressionEditor
            value={form.formula_expression ?? ""}
            options={variableOptions}
            onChange={(formulaExpression) => onChange({ ...form, formula_expression: formulaExpression, terms: [] })}
          />
          <span className="text-xs text-gray-500">Use chaves dos termos, variaveis do plano como c_1 ou referencias entre colchetes como [1 - Receitas]. Funcoes: pct(a,b), safe_div(a,b), min, max, abs, round, clamp, ifelse.</span>
        </label>
        )}
      </div>

      <div className="rounded-xl border border-sky-200 bg-sky-50 p-3">
        <div className="text-sm font-black text-sky-950">Variaveis automaticas do plano</div>
        <div className="mt-2 grid gap-2 text-xs font-semibold text-sky-900 md:grid-cols-2">
          {chartAccounts.slice(0, 10).map((account) => (
            <div key={account.id} className="rounded-lg bg-white px-3 py-2">
              <span className="font-mono">{accountFormulaVariable(account)}</span>
              <span className="text-sky-700"> ou [{account.code} - {account.name}]</span>
            </div>
          ))}
        </div>
        <div className="mt-2 text-xs text-sky-800">
          Cada variavel soma a conta e seus filhos no periodo filtrado. Prefixos disponiveis: entrada_, saida_, liquido_ e abs_.
        </div>
      </div>

      {advancedMode && (
        <div className="grid gap-3 lg:grid-cols-[1fr_1.1fr]">
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-3">
            <div className="text-sm font-black text-emerald-950">Funcoes disponiveis</div>
            <div className="mt-2 grid gap-2">
              {functionHelp.map((item) => (
                <div key={item} className="rounded-lg bg-white px-3 py-2 text-xs font-semibold text-emerald-900">{item}</div>
              ))}
            </div>
          </div>
          <div className="rounded-xl border border-gray-200 bg-white p-3">
            <div className="text-sm font-black text-gray-950">Exemplos de formulas</div>
            <div className="mt-2 grid gap-2">
              {formulaExamples.map((example) => (
                <button
                  key={example.title}
                  type="button"
                  className="grid gap-1 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-left transition hover:border-emerald-300 hover:bg-emerald-50"
                  onClick={() => onChange({ ...form, formula_expression: example.expression, terms: [] })}
                >
                  <span className="text-xs font-black text-gray-950">{example.title}</span>
                  <span className="font-mono text-xs text-gray-600">{example.expression}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="grid gap-2 rounded-xl border border-gray-200 bg-gray-50 p-3 md:grid-cols-2">
        <CheckItem label="Mostrar no Dashboard" checked={form.show_on_dashboard} onChange={(checked) => onChange({ ...form, show_on_dashboard: checked })} />
        <CheckItem label="Mostrar em Relatórios" checked={form.show_on_reports} onChange={(checked) => onChange({ ...form, show_on_reports: checked })} />
        <CheckItem label="Incluir transferências internas" checked={form.include_internal_transfers} onChange={(checked) => onChange({ ...form, include_internal_transfers: checked })} />
        <CheckItem label="Indicador ativo" checked={form.is_active} onChange={(checked) => onChange({ ...form, is_active: checked })} />
      </div>

      {!advancedMode && (
      <div className="grid gap-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <div className="text-sm font-black text-gray-950">Fórmula</div>
            <div className="text-xs text-gray-500">Exemplo: somar Receita e subtrair Fixas, Variáveis e Obrigações.</div>
          </div>
          <Button type="button" variant="secondary" icon={<Plus size={15} />} onClick={addTerm} disabled={!chartAccounts.length}>
            Adicionar termo
          </Button>
        </div>

        {form.terms.map((term, index) => (
          <FormulaTermEditor
            key={index}
            term={term}
            index={index}
            chartAccounts={chartAccounts}
            onChange={(nextTerm) => {
              const terms = [...form.terms];
              terms[index] = { ...nextTerm, position: index };
              onChange({ ...form, terms });
            }}
            onRemove={() => onChange({ ...form, terms: form.terms.filter((_, termIndex) => termIndex !== index).map((item, position) => ({ ...item, position })) })}
          />
        ))}
      </div>
      )}
    </div>
  );
}

function FormulaTermEditor({
  term,
  index,
  chartAccounts,
  onChange,
  onRemove
}: {
  term: ReportIndicatorTermPayload;
  index: number;
  chartAccounts: ChartAccount[];
  onChange: (term: ReportIndicatorTermPayload) => void;
  onRemove: () => void;
}) {
  return (
    <div className="grid gap-3 rounded-xl border border-gray-200 bg-white p-3">
      <div className="flex items-center justify-between gap-3">
        <div className="text-xs font-black uppercase text-gray-500">Termo {index + 1}</div>
        <Button type="button" title="Remover termo" variant="ghost" icon={<Trash2 size={15} />} onClick={onRemove} />
      </div>
      <div className="grid gap-3 md:grid-cols-[0.8fr_1fr_1fr]">
        <Select label="Operação" value={term.operation} onChange={(event) => onChange({ ...term, operation: event.target.value as FormulaOperation })}>
          <option value="add">Somar</option>
          <option value="subtract">Subtrair</option>
          <option value="multiply">Multiplicar</option>
          <option value="divide">Dividir</option>
        </Select>
        <Select label="Plano de contas" value={term.chart_account_id} onChange={(event) => onChange({ ...term, chart_account_id: Number(event.target.value) })}>
          {chartAccounts.map((account) => <option key={account.id} value={account.id}>{account.code} - {account.name}</option>)}
        </Select>
        <Select label="Valor usado" value={term.value_mode} onChange={(event) => onChange({ ...term, value_mode: event.target.value as FormulaValueMode })}>
          <option value="inflow">Entradas</option>
          <option value="outflow">Saídas</option>
          <option value="net">Saldo líquido</option>
          <option value="absolute">Valor absoluto</option>
        </Select>
      </div>
      <div className="grid gap-3 md:grid-cols-[1fr_0.8fr_0.7fr_0.7fr]">
        <Input label="Apelido na fórmula" value={term.label ?? ""} onChange={(event) => onChange({ ...term, label: event.target.value })} />
        <Input label="Chave" value={term.variable_key ?? ""} onChange={(event) => onChange({ ...term, variable_key: event.target.value })} placeholder="receita" />
        <Input label="Peso" type="number" step="0.01" value={term.weight} onChange={(event) => onChange({ ...term, weight: event.target.value })} />
        <Input label="Probabilidade" type="number" step="0.01" min="0" max="1" value={term.probability} onChange={(event) => onChange({ ...term, probability: event.target.value })} />
        <CheckItem label="Incluir subcontas" checked={term.include_children} onChange={(checked) => onChange({ ...term, include_children: checked })} />
      </div>
    </div>
  );
}

type FormulaVariableOption = {
  insert: string;
  label: string;
  detail: string;
  search: string;
};

function FormulaExpressionEditor({
  value,
  options,
  onChange
}: {
  value: string;
  options: FormulaVariableOption[];
  onChange: (value: string) => void;
}) {
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const [cursor, setCursor] = useState(value.length);
  const slashQuery = slashSearch(value, cursor);
  const filteredOptions = slashQuery === null
    ? []
    : options
      .filter((option) => option.search.includes(normalizeSearch(slashQuery)))
      .slice(0, 8);

  const selectOption = (option: FormulaVariableOption) => {
    const slashIndex = value.lastIndexOf("/", cursor - 1);
    const nextValue = `${value.slice(0, slashIndex)}${option.insert}${value.slice(cursor)}`;
    const nextCursor = slashIndex + option.insert.length;
    onChange(nextValue);
    setCursor(nextCursor);
    setTimeout(() => {
      textareaRef.current?.focus();
      textareaRef.current?.setSelectionRange(nextCursor, nextCursor);
    }, 0);
  };

  return (
    <span className="relative grid gap-2">
      <textarea
        ref={textareaRef}
        className="min-h-24 rounded-lg border border-gray-300 bg-white px-3 py-2 font-mono text-sm text-gray-900 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
        placeholder="Digite / para buscar uma classificacao. Ex.: pct(/1, /2)"
        value={value}
        onChange={(event) => {
          onChange(event.target.value);
          setCursor(event.target.selectionStart ?? event.target.value.length);
        }}
        onClick={(event) => setCursor(event.currentTarget.selectionStart ?? value.length)}
        onKeyUp={(event) => setCursor(event.currentTarget.selectionStart ?? value.length)}
        onKeyDown={(event) => {
          if ((event.key === "Enter" || event.key === "Tab") && filteredOptions[0]) {
            event.preventDefault();
            selectOption(filteredOptions[0]);
          }
          if (event.key === "Escape") {
            setCursor(0);
          }
        }}
      />
      {slashQuery !== null && (
        <div className="absolute left-0 right-0 top-full z-20 mt-1 overflow-hidden rounded-xl border border-gray-200 bg-white shadow-lg">
          {filteredOptions.length ? filteredOptions.map((option) => (
            <button
              key={option.insert}
              type="button"
              className="flex w-full items-center justify-between gap-3 px-3 py-2 text-left text-sm hover:bg-emerald-50"
              onMouseDown={(event) => {
                event.preventDefault();
                selectOption(option);
              }}
            >
              <span className="min-w-0">
                <span className="block truncate font-bold text-gray-900">{option.label}</span>
                <span className="block truncate text-xs text-gray-500">{option.detail}</span>
              </span>
              <Divide size={15} className="shrink-0 text-emerald-600" />
            </button>
          )) : (
            <div className="px-3 py-2 text-sm font-semibold text-gray-500">Nenhuma variavel encontrada.</div>
          )}
        </div>
      )}
    </span>
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

function newTerm(chartAccountId: number, position = 0): ReportIndicatorTermPayload {
  return {
    chart_account_id: chartAccountId,
    operation: "add",
    value_mode: "outflow",
    variable_key: "",
    weight: "1",
    probability: "1",
    include_children: true,
    label: "",
    position
  };
}

function accountFormulaVariable(account: ChartAccount): string {
  return `c_${account.code.replace(/\./g, "_")}`;
}

function buildVariableOptions(accounts: ChartAccount[]): FormulaVariableOption[] {
  return accounts.map((account) => {
    const variable = accountFormulaVariable(account);
    const bracket = `[${account.code} - ${account.name}]`;
    return {
      insert: bracket,
      label: `${account.code} - ${account.name}`,
      detail: `${variable} soma a classificacao e os filhos`,
      search: normalizeSearch(`${account.code} ${account.name} ${variable} ${bracket}`)
    };
  });
}

function slashSearch(value: string, cursor: number): string | null {
  const slashIndex = value.lastIndexOf("/", cursor - 1);
  if (slashIndex < 0) return null;
  const fragment = value.slice(slashIndex + 1, cursor);
  if (/[\n()[\],+\-*]/.test(fragment)) return null;
  return fragment;
}

function normalizeSearch(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

function normalizePayload(form: ReportIndicatorPayload): ReportIndicatorPayload {
  const formulaExpression = form.formula_expression?.trim() || null;
  return {
    ...form,
    description: form.description?.trim() || null,
    formula_expression: formulaExpression,
    terms: formulaExpression ? [] : form.terms.map((term, position) => ({
      ...term,
      label: term.label?.trim() || null,
      variable_key: term.variable_key?.trim() || null,
      weight: term.weight || "1",
      probability: term.probability || "1",
      position
    }))
  };
}

function canSave(form: ReportIndicatorPayload) {
  const hasFormula = Boolean(form.formula_expression?.trim());
  const hasTerms = form.terms.length > 0 && form.terms.every((term) => term.chart_account_id);
  return Boolean(form.name.trim() && form.result_label.trim() && (hasFormula || hasTerms));
}
