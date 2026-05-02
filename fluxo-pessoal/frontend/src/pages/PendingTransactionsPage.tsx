import { CheckCircle2 } from "lucide-react";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { EmptyState } from "../components/ui/EmptyState";
import { Input, Select } from "../components/ui/Input";
import { PageToolbar } from "../components/ui/PageToolbar";
import { formatDateBR, money } from "../services/api";
import { chartAccountsService } from "../services/chartAccountsService";
import { transactionsService } from "../services/transactionsService";
import type { ChartAccount } from "../types/chartAccount";
import type { Transaction, TransactionType } from "../types/transaction";

export function PendingTransactionsPage() {
  const queryClient = useQueryClient();
  const pending = useQuery({ queryKey: ["pending-transactions"], queryFn: transactionsService.pending });
  const chartAccounts = useQuery({ queryKey: ["chart-accounts"], queryFn: () => chartAccountsService.list() });

  const mutation = useMutation({
    mutationFn: async (payload: {
      tx: Transaction;
      chart_account_id: number;
      transaction_type: TransactionType;
      is_internal_transfer: boolean;
      create_rule: boolean;
      keyword?: string;
    }) => {
      await transactionsService.classify(payload.tx.id, {
        chart_account_id: payload.chart_account_id,
        transaction_type: payload.transaction_type,
        is_internal_transfer: payload.is_internal_transfer,
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
    }
  });

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

      {(pending.data ?? []).map((tx) => (
        <PendingRow
          key={tx.id}
          tx={tx}
          chartAccounts={chartAccounts.data ?? []}
          isSaving={mutation.isPending}
          onClassify={(payload) => mutation.mutate(payload)}
        />
      ))}
      {pending.data?.length === 0 && (
        <EmptyState title="Tudo classificado" description="Quando novas movimentações sem regra entrarem, elas aparecerão aqui." />
      )}
    </div>
  );
}

function PendingRow({
  tx,
  chartAccounts,
  isSaving,
  onClassify
}: {
  tx: Transaction;
  chartAccounts: ChartAccount[];
  isSaving: boolean;
  onClassify: (payload: {
    tx: Transaction;
    chart_account_id: number;
    transaction_type: TransactionType;
    is_internal_transfer: boolean;
    create_rule: boolean;
    keyword?: string;
  }) => void;
}) {
  const [chartAccountId, setChartAccountId] = useState("");
  const [transactionType, setTransactionType] = useState<TransactionType>(Number(tx.amount) >= 0 ? "income" : "expense");
  const [internalTransfer, setInternalTransfer] = useState(false);
  const [createRule, setCreateRule] = useState(true);
  const [keyword, setKeyword] = useState("");

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
        <Select label="Categoria" value={chartAccountId} onChange={(event) => setChartAccountId(event.target.value)} required>
          <option value="">Selecione</option>
          {chartAccounts.map((item) => <option key={item.id} value={item.id}>{item.code} - {item.name}</option>)}
        </Select>
        <Select label="Tipo" value={transactionType} onChange={(event) => setTransactionType(event.target.value as TransactionType)}>
          <option value="income">Receita</option>
          <option value="expense">Despesa</option>
          <option value="transfer">Transferência</option>
          <option value="reserve">Reserva</option>
          <option value="adjustment">Ajuste</option>
          <option value="credit_card_payment">Pagamento cartão</option>
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
                chart_account_id: Number(chartAccountId),
                transaction_type: transactionType,
                is_internal_transfer: internalTransfer,
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
        <label className="flex items-center gap-2 text-sm font-semibold text-gray-700 md:col-span-2">
          <input type="checkbox" checked={internalTransfer} onChange={(event) => setInternalTransfer(event.target.checked)} />
          Transferência interna
        </label>
      </div>
    </div>
  );
}
