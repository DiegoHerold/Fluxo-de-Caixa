import { Scale } from "lucide-react";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Input, Select } from "../components/ui/Input";
import { currentMonth, money } from "../services/api";
import { accountsService } from "../services/accountsService";
import { balancesService } from "../services/balancesService";

export function BalancesPage() {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({ account_id: "", period_month: currentMonth(), real_balance: "0.00" });
  const accounts = useQuery({ queryKey: ["accounts"], queryFn: accountsService.list });
  const snapshots = useQuery({ queryKey: ["snapshots"], queryFn: balancesService.snapshots });

  const reconcileMutation = useMutation({
    mutationFn: () => balancesService.reconcile({ account_id: Number(form.account_id), period_month: form.period_month, real_balance: form.real_balance }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["snapshots"] })
  });

  return (
    <div className="grid gap-6">
      <form
        className="grid gap-3 rounded-lg border border-gray-200 bg-white p-4 md:grid-cols-[1fr_1fr_1fr_auto]"
        onSubmit={(event) => {
          event.preventDefault();
          if (form.account_id) reconcileMutation.mutate();
        }}
      >
        <Select label="Conta" value={form.account_id} onChange={(event) => setForm({ ...form, account_id: event.target.value })} required>
          <option value="">Selecione</option>
          {accounts.data?.map((account) => <option key={account.id} value={account.id}>{account.name}</option>)}
        </Select>
        <Input label="Mês" type="month" value={form.period_month} onChange={(event) => setForm({ ...form, period_month: event.target.value })} />
        <Input label="Saldo real" type="number" step="0.01" value={form.real_balance} onChange={(event) => setForm({ ...form, real_balance: event.target.value })} />
        <div className="flex items-end">
          <Button className="w-full" icon={<Scale size={16} />}>Conciliar</Button>
        </div>
      </form>

      <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-100 text-left text-xs font-bold uppercase text-gray-600">
            <tr>
              <th className="px-3 py-3">Mês</th>
              <th className="px-3 py-3">Conta</th>
              <th className="px-3 py-3 text-right">Calculado</th>
              <th className="px-3 py-3 text-right">Real</th>
              <th className="px-3 py-3 text-right">Diferença</th>
              <th className="px-3 py-3">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {snapshots.data?.map((snapshot) => {
              const account = accounts.data?.find((item) => item.id === snapshot.account_id);
              return (
                <tr key={snapshot.id}>
                  <td className="px-3 py-3 font-semibold">{snapshot.period_month}</td>
                  <td className="px-3 py-3">{account?.name ?? snapshot.account_id}</td>
                  <td className="px-3 py-3 text-right">{money(snapshot.calculated_balance)}</td>
                  <td className="px-3 py-3 text-right">{money(snapshot.real_balance)}</td>
                  <td className="px-3 py-3 text-right font-semibold">{money(snapshot.difference)}</td>
                  <td className="px-3 py-3"><Badge value={snapshot.status} /></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
