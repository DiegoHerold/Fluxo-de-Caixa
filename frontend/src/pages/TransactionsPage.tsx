import { Plus, RotateCcw, Search, Trash2, X } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { TransactionsTable } from "../components/tables/TransactionsTable";
import { Button } from "../components/ui/Button";
import { Input, Select } from "../components/ui/Input";
import { Modal } from "../components/ui/Modal";
import { PageToolbar } from "../components/ui/PageToolbar";
import { currentMonth, money, todayISODate } from "../services/api";
import { accountsService } from "../services/accountsService";
import { chartAccountsService } from "../services/chartAccountsService";
import { transactionsService, type ManualTransactionPayload, type TransactionFilters, type TransactionSplitPartPayload } from "../services/transactionsService";
import type { ClassificationStatus, Transaction, TransactionSource, TransactionType } from "../types/transaction";

const emptyManual: ManualTransactionPayload = {
  account_id: 0,
  chart_account_id: null,
  reserve_box_id: null,
  transaction_date: todayISODate(),
  description_original: "",
  amount: "0.00",
  transaction_type: "expense",
  is_internal_transfer: false,
  notes: ""
};

function transactionToForm(transaction: Transaction): ManualTransactionPayload {
  return {
    account_id: transaction.account_id,
    chart_account_id: transaction.chart_account_id,
    reserve_box_id: transaction.reserve_box_id,
    transaction_date: transaction.transaction_date,
    description_original: transaction.description_original,
    amount: transaction.amount,
    transaction_type: transaction.transaction_type,
    direction: transaction.direction,
    notes: transaction.notes ?? "",
    is_internal_transfer: transaction.is_internal_transfer
  };
}

export function TransactionsPage() {
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState<TransactionFilters>({});
  const [formOpen, setFormOpen] = useState(false);
  const [selected, setSelected] = useState<Transaction | null>(null);
  const [manual, setManual] = useState<ManualTransactionPayload>(emptyManual);
  const [saveRule, setSaveRule] = useState(false);
  const [ruleKeyword, setRuleKeyword] = useState("");
  const [splitTarget, setSplitTarget] = useState<Transaction | null>(null);
  const [splitParts, setSplitParts] = useState<TransactionSplitPartPayload[]>([]);

  const accounts = useQuery({ queryKey: ["accounts"], queryFn: accountsService.list });
  const chartAccounts = useQuery({ queryKey: ["chart-accounts"], queryFn: () => chartAccountsService.list() });
  const transactions = useQuery({ queryKey: ["transactions", filters], queryFn: () => transactionsService.list(filters) });
  const activeFilters = useMemo(
    () => buildActiveFilterLabels(filters, accounts.data ?? [], chartAccounts.data ?? []),
    [filters, accounts.data, chartAccounts.data]
  );
  const splitDifferenceCents = splitTarget ? splitPartsTotalCents(splitParts) - toCents(splitTarget.amount) : 0;
  const canSaveSplit =
    Boolean(splitTarget) &&
    splitParts.length >= 2 &&
    splitDifferenceCents === 0 &&
    splitParts.every((part) => part.amount !== "" && toCents(part.amount) !== 0);

  function invalidateFinancialData() {
    queryClient.invalidateQueries({ queryKey: ["transactions"] });
    queryClient.invalidateQueries({ queryKey: ["pending-transactions"] });
    queryClient.invalidateQueries({ queryKey: ["account-balances"] });
    queryClient.invalidateQueries({ queryKey: ["classification-rules"] });
    queryClient.invalidateQueries({ queryKey: ["consolidated-balance"] });
    queryClient.invalidateQueries({ queryKey: ["reserves"] });
    queryClient.invalidateQueries({ queryKey: ["loan-people"] });
    queryClient.invalidateQueries({ queryKey: ["loan-movements"] });
  }

  function setFilter<K extends keyof TransactionFilters>(key: K, value: TransactionFilters[K] | undefined) {
    setFilters((current) => ({ ...current, [key]: value || undefined }));
  }

  function removeFilter(key: keyof TransactionFilters) {
    setFilters((current) => ({ ...current, [key]: undefined }));
  }

  useEffect(() => {
    setManual(selected ? transactionToForm(selected) : emptyManual);
    setSaveRule(false);
    setRuleKeyword("");
  }, [selected, formOpen]);

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (!selected) {
        return transactionsService.createManual(manual);
      }
      const updated = await transactionsService.update(selected.id, manual);
      if (saveRule && manual.chart_account_id && manual.transaction_type) {
        return transactionsService.classify(selected.id, {
          chart_account_id: manual.chart_account_id,
          transaction_type: manual.transaction_type,
          is_internal_transfer: manual.is_internal_transfer,
          reserve_box_id: manual.reserve_box_id ?? null,
          notes: manual.notes,
          create_rule: true,
          rule_keyword: ruleKeyword || null,
          rule_match_type: ruleKeyword ? "contains" : "equals",
          rule_priority: ruleKeyword ? 50 : 10
        });
      }
      return updated;
    },
    onSuccess: () => {
      setSelected(null);
      setFormOpen(false);
      invalidateFinancialData();
    }
  });

  const splitMutation = useMutation({
    mutationFn: () => {
      if (!splitTarget) throw new Error("Nenhuma movimentacao selecionada");
      return transactionsService.split(splitTarget.id, splitParts);
    },
    onSuccess: () => {
      setSplitTarget(null);
      setSplitParts([]);
      invalidateFinancialData();
    }
  });

  const deleteMutation = useMutation({
    mutationFn: transactionsService.remove,
    onSuccess: () => {
      invalidateFinancialData();
    }
  });

  return (
    <div className="grid gap-6">
      <PageToolbar>
        <div className="grid gap-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="text-sm font-black text-gray-950">Movimentações</div>
              <div className="text-sm text-gray-500">Filtre, edite, exclua ou lance movimentações manuais.</div>
            </div>
            <Button
              icon={<Plus size={16} />}
              onClick={() => {
                setSelected(null);
                setFormOpen(true);
              }}
            >
              Lançamento manual
            </Button>
          </div>

          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-[1.5fr_0.9fr_0.9fr_1fr_1fr]">
            <label className="grid gap-1 text-sm font-medium text-gray-700 md:col-span-2 xl:col-span-1">
              <span>Pesquisar</span>
              <span className="relative">
                <Search size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  className="min-h-10 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 pl-9 text-sm text-gray-900 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
                  value={filters.search ?? ""}
                  onChange={(event) => setFilter("search", event.target.value || undefined)}
                  placeholder="Descricao, observacao..."
                />
                {filters.search && (
                  <button
                    type="button"
                    className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-700"
                    onClick={() => removeFilter("search")}
                  >
                    <X size={14} />
                  </button>
                )}
              </span>
            </label>
            <Input label="Inicio" type="date" value={filters.start_date ?? ""} onChange={(event) => setFilter("start_date", event.target.value || undefined)} />
            <Input label="Fim" type="date" value={filters.end_date ?? ""} onChange={(event) => setFilter("end_date", event.target.value || undefined)} />
            <Select label="Conta" value={filters.account_id ?? ""} onChange={(event) => setFilter("account_id", event.target.value ? Number(event.target.value) : undefined)}>
              <option value="">Todas</option>
              {accounts.data?.map((account) => <option key={account.id} value={account.id}>{account.name}</option>)}
            </Select>
            <ChartAccountFilterCombobox
              chartAccounts={chartAccounts.data ?? []}
              value={filters.chart_account_id}
              disabled={Boolean(filters.uncategorized)}
              onChange={(chartAccountId) => setFilters((current) => ({ ...current, chart_account_id: chartAccountId, uncategorized: undefined }))}
            />
            <Select label="Tipo" value={filters.transaction_type ?? ""} onChange={(event) => setFilter("transaction_type", (event.target.value || undefined) as TransactionType | undefined)}>
              <option value="">Todos</option>
              <option value="income">Receita</option>
              <option value="expense">Despesa</option>
              <option value="transfer">Transferência</option>
              <option value="reserve">Reserva</option>
              <option value="adjustment">Ajuste</option>
              <option value="credit_card_payment">Pagamento cartão</option>
            </Select>
            <Select label="Status" value={filters.status ?? ""} onChange={(event) => setFilter("status", (event.target.value || undefined) as ClassificationStatus | undefined)}>
              <option value="">Todos</option>
              <option value="pending">Pendente</option>
              <option value="automatic">Automático</option>
              <option value="manual">Manual</option>
              <option value="reviewed">Revisado</option>
            </Select>
            <Select label="Origem" value={filters.source ?? ""} onChange={(event) => setFilter("source", (event.target.value || undefined) as TransactionSource | undefined)}>
              <option value="">Todas</option>
              <option value="manual">Manual</option>
              <option value="nubank_csv">Nubank CSV</option>
              <option value="nubank_ofx">Nubank OFX</option>
              <option value="mercado_pago_xlsx">Mercado Pago</option>
            </Select>
          </div>

          <div className="flex flex-wrap gap-2">
            <Button type="button" variant="secondary" onClick={() => setFilters({ ...filters, ...monthFilter(currentMonth()) })}>
              Mes atual
            </Button>
            <Button type="button" variant="secondary" onClick={() => setFilters({ ...filters, ...lastDaysFilter(90) })}>
              90 dias
            </Button>
            <Button type="button" variant="secondary" onClick={() => setFilters({ ...filters, status: "pending" })}>
              Pendentes
            </Button>
            <Button type="button" variant="secondary" onClick={() => setFilters({ ...filters, transaction_type: "income" })}>
              Entradas
            </Button>
            <Button type="button" variant="secondary" onClick={() => setFilters({ ...filters, transaction_type: "expense" })}>
              Saidas
            </Button>
            <Button type="button" variant="secondary" onClick={() => setFilters({ ...filters, chart_account_id: undefined, uncategorized: true })}>
              Sem categoria
            </Button>
            <Button variant="ghost" icon={<RotateCcw size={16} />} onClick={() => setFilters({})}>
              Limpar
            </Button>
          </div>

          {activeFilters.length > 0 && (
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-bold uppercase text-gray-500">{activeFilters.length} filtro(s)</span>
              {activeFilters.map((filter) => (
                <button
                  key={filter.key}
                  type="button"
                  className="inline-flex items-center gap-1 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-900"
                  onClick={() => removeFilter(filter.key)}
                >
                  {filter.label}
                  <X size={13} />
                </button>
              ))}
            </div>
          )}
        </div>
      </PageToolbar>

      <TransactionsTable
        transactions={transactions.data ?? []}
        onEdit={(transaction) => {
          setSelected(transaction);
          setFormOpen(true);
        }}
        onSplit={(transaction) => {
          setSplitTarget(transaction);
          setSplitParts(buildInitialSplitParts(transaction));
        }}
        onDelete={(id) => {
          if (confirm("Excluir esta movimentação? O saldo será recalculado.")) {
            deleteMutation.mutate(id);
          }
        }}
      />

      {formOpen && (
        <Modal
          title={selected ? "Editar movimentação" : "Lançamento manual"}
          description={selected ? "Altere dados, categoria, tipo ou observações da movimentação." : "Crie uma movimentação fora da importação de extratos."}
          onClose={() => {
            setSelected(null);
            setFormOpen(false);
          }}
          footer={
            <>
              <Button type="button" variant="secondary" onClick={() => setFormOpen(false)}>Cancelar</Button>
              <Button type="button" onClick={() => manual.account_id && saveMutation.mutate()}>{selected ? "Salvar alterações" : "Lançar"}</Button>
            </>
          }
        >
          <TransactionForm
            value={manual}
            onChange={setManual}
            accounts={accounts.data ?? []}
            chartAccounts={chartAccounts.data ?? []}
            selected={selected}
            saveRule={saveRule}
            onSaveRuleChange={setSaveRule}
            ruleKeyword={ruleKeyword}
            onRuleKeywordChange={setRuleKeyword}
          />
        </Modal>
      )}

      {splitTarget && (
        <Modal
          title="Dividir movimentacao"
          description="Separe o valor em duas ou mais partes, cada uma com sua propria categoria."
          onClose={() => {
            setSplitTarget(null);
            setSplitParts([]);
          }}
          footer={
            <>
              <Button
                type="button"
                variant="secondary"
                onClick={() => {
                  setSplitTarget(null);
                  setSplitParts([]);
                }}
              >
                Cancelar
              </Button>
              <Button type="button" disabled={!canSaveSplit || splitMutation.isPending} onClick={() => splitMutation.mutate()}>
                Dividir
              </Button>
            </>
          }
        >
          <SplitTransactionForm
            transaction={splitTarget}
            parts={splitParts}
            onChange={setSplitParts}
            chartAccounts={chartAccounts.data ?? []}
            differenceCents={splitDifferenceCents}
          />
        </Modal>
      )}
    </div>
  );
}

function TransactionForm({
  value,
  onChange,
  accounts,
  chartAccounts,
  selected,
  saveRule,
  onSaveRuleChange,
  ruleKeyword,
  onRuleKeywordChange
}: {
  value: ManualTransactionPayload;
  onChange: (value: ManualTransactionPayload) => void;
  accounts: Awaited<ReturnType<typeof accountsService.list>>;
  chartAccounts: Awaited<ReturnType<typeof chartAccountsService.list>>;
  selected: Transaction | null;
  saveRule: boolean;
  onSaveRuleChange: (value: boolean) => void;
  ruleKeyword: string;
  onRuleKeywordChange: (value: string) => void;
}) {
  return (
    <div className="grid gap-3 md:grid-cols-2">
      <Select label="Conta" value={value.account_id || ""} onChange={(event) => onChange({ ...value, account_id: Number(event.target.value) })} required>
        <option value="">Selecione</option>
        {accounts.map((account) => <option key={account.id} value={account.id}>{account.name}</option>)}
      </Select>
      <Input label="Data" type="date" value={value.transaction_date} onChange={(event) => onChange({ ...value, transaction_date: event.target.value })} required />
      <Input label="Descrição" value={value.description_original} onChange={(event) => onChange({ ...value, description_original: event.target.value })} required />
      <Input label="Valor" type="number" step="0.01" value={value.amount} onChange={(event) => onChange({ ...value, amount: event.target.value })} required />
      <Select label="Tipo" value={value.transaction_type} onChange={(event) => onChange({ ...value, transaction_type: event.target.value as TransactionType })}>
        <option value="income">Receita</option>
        <option value="expense">Despesa</option>
        <option value="transfer">Transferência</option>
        <option value="reserve">Reserva</option>
        <option value="adjustment">Ajuste</option>
        <option value="credit_card_payment">Pagamento cartão</option>
      </Select>
      <Select label="Categoria" value={value.chart_account_id ?? ""} onChange={(event) => onChange({ ...value, chart_account_id: event.target.value ? Number(event.target.value) : null })}>
        <option value="">Pendente</option>
        {chartAccounts.map((item) => <option key={item.id} value={item.id}>{item.code} - {item.name}</option>)}
      </Select>
      <label className="flex items-center gap-2 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-semibold text-gray-700 md:col-span-2">
        <input type="checkbox" checked={value.is_internal_transfer} onChange={(event) => onChange({ ...value, is_internal_transfer: event.target.checked })} />
        Transferência interna, reserva ou movimentação que não deve distorcer receitas e despesas reais
      </label>
      {selected && (
        <div className="grid gap-3 rounded-lg border border-emerald-200 bg-emerald-50 p-3 md:col-span-2 md:grid-cols-[1fr_1fr]">
          <label className="flex items-center gap-2 text-sm font-bold text-emerald-900">
            <input type="checkbox" checked={saveRule} onChange={(event) => onSaveRuleChange(event.target.checked)} />
            Salvar regra para transações iguais no futuro
          </label>
          <Input
            label="Palavra-chave da regra"
            value={ruleKeyword}
            onChange={(event) => onRuleKeywordChange(event.target.value)}
            placeholder="vazio = descrição exata"
          />
        </div>
      )}
      <label className="grid gap-1 text-sm font-medium text-gray-700 md:col-span-2">
        <span>Observações</span>
        <textarea
          className="min-h-24 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
          value={value.notes ?? ""}
          onChange={(event) => onChange({ ...value, notes: event.target.value })}
        />
      </label>
    </div>
  );
}

function ChartAccountFilterCombobox({
  chartAccounts,
  value,
  disabled,
  onChange
}: {
  chartAccounts: Awaited<ReturnType<typeof chartAccountsService.list>>;
  value?: number;
  disabled?: boolean;
  onChange: (value: number | undefined) => void;
}) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const selected = chartAccounts.find((item) => item.id === value);
  const filtered = useMemo(() => {
    const q = query.toLowerCase().trim();
    const active = chartAccounts.filter((item) => item.is_active);
    if (!q) return active;
    return active.filter((item) => item.code.toLowerCase().includes(q) || item.name.toLowerCase().includes(q));
  }, [chartAccounts, query]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
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
        disabled={disabled}
        placeholder={disabled ? "Sem categoria" : selected ? `${selected.code} - ${selected.name}` : "Buscar por numero ou nome..."}
        value={open ? query : disabled ? "Sem categoria" : selected ? `${selected.code} - ${selected.name}` : ""}
        onFocus={() => {
          if (disabled) return;
          setOpen(true);
          setQuery("");
        }}
        onChange={(event) => setQuery(event.target.value)}
        className="min-h-10 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100 disabled:bg-gray-100 disabled:text-gray-500"
      />
      {open && !disabled && (
        <ul className="absolute z-50 mt-1 max-h-64 w-full overflow-auto rounded-lg border border-gray-200 bg-white text-sm shadow-lg">
          <li
            className="cursor-pointer px-3 py-2 font-semibold text-gray-700 hover:bg-emerald-50"
            onMouseDown={() => {
              onChange(undefined);
              setOpen(false);
              setQuery("");
            }}
          >
            Todas as categorias
          </li>
          {filtered.map((item) => (
            <li
              key={item.id}
              className={`cursor-pointer px-3 py-2 hover:bg-emerald-50 ${item.id === value ? "bg-emerald-50 font-bold text-emerald-800" : "text-gray-700"}`}
              onMouseDown={() => {
                onChange(item.id);
                setOpen(false);
                setQuery("");
              }}
            >
              {item.code} - {item.name}
            </li>
          ))}
          {filtered.length === 0 && <li className="px-3 py-2 text-gray-400">Nenhuma categoria encontrada.</li>}
        </ul>
      )}
    </div>
  );
}

function SplitTransactionForm({
  transaction,
  parts,
  onChange,
  chartAccounts,
  differenceCents
}: {
  transaction: Transaction;
  parts: TransactionSplitPartPayload[];
  onChange: (parts: TransactionSplitPartPayload[]) => void;
  chartAccounts: Awaited<ReturnType<typeof chartAccountsService.list>>;
  differenceCents: number;
}) {
  const totalCents = splitPartsTotalCents(parts);

  function updatePart(index: number, patch: Partial<TransactionSplitPartPayload>) {
    onChange(parts.map((part, partIndex) => (partIndex === index ? { ...part, ...patch } : part)));
  }

  return (
    <div className="grid gap-4">
      <div className="grid gap-2 rounded-lg border border-gray-200 bg-gray-50 p-3 text-sm md:grid-cols-3">
        <div>
          <div className="text-xs font-semibold uppercase text-gray-500">Original</div>
          <div className="font-bold text-gray-950">{transaction.description_original}</div>
        </div>
        <div>
          <div className="text-xs font-semibold uppercase text-gray-500">Data</div>
          <div className="font-bold text-gray-950">{transaction.transaction_date}</div>
        </div>
        <div>
          <div className="text-xs font-semibold uppercase text-gray-500">Valor</div>
          <div className="font-bold text-gray-950">{money(transaction.amount)}</div>
        </div>
      </div>

      <div className="grid gap-3">
        {parts.map((part, index) => (
          <div key={index} className="grid gap-3 rounded-lg border border-gray-200 p-3 md:grid-cols-[1.4fr_0.7fr_0.8fr_1.2fr_auto]">
            <Input
              label={`Descricao ${index + 1}`}
              value={part.description_original ?? ""}
              onChange={(event) => updatePart(index, { description_original: event.target.value })}
              required
            />
            <Input
              label="Valor"
              type="number"
              step="0.01"
              value={part.amount}
              onChange={(event) => updatePart(index, { amount: event.target.value })}
              required
            />
            <Select
              label="Tipo"
              value={part.transaction_type ?? transaction.transaction_type}
              onChange={(event) => updatePart(index, { transaction_type: event.target.value as TransactionType })}
            >
              <option value="income">Receita</option>
              <option value="expense">Despesa</option>
              <option value="transfer">Transferencia</option>
              <option value="reserve">Reserva</option>
              <option value="adjustment">Ajuste</option>
              <option value="credit_card_payment">Pagamento cartao</option>
            </Select>
            <Select
              label="Categoria"
              value={part.chart_account_id ?? ""}
              onChange={(event) => updatePart(index, { chart_account_id: event.target.value ? Number(event.target.value) : null })}
            >
              <option value="">Pendente</option>
              {chartAccounts.map((item) => <option key={item.id} value={item.id}>{item.code} - {item.name}</option>)}
            </Select>
            <div className="flex items-end">
              <Button
                type="button"
                title="Remover parte"
                variant="ghost"
                icon={<Trash2 size={16} />}
                disabled={parts.length <= 2}
                onClick={() => onChange(parts.filter((_, partIndex) => partIndex !== index))}
              />
            </div>
            <label className="grid gap-1 text-sm font-medium text-gray-700 md:col-span-5">
              <span>Observacoes</span>
              <textarea
                className="min-h-20 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
                value={part.notes ?? ""}
                onChange={(event) => updatePart(index, { notes: event.target.value })}
              />
            </label>
          </div>
        ))}
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <Button
          type="button"
          variant="secondary"
          icon={<Plus size={16} />}
          onClick={() =>
            onChange([
              ...parts,
              {
                description_original: transaction.description_original,
                amount: "0.00",
                chart_account_id: null,
                reserve_box_id: transaction.reserve_box_id,
                transaction_type: transaction.transaction_type,
                notes: "",
                is_internal_transfer: transaction.is_internal_transfer
              }
            ])
          }
        >
          Adicionar parte
        </Button>
        <div className={`rounded-lg px-3 py-2 text-sm font-bold ${differenceCents === 0 ? "bg-emerald-50 text-emerald-800" : "bg-amber-50 text-amber-900"}`}>
          Total das partes: {money(totalCents / 100)} | Diferenca: {money(differenceCents / 100)}
        </div>
      </div>
    </div>
  );
}

function buildInitialSplitParts(transaction: Transaction): TransactionSplitPartPayload[] {
  const totalCents = toCents(transaction.amount);
  const firstCents = Math.trunc(totalCents / 2);
  const secondCents = totalCents - firstCents;
  const base: Omit<TransactionSplitPartPayload, "amount" | "chart_account_id"> = {
    description_original: transaction.description_original,
    reserve_box_id: transaction.reserve_box_id,
    transaction_type: transaction.transaction_type,
    notes: transaction.notes ?? "",
    is_internal_transfer: transaction.is_internal_transfer
  };
  return [
    {
      ...base,
      amount: centsToAmount(firstCents),
      chart_account_id: transaction.chart_account_id
    },
    {
      ...base,
      amount: centsToAmount(secondCents),
      chart_account_id: null
    }
  ];
}

function splitPartsTotalCents(parts: TransactionSplitPartPayload[]): number {
  return parts.reduce((total, part) => total + toCents(part.amount), 0);
}

function toCents(value: string | number | null | undefined): number {
  return Math.round(Number(value ?? 0) * 100);
}

function centsToAmount(cents: number): string {
  return (cents / 100).toFixed(2);
}

function monthFilter(month: string): Pick<TransactionFilters, "start_date" | "end_date"> {
  const [year, monthNumber] = month.split("-").map(Number);
  const start = new Date(year, monthNumber - 1, 1);
  const end = new Date(year, monthNumber, 0);
  return { start_date: toISODate(start), end_date: toISODate(end) };
}

function lastDaysFilter(days: number): Pick<TransactionFilters, "start_date" | "end_date"> {
  const end = new Date();
  const start = new Date();
  start.setDate(end.getDate() - days + 1);
  return { start_date: toISODate(start), end_date: toISODate(end) };
}

function toISODate(value: Date): string {
  return `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, "0")}-${String(value.getDate()).padStart(2, "0")}`;
}

function buildActiveFilterLabels(
  filters: TransactionFilters,
  accounts: Awaited<ReturnType<typeof accountsService.list>>,
  chartAccounts: Awaited<ReturnType<typeof chartAccountsService.list>>
): Array<{ key: keyof TransactionFilters; label: string }> {
  const items: Array<{ key: keyof TransactionFilters; label: string }> = [];
  if (filters.search) items.push({ key: "search", label: `Busca: ${filters.search}` });
  if (filters.start_date) items.push({ key: "start_date", label: `Inicio: ${filters.start_date}` });
  if (filters.end_date) items.push({ key: "end_date", label: `Fim: ${filters.end_date}` });
  if (filters.account_id) {
    const account = accounts.find((item) => item.id === filters.account_id);
    items.push({ key: "account_id", label: `Conta: ${account?.name ?? filters.account_id}` });
  }
  if (filters.uncategorized) items.push({ key: "uncategorized", label: "Sem categoria" });
  if (filters.chart_account_id) {
    const account = chartAccounts.find((item) => item.id === filters.chart_account_id);
    items.push({ key: "chart_account_id", label: `Categoria: ${account ? `${account.code} - ${account.name}` : filters.chart_account_id}` });
  }
  if (filters.transaction_type) items.push({ key: "transaction_type", label: `Tipo: ${transactionTypeLabel(filters.transaction_type)}` });
  if (filters.status) items.push({ key: "status", label: `Status: ${statusLabel(filters.status)}` });
  if (filters.source) items.push({ key: "source", label: `Origem: ${sourceLabel(filters.source)}` });
  return items;
}

function transactionTypeLabel(value: TransactionType): string {
  const labels: Record<TransactionType, string> = {
    income: "Receita",
    expense: "Despesa",
    transfer: "Transferencia",
    reserve: "Reserva",
    adjustment: "Ajuste",
    credit_card_payment: "Pagamento cartao"
  };
  return labels[value];
}

function statusLabel(value: ClassificationStatus): string {
  const labels: Record<ClassificationStatus, string> = {
    pending: "Pendente",
    automatic: "Automatico",
    manual: "Manual",
    reviewed: "Revisado"
  };
  return labels[value];
}

function sourceLabel(value: TransactionSource): string {
  const labels: Record<TransactionSource, string> = {
    manual: "Manual",
    nubank_csv: "Nubank CSV",
    nubank_ofx: "Nubank OFX",
    mercado_pago_xlsx: "Mercado Pago"
  };
  return labels[value];
}
