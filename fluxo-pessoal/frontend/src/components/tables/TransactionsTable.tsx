import { Edit3, Trash2 } from "lucide-react";
import { formatDateBR, money } from "../../services/api";
import type { Transaction } from "../../types/transaction";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";

export function TransactionsTable({
  transactions,
  onEdit,
  onDelete
}: {
  transactions: Transaction[];
  onEdit?: (transaction: Transaction) => void;
  onDelete?: (id: number) => void;
}) {
  const hasActions = Boolean(onEdit || onDelete);

  return (
    <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-100 text-left text-xs font-bold uppercase text-gray-600">
            <tr>
              <th className="px-3 py-3">Data</th>
              <th className="px-3 py-3">Conta</th>
              <th className="px-3 py-3">Descrição</th>
              <th className="px-3 py-3">Categoria</th>
              <th className="px-3 py-3 text-right">Valor</th>
              <th className="px-3 py-3">Tipo</th>
              <th className="px-3 py-3">Status</th>
              {hasActions && <th className="px-3 py-3 text-right">Ações</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {transactions.map((tx) => (
              <tr key={tx.id} className="hover:bg-gray-50">
                <td className="whitespace-nowrap px-3 py-3">{formatDateBR(tx.transaction_date)}</td>
                <td className="px-3 py-3">{tx.account_name ?? tx.account_id}</td>
                <td className="max-w-sm px-3 py-3">
                  <div className="font-semibold text-gray-900">{tx.description_original}</div>
                  <div className="truncate text-xs text-gray-500">{tx.source}</div>
                </td>
                <td className="px-3 py-3">{tx.chart_account_name ?? "Sem categoria"}</td>
                <td className={`whitespace-nowrap px-3 py-3 text-right font-bold ${Number(tx.amount) < 0 ? "text-rose-700" : "text-emerald-700"}`}>
                  {money(tx.amount)}
                </td>
                <td className="px-3 py-3">{tx.transaction_type}</td>
                <td className="px-3 py-3">
                  <Badge value={tx.classification_status} />
                </td>
                {hasActions && (
                  <td className="px-3 py-3 text-right">
                    <div className="flex justify-end gap-2">
                      {onEdit && <Button title="Editar" variant="secondary" icon={<Edit3 size={16} />} onClick={() => onEdit(tx)} />}
                      {onDelete && <Button title="Excluir" variant="ghost" icon={<Trash2 size={16} />} onClick={() => onDelete(tx.id)} />}
                    </div>
                  </td>
                )}
              </tr>
            ))}
            {transactions.length === 0 && (
              <tr>
                <td className="px-3 py-8 text-center text-gray-500" colSpan={hasActions ? 8 : 7}>
                  Nenhuma movimentação encontrada.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
