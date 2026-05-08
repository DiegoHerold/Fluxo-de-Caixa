import { CheckCircle2, Plus, Search, Split, Trash2 } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { EmptyState } from "../components/ui/EmptyState";
import { Input, Select } from "../components/ui/Input";
import { Modal } from "../components/ui/Modal";
import { PageToolbar } from "../components/ui/PageToolbar";
import { formatDateBR, money } from "../services/api";
import { chartAccountsService } from "../services/chartAccountsService";
import { reserveBoxesService } from "../services/reserveBoxesService";
import { transactionsService, type TransactionSplitPartPayload } from "../services/transactionsService";
import type { ChartAccount } from "../types/chartAccount";
import type { ReserveBox } from "../types/reserveBox";
import type { Transaction, TransactionType } from "../types/transaction";

export function PendingTransactionsPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [filterType, setFilterType] = useState<"" | "income" | "expense">(""); 
  const [splitTarget, setSplitTarget] = useState<Transaction | null>(null);
  const [splitParts, setSplitParts] = useState<TransactionSplitPartPayload[]>([]);

  const pending = useQuery({ queryKey: ["pending-transactions"], queryFn: transactionsService.pending });
  const chartAccounts = useQuery({ queryKey: ["chart-accounts"], queryFn: () => chartAccountsService.list() });
  const reserveBoxes = useQuery({ queryKey: ["reserve-boxes"], queryFn: () => reserveBoxesService.list() });

  const mutation = useMutation({
    mutationFn: async (payload: {
      tx: Transaction;
      chart_account_id: number;
      transaction_type: TransactionType;
      reserve_box_id: number | null;
      create_rule: boolean;
      keyword?: string;
    }) => {
      await transactionsService.classify(payload.tx.id, {
        chart_account_id: payload.chart_account_id,
        transaction_type: payload.transaction_type,
        is_internal_transfer: ["transfer", "reserve"].includes(payload.transaction_type),
        reserve_box_id: payload.reserve_box_id,
        create_rule: payload.create_rule,
        rule_keyword: payload.keyword || null,
        rule_match_type: payload.keyword ? "contains" : "equals",
        rule_priority: payload.keyword ? 50 : 10
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pending-transactions"] });
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["classification-rules"] });
      queryClient.invalidateQueries({ queryKey: ["loan-people"] });
      queryClient.invalidateQueries({ queryKey: ["loan-movements"] });
    }
  });

  const splitDifferenceCents = splitTarget ? splitPartsTotalCents(splitParts) - toCents(splitTarget.amount) : 0;
  const canSaveSplit =
    Boolean(splitTarget) &&
    splitParts.length >= 2 &&
    splitDifferenceCents === 0 &&
    splitParts.every((part) => part.amount !== "" && toCents(part.amount) !== 0);

  const splitMutation = useMutation({
    mutationFn: () => {
      if (!splitTarget) throw new Error("Nenhuma movimentacao selecionada");
      return transactionsService.split(splitTarget.id, splitParts);
    },
    onSuccess: () => {
      setSplitTarget(null);
      setSplitParts([]);
      queryClient.invalidateQueries({ queryKey: ["pending-transactions"] });
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["loan-people"] });
      queryClient.invalidateQueries({ queryKey: ["loan-movements"] });
    }
  });

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    return (pending.data ?? []).filter((tx) => {
      const matchesSearch = !q || tx.description_original.toLowerCase().includes(q);
      const matchesType =
        !filterType ||
        (filterType === "income" ? Number(tx.amount) >= 0 : Number(tx.amount) < 0);
      return matchesSearch && matchesType;
    });
  }, [pending.data, search, filterType]);

  return (
    <div className="grid gap-5">
      <PageToolbar>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="text-sm font-black text-gray-950">Pendências para classificar</div>
            <div className="text-sm text-gray-500">Ao classificar, uma regra exata fica marcada por padrão para próximas transações iguais.</div>
          </div>
          <Badge value={`${pending.data?.length ?? 0} pendentes`} />
        </div>
      </PageToolbar>

      {/* Filtros */}
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-48">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
          <input
            type="text"
            placeholder="Buscar por descrição..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-gray-200 bg-white py-2 pl-9 pr-3 text-sm text-gray-800 placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value as "" | "income" | "expense")}
          className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="">Entradas e saídas</option>
          <option value="income">Só entradas</option>
          <option value="expense">Só saídas</option>
        </select>
      </div>

      {filtered.map((tx) => (
        <PendingRow
          key={tx.id}
          tx={tx}
          chartAccounts={chartAccounts.data ?? []}
          reserveBoxes={(reserveBoxes.data ?? []).filter((b) => b.account_id === tx.account_id && b.is_active)}
          isSaving={mutation.isPending}
          onClassify={(payload) => mutation.mutate(payload)}
          onSplit={(transaction) => {
            setSplitTarget(transaction);
            setSplitParts(buildInitialSplitParts(transaction));
          }}
        />
      ))}

      {pending.data?.length === 0 && (
        <EmptyState title="Tudo classificado" description="Quando novas movimentações sem regra entrarem, elas aparecerão aqui." />
      )}

      {pending.data && pending.data.length > 0 && filtered.length === 0 && (
        <EmptyState title="Nenhum resultado" description="Tente ajustar a busca ou os filtros." />
      )}

      {splitTarget && (
        <Modal
          title="Dividir pendencia"
          description="Separe o valor em duas ou mais partes antes de classificar."
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

function PendingRow({
  tx,
  chartAccounts,
  reserveBoxes,
  isSaving,
  onClassify,
  onSplit
}: {
  tx: Transaction;
  chartAccounts: ChartAccount[];
  reserveBoxes: ReserveBox[];
  isSaving: boolean;
  onClassify: (payload: {
    tx: Transaction;
    chart_account_id: number;
    transaction_type: TransactionType;
    reserve_box_id: number | null;
    create_rule: boolean;
    keyword?: string;
  }) => void;
  onSplit: (transaction: Transaction) => void;
}) {
  const [chartAccountId, setChartAccountId] = useState(0);
  const [transactionType, setTransactionType] = useState<TransactionType>(Number(tx.amount) >= 0 ? "income" : "expense");
  const [destination, setDestination] = useState("account");
  const [createRule, setCreateRule] = useState(true);
  const [keyword, setKeyword] = useState("");

  const reserveBoxId = destination === "account" ? null : Number(destination);

  return (
    <div className="grid gap-4 rounded-xl border border-gray-200 bg-white p-4 shadow-sm xl:grid-cols-[0.9fr_1.4fr]">
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge value={tx.classification_status} />
          <span className="text-sm font-medium text-gray-500">{formatDateBR(tx.transaction_date)}</span>
          <span className="text-sm font-medium text-gray-500">{tx.account_name}</span>
        </div>
        <div className="mt-2 text-base font-black text-gray-950">{tx.description_original}</div>
        <div className={`mt-1 text-xl font-black ${Number(tx.amount) < 0 ? "text-rose-700" : "text-emerald-700"}`}>{money(tx.amount)}</div>
        <div className="mt-2 text-xs font-medium text-gray-500">Regra exata sugerida: descrição limpa da própria movimentação.</div>
      </div>

      <div className="grid gap-3 md:grid-cols-[1.4fr_1fr_1fr_auto]">
        <div className="md:col-span-4">
          <CategoryCombobox
            chartAccounts={chartAccounts}
            value={chartAccountId}
            onChange={setChartAccountId}
          />
        </div>
        <Select label="Tipo" value={transactionType} onChange={(event) => setTransactionType(event.target.value as TransactionType)}>
          <option value="income">Receita</option>
          <option value="expense">Despesa</option>
          <option value="transfer">Transferência</option>
          <option value="reserve">Reserva</option>
          <option value="adjustment">Ajuste</option>
          <option value="credit_card_payment">Pagamento cartão</option>
        </Select>
        <Select
          label="Destino"
          value={destination}
          onChange={(event) => {
            const nextDestination = event.target.value;
            setDestination(nextDestination);
            if (nextDestination !== "account") {
              const reserveBox = reserveBoxes.find((box) => box.id === Number(nextDestination));
              const linkedChartAccountId = Number(tx.amount) >= 0 ? reserveBox?.withdrawal_chart_account_id : reserveBox?.chart_account_id;
              if (linkedChartAccountId) {
                setChartAccountId(linkedChartAccountId);
                setTransactionType("transfer");
              }
            }
          }}
        >
          <option value="account">Saldo da conta</option>
          {reserveBoxes.map((box) => (
            <option key={box.id} value={box.id}>{box.name}{box.chart_account_code ? ` (${box.chart_account_code})` : ""}</option>
          ))}
        </Select>
        <Input label="Palavra-chave" value={keyword} onChange={(event) => setKeyword(event.target.value)} placeholder="opcional" />
        <div className="flex items-end gap-2">
          <Button
            type="button"
            title="Dividir lancamento"
            variant="secondary"
            icon={<Split size={16} />}
            onClick={() => onSplit(tx)}
          />
          <Button
            className="w-full"
            icon={<CheckCircle2 size={16} />}
            disabled={!chartAccountId || isSaving}
            onClick={() =>
              onClassify({
                tx,
                chart_account_id: chartAccountId,
                transaction_type: transactionType,
                reserve_box_id: reserveBoxId,
                create_rule: createRule,
                keyword: keyword || undefined
              })
            }
          >
            Classificar
          </Button>
        </div>
        <label className="flex items-center gap-2 text-sm font-semibold text-gray-700 md:col-span-2">
          <input type="checkbox" checked={createRule} onChange={(event) => setCreateRule(event.target.checked)} />
          Salvar regra para próximas transações iguais
        </label>
      </div>
    </div>
  );
}

function CategoryCombobox({
  chartAccounts,
  value,
  onChange
}: {
  chartAccounts: ChartAccount[];
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
  chartAccounts: ChartAccount[];
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
