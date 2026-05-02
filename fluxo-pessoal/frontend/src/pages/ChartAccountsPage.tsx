import { ChevronDown, ChevronRight, Edit3, GitBranch, Plus, Sparkles, Trash2, Wand2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button } from "../components/ui/Button";
import { EmptyState } from "../components/ui/EmptyState";
import { Input, Select } from "../components/ui/Input";
import { Modal } from "../components/ui/Modal";
import { PageToolbar } from "../components/ui/PageToolbar";
import { chartAccountsService, type ChartAccountPayload } from "../services/chartAccountsService";
import type { AccountNature, ChartAccount, ChartAccountTree } from "../types/chartAccount";

const emptyForm: ChartAccountPayload = {
  code: "",
  name: "",
  parent_id: null,
  account_nature: "expense",
  is_active: true
};

const natureLabel: Record<AccountNature, string> = {
  income: "Receita",
  expense: "Despesa",
  transfer: "Transferência",
  reserve: "Reserva",
  adjustment: "Ajuste",
  liability: "Obrigação"
};

const natureTone: Record<AccountNature, string> = {
  income: "bg-emerald-50 text-emerald-700 border-emerald-200",
  expense: "bg-rose-50 text-rose-700 border-rose-200",
  transfer: "bg-sky-50 text-sky-700 border-sky-200",
  reserve: "bg-violet-50 text-violet-700 border-violet-200",
  adjustment: "bg-amber-50 text-amber-700 border-amber-200",
  liability: "bg-slate-100 text-slate-700 border-slate-200"
};

export function ChartAccountsPage() {
  const queryClient = useQueryClient();
  const [selected, setSelected] = useState<ChartAccount | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [form, setForm] = useState<ChartAccountPayload>(emptyForm);
  const [formError, setFormError] = useState<string | null>(null);
  const list = useQuery({ queryKey: ["chart-accounts"], queryFn: () => chartAccountsService.list() });
  const tree = useQuery({ queryKey: ["chart-accounts-tree"], queryFn: chartAccountsService.tree });

  const rootCount = tree.data?.length ?? 0;
  const totalCount = list.data?.length ?? 0;

  useEffect(() => {
    if (selected) {
      setForm({
        code: selected.code,
        name: selected.name,
        parent_id: selected.parent_id,
        account_nature: selected.account_nature,
        is_active: selected.is_active
      });
    } else {
      setForm(emptyForm);
    }
    setFormError(null);
  }, [selected, formOpen]);

  const parentOptions = useMemo(() => (list.data ?? []).filter((item) => item.id !== selected?.id), [list.data, selected?.id]);

  const saveMutation = useMutation({
    mutationFn: () => (selected ? chartAccountsService.update(selected.id, form) : chartAccountsService.create(form)),
    onSuccess: () => {
      setSelected(null);
      setFormOpen(false);
      setFormError(null);
      queryClient.invalidateQueries({ queryKey: ["chart-accounts"] });
      queryClient.invalidateQueries({ queryKey: ["chart-accounts-tree"] });
    },
    onError: (error: unknown) => {
      const detail = getErrorDetail(error);
      setFormError(detail || "Erro ao salvar. Verifique os campos e tente novamente.");
    }
  });

  const seedMutation = useMutation({
    mutationFn: chartAccountsService.seedDefault,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chart-accounts"] });
      queryClient.invalidateQueries({ queryKey: ["chart-accounts-tree"] });
    }
  });

  const cleanupMutation = useMutation({
    mutationFn: chartAccountsService.cleanupDuplicates,
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["chart-accounts"] });
      queryClient.invalidateQueries({ queryKey: ["chart-accounts-tree"] });
      alert(result.removed_duplicates ? `${result.removed_duplicates} item(ns) duplicado(s) removido(s).` : "Nenhum item duplicado encontrado.");
    }
  });

  const deleteMutation = useMutation({
    mutationFn: chartAccountsService.remove,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chart-accounts"] });
      queryClient.invalidateQueries({ queryKey: ["chart-accounts-tree"] });
    },
    onError: (error: unknown) => {
      const detail = getErrorDetail(error);
      alert(detail || "Não foi possível apagar este item do plano de contas.");
    }
  });

  return (
    <div className="grid gap-6">
      <PageToolbar>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="text-sm font-black text-gray-950">Plano de contas</div>
            <div className="text-sm text-gray-500">{totalCount} contas em {rootCount} grupos principais.</div>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" icon={<Sparkles size={16} />} onClick={() => seedMutation.mutate()} disabled={seedMutation.isPending}>
              Popular padrão
            </Button>
            <Button variant="secondary" icon={<Wand2 size={16} />} onClick={() => cleanupMutation.mutate()} disabled={cleanupMutation.isPending}>
              Limpar duplicados
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

      {!tree.data?.length ? (
        <EmptyState
          title="Plano de contas vazio"
          description="Popule o plano padrão ou crie uma conta do plano manualmente."
          action={<Button icon={<Sparkles size={16} />} onClick={() => seedMutation.mutate()}>Popular plano padrão</Button>}
        />
      ) : (
        <section className="grid gap-3">
          {tree.data.map((item) => (
            <AccountAccordion
              key={item.id}
              item={item}
              onAddChild={(parent) => {
                setSelected(null);
                setForm({
                  code: `${parent.code}.`,
                  name: "",
                  parent_id: parent.id,
                  account_nature: parent.account_nature,
                  is_active: true
                });
                setFormOpen(true);
              }}
              onEdit={(chartAccount) => {
                setSelected(chartAccount);
                setFormOpen(true);
              }}
              onDelete={(id) => {
                if (confirm("Apagar este item do plano de contas? Ele e suas subcontas serão removidos das listas ativas, preservando o histórico já lançado.")) {
                  deleteMutation.mutate(id);
                }
              }}
            />
          ))}
        </section>
      )}

      {formOpen && (
        <Modal
          title={selected ? "Editar conta do plano" : "Nova conta do plano"}
          description="Use códigos hierárquicos, como 3.2 ou 6.1, para manter o plano organizado."
          onClose={() => {
            setSelected(null);
            setFormOpen(false);
            setFormError(null);
          }}
          footer={
            <>
              <Button type="button" variant="secondary" onClick={() => { setFormOpen(false); setFormError(null); }}>Cancelar</Button>
              <Button type="button" icon={<GitBranch size={16} />} onClick={() => saveMutation.mutate()} disabled={!form.code || !form.name || saveMutation.isPending}>
                {selected ? "Salvar alterações" : "Cadastrar"}
              </Button>
            </>
          }
        >
          {formError && (
            <div className="mb-3 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
              {formError}
            </div>
          )}
          <ChartAccountForm form={form} onChange={setForm} parentOptions={parentOptions} />
        </Modal>
      )}
    </div>
  );
}

function ChartAccountForm({
  form,
  onChange,
  parentOptions
}: {
  form: ChartAccountPayload;
  onChange: (form: ChartAccountPayload) => void;
  parentOptions: ChartAccount[];
}) {
  return (
    <div className="grid gap-3 md:grid-cols-2">
      <Input label="Código" value={form.code} onChange={(event) => onChange({ ...form, code: event.target.value })} required />
      <Input label="Nome" value={form.name} onChange={(event) => onChange({ ...form, name: event.target.value })} required />
      <Select label="Conta pai" value={form.parent_id ?? ""} onChange={(event) => onChange({ ...form, parent_id: event.target.value ? Number(event.target.value) : null })}>
        <option value="">Raiz</option>
        {parentOptions.map((item) => <option key={item.id} value={item.id}>{item.code} - {item.name}</option>)}
      </Select>
      <Select label="Natureza" value={form.account_nature} onChange={(event) => onChange({ ...form, account_nature: event.target.value })}>
        <option value="income">Receita</option>
        <option value="expense">Despesa</option>
        <option value="transfer">Transferência</option>
        <option value="reserve">Reserva</option>
        <option value="adjustment">Ajuste</option>
        <option value="liability">Obrigação</option>
      </Select>
      <label className="flex items-center gap-2 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-semibold text-gray-700 md:col-span-2">
        <input type="checkbox" checked={form.is_active} onChange={(event) => onChange({ ...form, is_active: event.target.checked })} />
        Conta ativa
      </label>
    </div>
  );
}

function AccountAccordion({
  item,
  onAddChild,
  onEdit,
  onDelete
}: {
  item: ChartAccountTree;
  onAddChild: (item: ChartAccountTree) => void;
  onEdit: (item: ChartAccount) => void;
  onDelete: (id: number) => void;
}) {
  const [open, setOpen] = useState(true);
  const childrenCount = countChildren(item);

  return (
    <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
      <button
        type="button"
        className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left hover:bg-gray-50"
        onClick={() => setOpen((value) => !value)}
      >
        <div className="flex min-w-0 items-center gap-3">
          <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-gray-100 text-gray-700">
            {open ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
          </span>
          <div className="min-w-0">
            <div className="truncate text-sm font-black text-gray-950">{item.code} - {item.name}</div>
            <div className="text-xs font-medium text-gray-500">{childrenCount} subcontas</div>
          </div>
        </div>
        <span className={`shrink-0 rounded-full border px-2 py-1 text-xs font-bold ${natureTone[item.account_nature]}`}>
          {natureLabel[item.account_nature]}
        </span>
      </button>

      {open && (
        <div className="border-t border-gray-200">
          <div className="flex flex-wrap items-center justify-between gap-2 bg-gray-50 px-4 py-2">
            <div className="text-xs font-bold uppercase text-gray-500">Grupo principal</div>
            <div className="flex gap-2">
              <Button title="Nova subconta" variant="secondary" icon={<Plus size={15} />} onClick={() => onAddChild(item)} />
              <Button title="Editar" variant="ghost" icon={<Edit3 size={15} />} onClick={() => onEdit(item)} />
              <Button title="Apagar" variant="ghost" icon={<Trash2 size={15} />} onClick={() => onDelete(item.id)} />
            </div>
          </div>
          {item.children.length > 0 ? (
            <div className="divide-y divide-gray-100">
              {item.children.map((child) => (
                <AccountRow
                  key={child.id}
                  item={child}
                  depth={1}
                  onAddChild={onAddChild}
                  onEdit={onEdit}
                  onDelete={onDelete}
                />
              ))}
            </div>
          ) : (
            <div className="px-4 py-5 text-sm text-gray-500">Nenhuma subconta neste grupo.</div>
          )}
        </div>
      )}
    </div>
  );
}

function AccountRow({
  item,
  depth,
  onAddChild,
  onEdit,
  onDelete
}: {
  item: ChartAccountTree;
  depth: number;
  onAddChild: (item: ChartAccountTree) => void;
  onEdit: (item: ChartAccount) => void;
  onDelete: (id: number) => void;
}) {
  const [open, setOpen] = useState(false);
  const hasChildren = item.children.length > 0;

  return (
    <div>
      <div className="flex items-center justify-between gap-3 px-4 py-2 hover:bg-gray-50" style={{ paddingLeft: `${16 + depth * 18}px` }}>
        <button type="button" className="flex min-w-0 flex-1 items-center gap-2 text-left" onClick={() => hasChildren && setOpen((value) => !value)}>
          <span className="grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-gray-100 text-gray-600">
            {hasChildren ? (open ? <ChevronDown size={16} /> : <ChevronRight size={16} />) : <GitBranch size={15} />}
          </span>
          <span className="min-w-0">
            <span className="block truncate text-sm font-bold text-gray-900">{item.code} - {item.name}</span>
            <span className="block text-xs text-gray-500">{natureLabel[item.account_nature]}</span>
          </span>
        </button>
        <div className="flex shrink-0 gap-1">
          <Button title="Nova subconta" variant="ghost" icon={<Plus size={15} />} onClick={() => onAddChild(item)} />
          <Button title="Editar" variant="ghost" icon={<Edit3 size={15} />} onClick={() => onEdit(item)} />
          <Button title="Apagar" variant="ghost" icon={<Trash2 size={15} />} onClick={() => onDelete(item.id)} />
        </div>
      </div>
      {hasChildren && open && (
        <div className="border-t border-gray-100">
          {item.children.map((child) => (
            <AccountRow
              key={child.id}
              item={child}
              depth={depth + 1}
              onAddChild={onAddChild}
              onEdit={onEdit}
              onDelete={onDelete}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function countChildren(item: ChartAccountTree): number {
  return item.children.reduce((total, child) => total + 1 + countChildren(child), 0);
}

function getErrorDetail(error: unknown): string | undefined {
  if (typeof error === "object" && error !== null && "response" in error) {
    const response = (error as { response?: { data?: { detail?: string } } }).response;
    return response?.data?.detail;
  }
  return undefined;
}
