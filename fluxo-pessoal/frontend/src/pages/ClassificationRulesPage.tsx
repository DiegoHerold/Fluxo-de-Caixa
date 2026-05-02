import { Edit3, PlayCircle, Plus, Power } from "lucide-react";
import { useEffect, useState } from "react";
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
              {rules.data?.map((rule) => {
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
      <Select label="Categoria" value={form.chart_account_id || ""} onChange={(event) => onChange({ ...form, chart_account_id: Number(event.target.value) })} required>
        <option value="">Selecione</option>
        {chartAccounts.map((item) => <option key={item.id} value={item.id}>{item.code} - {item.name}</option>)}
      </Select>
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
