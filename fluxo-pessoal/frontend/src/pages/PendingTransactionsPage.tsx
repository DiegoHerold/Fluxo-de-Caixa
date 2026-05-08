import { CheckCircle2, Search } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { EmptyState } from "../components/ui/EmptyState";
import { Input, Select } from "../components/ui/Input";
import { PageToolbar } from "../components/ui/PageToolbar";
import { formatDateBR, money } from "../services/api";
import { chartAccountsService } from "../services/chartAccountsService";
import { reserveBoxesService } from "../services/reserveBoxesService";
import { transactionsService } from "../services/transactionsService";
import type { ChartAccount } from "../types/chartAccount";
import type { ReserveBox } from "../types/reserveBox";
import type { Transaction, TransactionType } from "../types/transaction";

export function PendingTransactionsPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [filterType, setFilterType] = useState<"" | "income" | "expense">(""); 

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
        />
      ))}

      {pending.data?.length === 0 && (
        <EmptyState title="Tudo classificado" description="Quando novas movimentações sem regra entrarem, elas aparecerão aqui." />
      )}

      {pending.data && pending.data.length > 0 && filtered.length === 0 && (
        <EmptyState title="Nenhum resultado" description="Tente ajustar a busca ou os filtros." />
      )}
    </div>
  );
}

function PendingRow({
  tx,
  chartAccounts,
  reserveBoxes,
  isSaving,
  onClassify
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
        <Select label="Destino" value={destination} onChange={(event) => setDestination(event.target.value)}>
          <option value="account">Saldo da conta</option>
          {reserveBoxes.map((box) => (
            <option key={box.id} value={box.id}>{box.name}</option>
          ))}
        </Select>
        <Input label="Palavra-chave" value={keyword} onChange={(event) => setKeyword(event.target.value)} placeholder="opcional" />
        <div className="flex items-end">
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
