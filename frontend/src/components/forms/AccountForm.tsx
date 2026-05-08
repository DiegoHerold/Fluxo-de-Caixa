import { Save } from "lucide-react";
import { useEffect, useState } from "react";
import type { Account } from "../../types/account";
import { Button } from "../ui/Button";
import { Input, Select } from "../ui/Input";

type FormState = {
  name: string;
  institution: string;
  account_type: string;
  initial_balance: string;
  is_active: boolean;
};

const emptyState: FormState = {
  name: "",
  institution: "",
  account_type: "checking",
  initial_balance: "0.00",
  is_active: true
};

export function AccountForm({
  selected,
  defaults,
  onSubmit,
  onCancel
}: {
  selected?: Account | null;
  defaults?: Partial<FormState>;
  onSubmit: (payload: FormState) => void;
  onCancel?: () => void;
}) {
  const [form, setForm] = useState<FormState>(emptyState);

  useEffect(() => {
    if (selected) {
      setForm({
        name: selected.name,
        institution: selected.institution ?? "",
        account_type: selected.account_type,
        initial_balance: selected.initial_balance,
        is_active: selected.is_active
      });
    } else {
      setForm({ ...emptyState, ...defaults });
    }
  }, [selected, defaults?.name, defaults?.institution, defaults?.account_type, defaults?.initial_balance, defaults?.is_active]);

  return (
    <form
      className="grid gap-3"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit(form);
      }}
    >
      <Input label="Conta" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required />
      <Input label="Instituição" value={form.institution} onChange={(event) => setForm({ ...form, institution: event.target.value })} />
      <Select label="Tipo" value={form.account_type} onChange={(event) => setForm({ ...form, account_type: event.target.value })}>
        <option value="checking">Conta corrente</option>
        <option value="wallet">Carteira digital</option>
        <option value="credit_card">Cartão de crédito</option>
        <option value="reserve">Reserva</option>
        <option value="investment">Investimento</option>
        <option value="cash">Dinheiro</option>
        <option value="manual">Manual</option>
      </Select>
      <Input label="Saldo inicial" type="number" step="0.01" value={form.initial_balance} onChange={(event) => setForm({ ...form, initial_balance: event.target.value })} />
      <label className="flex items-center gap-2 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-semibold text-gray-700">
        <input type="checkbox" checked={form.is_active} onChange={(event) => setForm({ ...form, is_active: event.target.checked })} />
        Conta ativa
      </label>
      <div className="flex items-end gap-2">
        <Button className="w-full" icon={<Save size={16} />}>{selected ? "Salvar" : "Cadastrar"}</Button>
        {selected && onCancel && <Button type="button" variant="secondary" onClick={onCancel}>Cancelar</Button>}
      </div>
    </form>
  );
}
