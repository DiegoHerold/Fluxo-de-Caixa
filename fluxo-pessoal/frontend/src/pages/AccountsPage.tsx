import { Edit3, PiggyBank, Plus, Power } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AccountForm } from "../components/forms/AccountForm";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { EmptyState } from "../components/ui/EmptyState";
import { Input, Select } from "../components/ui/Input";
import { Modal } from "../components/ui/Modal";
import { PageToolbar } from "../components/ui/PageToolbar";
import { money } from "../services/api";
import { accountsService } from "../services/accountsService";
import { reserveBoxesService, type ReserveBoxPayload } from "../services/reserveBoxesService";
import type { Account } from "../types/account";
import type { ReserveBox } from "../types/reserveBox";

const emptyReserve: ReserveBoxPayload = {
  account_id: 0,
  name: "",
  current_balance: "0.00",
  target_amount: "",
  notes: "",
  is_active: true
};

export function AccountsPage() {
  const queryClient = useQueryClient();
  const [selected, setSelected] = useState<Account | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [reserveOpen, setReserveOpen] = useState(false);
  const [selectedReserve, setSelectedReserve] = useState<ReserveBox | null>(null);
  const [reserveForm, setReserveForm] = useState<ReserveBoxPayload>(emptyReserve);

  const accounts = useQuery({ queryKey: ["accounts"], queryFn: accountsService.list });
  const balances = useQuery({ queryKey: ["account-balances"], queryFn: accountsService.balances });
  const reserveBoxes = useQuery({ queryKey: ["reserve-boxes"], queryFn: () => reserveBoxesService.list() });

  const balancesById = useMemo(() => new Map((balances.data ?? []).map((item) => [item.id, item])), [balances.data]);
  const accountsById = useMemo(() => new Map((accounts.data ?? []).map((item) => [item.id, item])), [accounts.data]);

  useEffect(() => {
    setReserveForm(
      selectedReserve
        ? {
            account_id: selectedReserve.account_id,
            name: selectedReserve.name,
            current_balance: selectedReserve.current_balance,
            target_amount: selectedReserve.target_amount ?? "",
            notes: selectedReserve.notes ?? "",
            is_active: selectedReserve.is_active
          }
        : { ...emptyReserve, account_id: accounts.data?.[0]?.id ?? 0 }
    );
  }, [selectedReserve, reserveOpen, accounts.data]);

  const saveMutation = useMutation({
    mutationFn: (payload: Parameters<typeof accountsService.create>[0]) =>
      selected ? accountsService.update(selected.id, payload) : accountsService.create(payload),
    onSuccess: () => {
      setSelected(null);
      setFormOpen(false);
      invalidateMoney(queryClient);
    }
  });

  const deactivateMutation = useMutation({
    mutationFn: accountsService.deactivate,
    onSuccess: () => invalidateMoney(queryClient)
  });

  const saveReserveMutation = useMutation({
    mutationFn: () => {
      const payload = {
        ...reserveForm,
        target_amount: reserveForm.target_amount || null,
        notes: reserveForm.notes || null
      };
      return selectedReserve ? reserveBoxesService.update(selectedReserve.id, payload) : reserveBoxesService.create(payload);
    },
    onSuccess: () => {
      setSelectedReserve(null);
      setReserveOpen(false);
      invalidateMoney(queryClient);
    }
  });

  const deactivateReserveMutation = useMutation({
    mutationFn: reserveBoxesService.deactivate,
    onSuccess: () => invalidateMoney(queryClient)
  });

  return (
    <div className="grid gap-6">
      <PageToolbar>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="text-sm font-black text-gray-950">Contas e caixinhas</div>
            <div className="text-sm text-gray-500">Gerencie contas, saldo inicial e caixinhas com valor editável.</div>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="secondary"
              icon={<PiggyBank size={16} />}
              onClick={() => {
                setSelectedReserve(null);
                setReserveOpen(true);
              }}
            >
              Nova caixinha
            </Button>
            <Button
              icon={<Plus size={16} />}
              onClick={() => {
                setSelected(null);
                setFormOpen(true);
              }}
            >
              Nova conta
            </Button>
          </div>
        </div>
      </PageToolbar>

      {!accounts.data?.length ? (
        <EmptyState
          title="Nenhuma conta cadastrada"
          description="Crie sua primeira conta financeira para importar extratos e calcular saldos."
          action={<Button icon={<Plus size={16} />} onClick={() => setFormOpen(true)}>Criar conta</Button>}
        />
      ) : (
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-100 text-left text-xs font-bold uppercase text-gray-600">
                <tr>
                  <th className="px-3 py-3">Conta</th>
                  <th className="px-3 py-3">Tipo</th>
                  <th className="px-3 py-3 text-right">Saldo inicial</th>
                  <th className="px-3 py-3 text-right">Disponível</th>
                  <th className="px-3 py-3 text-right">Caixinhas</th>
                  <th className="px-3 py-3 text-right">Total</th>
                  <th className="px-3 py-3">Status</th>
                  <th className="px-3 py-3 text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {accounts.data?.map((account) => (
                  <tr key={account.id} className="hover:bg-gray-50">
                    <td className="px-3 py-3">
                      <div className="font-bold text-gray-950">{account.name}</div>
                      <div className="text-xs text-gray-500">{account.institution || "Sem instituição"}</div>
                    </td>
                    <td className="px-3 py-3">{account.account_type}</td>
                    <td className="px-3 py-3 text-right">{money(account.initial_balance)}</td>
                    <td className="px-3 py-3 text-right font-bold">{money(balancesById.get(account.id)?.calculated_balance ?? account.current_balance)}</td>
                    <td className="px-3 py-3 text-right">{money(balancesById.get(account.id)?.reserve_balance ?? 0)}</td>
                    <td className="px-3 py-3 text-right font-black">{money(balancesById.get(account.id)?.balance_with_reserves ?? account.current_balance)}</td>
                    <td className="px-3 py-3">
                      <Badge value={account.is_active ? "ativa" : "inativa"} />
                    </td>
                    <td className="px-3 py-3 text-right">
                      <div className="flex justify-end gap-2">
                        <Button
                          title="Editar"
                          variant="secondary"
                          icon={<Edit3 size={16} />}
                          onClick={() => {
                            setSelected(account);
                            setFormOpen(true);
                          }}
                        />
                        <Button title="Desativar" variant="ghost" icon={<Power size={16} />} onClick={() => deactivateMutation.mutate(account.id)} />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <section className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-black text-gray-950">Caixinhas cadastradas</h2>
            <p className="text-sm text-gray-500">Esses valores são manuais e editáveis. Se houver caixinha detectada com o mesmo nome, o valor manual prevalece.</p>
          </div>
          <Button
            variant="secondary"
            icon={<PiggyBank size={16} />}
            onClick={() => {
              setSelectedReserve(null);
              setReserveOpen(true);
            }}
          >
            Nova caixinha
          </Button>
        </div>

        <div className="mt-4 grid gap-6">
          {(accounts.data ?? []).map((account) => {
            const boxes = (reserveBoxes.data ?? []).filter((box) => box.account_id === account.id);
            if (!boxes.length) return null;
            return (
              <div key={account.id}>
                <div className="mb-2 flex items-center gap-2">
                  <span className="text-xs font-bold uppercase text-gray-500">{account.name}</span>
                  {account.institution && <span className="text-xs text-gray-400">· {account.institution}</span>}
                </div>
                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                  {boxes.map((box) => (
                    <div key={box.id} className="rounded-xl border border-gray-200 bg-gray-50 p-4">
                      <div className="flex items-start justify-between gap-3">
                        <div className="font-black text-gray-950">{box.name}</div>
                        <Badge value={box.is_active ? "ativa" : "inativa"} />
                      </div>
                      <div className="mt-4 text-2xl font-black text-emerald-700">{money(box.current_balance)}</div>
                      {box.target_amount && <div className="mt-1 text-sm font-semibold text-gray-500">Meta: {money(box.target_amount)}</div>}
                      {box.notes && <p className="mt-2 text-sm text-gray-600">{box.notes}</p>}
                      <div className="mt-4 flex gap-2">
                        <Button
                          variant="secondary"
                          icon={<Edit3 size={16} />}
                          onClick={() => {
                            setSelectedReserve(box);
                            setReserveOpen(true);
                          }}
                        >
                          Editar
                        </Button>
                        <Button variant="ghost" icon={<Power size={16} />} onClick={() => deactivateReserveMutation.mutate(box.id)}>
                          Desativar
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
          {!(reserveBoxes.data ?? []).length && (
            <EmptyState title="Nenhuma caixinha manual" description="Crie caixinhas para registrar valores reais guardados fora do saldo disponível." />
          )}
        </div>
      </section>

      {formOpen && (
        <Modal
          title={selected ? "Editar conta" : "Nova conta"}
          description="O saldo calculado é derivado do saldo inicial somado às movimentações."
          onClose={() => {
            setSelected(null);
            setFormOpen(false);
          }}
        >
          <AccountForm
            selected={selected}
            onCancel={() => {
              setSelected(null);
              setFormOpen(false);
            }}
            onSubmit={(payload) => saveMutation.mutate(payload)}
          />
        </Modal>
      )}

      {reserveOpen && (
        <Modal
          title={selectedReserve ? "Editar caixinha" : "Nova caixinha"}
          description="Use o valor atual real da caixinha para que o saldo total reflita seu dinheiro guardado."
          onClose={() => {
            setSelectedReserve(null);
            setReserveOpen(false);
          }}
          footer={
            <>
              <Button type="button" variant="secondary" onClick={() => setReserveOpen(false)}>Cancelar</Button>
              <Button type="button" onClick={() => reserveForm.account_id && reserveForm.name && saveReserveMutation.mutate()}>
                {selectedReserve ? "Salvar alterações" : "Criar caixinha"}
              </Button>
            </>
          }
        >
          <ReserveBoxForm value={reserveForm} onChange={setReserveForm} accounts={accounts.data ?? []} />
        </Modal>
      )}
    </div>
  );
}

function ReserveBoxForm({
  value,
  onChange,
  accounts
}: {
  value: ReserveBoxPayload;
  onChange: (value: ReserveBoxPayload) => void;
  accounts: Account[];
}) {
  return (
    <div className="grid gap-3 md:grid-cols-2">
      <Select label="Conta vinculada" value={value.account_id || ""} onChange={(event) => onChange({ ...value, account_id: Number(event.target.value) })} required>
        <option value="">Selecione</option>
        {accounts.map((account) => <option key={account.id} value={account.id}>{account.name}</option>)}
      </Select>
      <Input label="Nome da caixinha" value={value.name} onChange={(event) => onChange({ ...value, name: event.target.value })} placeholder="Casa, Moto, Reserva..." required />
      <Input label="Valor atual" type="number" step="0.01" value={value.current_balance} onChange={(event) => onChange({ ...value, current_balance: event.target.value })} />
      <Input label="Meta" type="number" step="0.01" value={value.target_amount ?? ""} onChange={(event) => onChange({ ...value, target_amount: event.target.value })} />
      <label className="flex items-center gap-2 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-semibold text-gray-700 md:col-span-2">
        <input type="checkbox" checked={value.is_active} onChange={(event) => onChange({ ...value, is_active: event.target.checked })} />
        Caixinha ativa
      </label>
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

function invalidateMoney(queryClient: ReturnType<typeof useQueryClient>) {
  queryClient.invalidateQueries({ queryKey: ["accounts"] });
  queryClient.invalidateQueries({ queryKey: ["account-balances"] });
  queryClient.invalidateQueries({ queryKey: ["consolidated-balance"] });
  queryClient.invalidateQueries({ queryKey: ["reserves"] });
  queryClient.invalidateQueries({ queryKey: ["reserve-boxes"] });
}
