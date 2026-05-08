import { Edit3, PlayCircle, Plus, Power, Search, Trash2 } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Input, Select } from "../components/ui/Input";
import { Modal } from "../components/ui/Modal";
import { PageToolbar } from "../components/ui/PageToolbar";
import { chartAccountsService } from "../services/chartAccountsService";
import { classificationRulesService, type ClassificationRulePayload } from "../services/classificationRulesService";
import type { ClassificationRule } from "../types/classificationRule";
import type { TransactionType } from "../types/transaction";

const emptyForm: ClassificationRulePayload = {
  keyword: "",
  match_type: "contains",
  chart_account_id: 0,
  transaction_type: "expense",
  priority: 100,
  active: true
};

export function ClassificationRulesPage() {
  const queryClient = useQueryClient();
  const [formOpen, setFormOpen] = useState(false);
  const [selected, setSelected] = useState<ClassificationRule | null>(null);
  const [form, setForm] = useState<ClassificationRulePayload>(emptyForm);

  const [search, setSearch] = useState("");
  const [filterType, setFilterType] = useState("");
  const [filterStatus, setFilterStatus] = useState("");

  const rules = useQuery({ queryKey: ["classification-rules"], queryFn: classificationRulesService.list });
  const chartAccounts = useQuery({ queryKey: ["chart-accounts"], queryFn: () => chartAccountsService.list() });

  useEffect(() => {
    setForm(
      selected
        ? {
            keyword: selected.keyword,
            match_type: selected.match_type,
            chart_account_id: selected.chart_account_id,
            transaction_type: selected.transaction_type,
            priority: selected.priority,
            active: selected.active
          }
        : emptyForm
    );
  }, [selected, formOpen]);

  const filteredRules = useMemo(() => {
    const accounts = chartAccounts.data ?? [];
    return (rules.data ?? []).filter((rule) => {
      const chart = accounts.find((a) => a.id === rule.chart_account_id);
      const categoryLabel = chart ? `${chart.code} ${chart.name}`.toLowerCase() : "";
      const q = search.toLowerCase();
      const matchesSearch =
        !q ||
        rule.keyword.toLowerCase().includes(q) ||
        categoryLabel.includes(q) ||
        rule.match_type.toLowerCase().includes(q);
      const matchesType = !filterType || rule.transaction_type === filterType;
      const matchesStatus =
        !filterStatus ||
        (filterStatus === "active" ? rule.active : !rule.active);
      return matchesSearch && matchesType && matchesStatus;
    });
  }, [rules.data, chartAccounts.data, search, filterType, filterStatus]);

  const saveMutation = useMutation({
    mutationFn: () => (selected ? classificationRulesService.update(selected.id, form) : classificationRulesService.create(form)),
    onSuccess: () => {
      setSelected(null);
      setFormOpen(false);
      queryClient.invalidateQueries({ queryKey: ["classification-rules"] });
      queryClient.invalidateQueries({ queryKey: ["pending-transactions"] });
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
    }
  });

  const deactivateMutation = useMutation({
    mutationFn: classificationRulesService.deactivate,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["classification-rules"] })
  });

  const removeMutation = useMutation({
    mutationFn: classificationRulesService.remove,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["classification-rules"] })
  });

  const applyMutation = useMutation({
    mutationFn: classificationRulesService.applyToPending,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["classification-rules"] });
      queryClient.invalidateQueries({ queryKey: ["pending-transactions"] });
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
    }
  });

  return (
    <div className="grid gap-6">
      <PageToolbar>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="text-sm font-black text-gray-950">Regras automáticas</div>
            <div className="text-sm text-gray-500">Crie, edite, desative e reaplique regras sobre movimentações pendentes.</div>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" icon={<PlayCircle size={16} />} onClick={() => applyMutation.mutate()}>
              Aplicar pendentes
            </Button>
            <Button
              icon={<Plus size={16} />}
              onClick={() => {
                setSelected(null);
                setFormOpen(true);
              }}
            >
              Nova regra
            </Button>
          </div>
        </div>
      </PageToolbar>

      {applyMutation.data && (
        <div className="rounded-xl border border-sky-200 bg-sky-50 p-3 text-sm font-bold text-sky-900">
          Atualizadas: {applyMutation.data.updated}. Pendentes restantes: {applyMutation.data.remaining_pending}.
        </div>
      )}

      {/* Filtros */}
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-48">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
          <input
            type="text"
            placeholder="Buscar por palavra-chave ou categoria..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-gray-200 bg-white py-2 pl-9 pr-3 text-sm text-gray-800 placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="">Todos os tipos</option>
          <option value="income">Receita</option>
          <option value="expense">Despesa</option>
          <option value="transfer">Transferência</option>
          <option value="reserve">Reserva</option>
          <option value="adjustment">Ajuste</option>
          <option value="credit_card_payment">Pagamento cartão</option>
        </select>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="">Todos os status</option>
          <option value="active">Ativas</option>
          <option value="inactive">Inativas</option>
        </select>
      </div>

      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-100 text-left text-xs font-bold uppercase text-gray-600">
              <tr>
                <th className="px-3 py-3">Regra</th>
                <th className="px-3 py-3">Match</th>
                <th className="px-3 py-3">Categoria</th>
                <th className="px-3 py-3">Tipo</th>
                <th className="px-3 py-3">Prioridade</th>
                <th className="px-3 py-3">Status</th>
                <th className="px-3 py-3 text-right">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filteredRules.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-3 py-6 text-center text-sm text-gray-400">
                    Nenhuma regra encontrada.
                  </td>
                </tr>
              )}
              {filteredRules.map((rule) => {
                const chart = chartAccounts.data?.find((item) => item.id === rule.chart_account_id);
                return (
                  <tr key={rule.id} className="hover:bg-gray-50">
                    <td className="px-3 py-3 font-bold">{rule.keyword}</td>
                    <td className="px-3 py-3">{rule.match_type}</td>
                    <td className="px-3 py-3">{chart ? `${chart.code} - ${chart.name}` : rule.chart_account_id}</td>
                    <td className="px-3 py-3">{rule.transaction_type}</td>
                    <td className="px-3 py-3">{rule.priority}</td>
                    <td className="px-3 py-3">
                      <Badge value={rule.active ? "ativa" : "inativa"} />
                    </td>
                    <td className="px-3 py-3 text-right">
                      <div className="flex justify-end gap-2">
                        <Button
                          title="Editar"
                          variant="secondary"
                          icon={<Edit3 size={16} />}
                          onClick={() => {
                            setSelected(rule);
                            setFormOpen(true);
                          }}
                        />
                        <Button title="Desativar" variant="ghost" icon={<Power size={16} />} onClick={() => deactivateMutation.mutate(rule.id)} />
                        <Button
                          title="Apagar"
                          variant="ghost"
                          icon={<Trash2 size={16} />}
                          onClick={() => {
                            if (confirm(`Apagar a regra "${rule.keyword}" permanentemente?`)) {
                              removeMutation.mutate(rule.id);
                            }
                          }}
                        />
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {formOpen && (
        <Modal
          title={selected ? "Editar regra" : "Nova regra"}
          description="Regras com prioridade menor são testadas primeiro."
          onClose={() => {
            setSelected(null);
            setFormOpen(false);
          }}
          footer={
            <>
              <Button type="button" variant="secondary" onClick={() => setFormOpen(false)}>Cancelar</Button>
              <Button type="button" onClick={() => form.chart_account_id && saveMutation.mutate()}>{selected ? "Salvar alterações" : "Criar regra"}</Button>
            </>
          }
        >
          <RuleForm form={form} onChange={setForm} chartAccounts={chartAccounts.data ?? []} />
        </Modal>
      )}
    </div>
  );
}

function RuleForm({
  form,
  onChange,
  chartAccounts
}: {
  form: ClassificationRulePayload;
  onChange: (form: ClassificationRulePayload) => void;
  chartAccounts: Awaited<ReturnType<typeof chartAccountsService.list>>;
}) {
  return (
    <div className="grid gap-3 md:grid-cols-2">
      <Input label="Palavra-chave" value={form.keyword} onChange={(event) => onChange({ ...form, keyword: event.target.value })} required />
      <Select label="Match" value={form.match_type} onChange={(event) => onChange({ ...form, match_type: event.target.value })}>
        <option value="contains">Contém</option>
        <option value="equals">Igual</option>
        <option value="starts_with">Começa com</option>
        <option value="regex">Regex</option>
      </Select>
      <div className="md:col-span-2">
        <CategoryCombobox
          chartAccounts={chartAccounts}
          value={form.chart_account_id}
          onChange={(id) => onChange({ ...form, chart_account_id: id })}
        />
      </div>
      <Select label="Tipo" value={form.transaction_type} onChange={(event) => onChange({ ...form, transaction_type: event.target.value as TransactionType })}>
        <option value="income">Receita</option>
        <option value="expense">Despesa</option>
        <option value="transfer">Transferência</option>
        <option value="reserve">Reserva</option>
        <option value="adjustment">Ajuste</option>
        <option value="credit_card_payment">Pagamento cartão</option>
      </Select>
      <Input label="Prioridade" type="number" value={form.priority} onChange={(event) => onChange({ ...form, priority: Number(event.target.value) })} />
      <label className="flex items-center gap-2 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-semibold text-gray-700">
        <input type="checkbox" checked={form.active} onChange={(event) => onChange({ ...form, active: event.target.checked })} />
        Regra ativa
      </label>
    </div>
  );
}

function CategoryCombobox({
  chartAccounts,
  value,
  onChange
}: {
  chartAccounts: Awaited<ReturnType<typeof chartAccountsService.list>>;
  value: number;
  onChange: (id: number) => void;
}) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const selected = chartAccounts.find((a) => a.id === value);

  const filtered = useMemo(() => {
    const q = query.toLowerCase();
    if (!q) return chartAccounts;
    return chartAccounts.filter(
      (a) => a.code.toLowerCase().includes(q) || a.name.toLowerCase().includes(q)
    );
  }, [chartAccounts, query]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
        setQuery("");
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div ref={containerRef} className="relative">
      <label className="mb-1 block text-xs font-semibold text-gray-600">Categoria</label>
      <input
        type="text"
        placeholder={selected ? `${selected.code} - ${selected.name}` : "Buscar categoria..."}
        value={open ? query : selected ? `${selected.code} - ${selected.name}` : ""}
        onFocus={() => { setOpen(true); setQuery(""); }}
        onChange={(e) => setQuery(e.target.value)}
        className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-800 placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
      />
      {open && (
        <ul className="absolute z-50 mt-1 max-h-56 w-full overflow-auto rounded-lg border border-gray-200 bg-white shadow-lg text-sm">
          {filtered.length === 0 && (
            <li className="px-3 py-2 text-gray-400">Nenhuma categoria encontrada.</li>
          )}
          {filtered.map((a) => (
            <li
              key={a.id}
              onMouseDown={() => {
                onChange(a.id);
                setOpen(false);
                setQuery("");
              }}
              className={`cursor-pointer px-3 py-2 hover:bg-blue-50 ${a.id === value ? "bg-blue-50 font-semibold text-blue-700" : "text-gray-700"}`}
            >
              {a.code} - {a.name}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
