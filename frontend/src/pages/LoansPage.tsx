import { AlertTriangle, Edit3, Link2, Plus, Power, Settings2, UserRound } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { EmptyState } from "../components/ui/EmptyState";
import { Input, Select } from "../components/ui/Input";
import { Modal } from "../components/ui/Modal";
import { PageToolbar } from "../components/ui/PageToolbar";
import { formatDateBR, money, todayISODate } from "../services/api";
import { chartAccountsService } from "../services/chartAccountsService";
import { loansService, type LoanLinkPayload, type LoanLossWriteoffPayload, type LoanPersonPayload } from "../services/loansService";
import type { ChartAccount } from "../types/chartAccount";
import type { LoanAccountLink, LoanMovementEffect, LoanPerson } from "../types/loan";

const emptyPerson: LoanPersonPayload = {
  name: "",
  document: "",
  phone: "",
  opening_balance: "0.00",
  notes: "",
  is_active: true
};

const emptyLink: LoanLinkPayload = {
  person_id: 0,
  chart_account_id: 0,
  effect: "increase",
  notes: "",
  is_active: true
};

const emptyLoss: LoanLossWriteoffPayload = {
  writeoff_date: todayISODate(),
  amount: "",
  notes: ""
};

const effectLabel: Record<LoanMovementEffect, string> = {
  increase: "Aumenta divida",
  decrease: "Abate divida"
};

export function LoansPage() {
  const queryClient = useQueryClient();
  const [activePersonId, setActivePersonId] = useState<number | null>(null);
  const [personOpen, setPersonOpen] = useState(false);
  const [selectedPerson, setSelectedPerson] = useState<LoanPerson | null>(null);
  const [personForm, setPersonForm] = useState<LoanPersonPayload>(emptyPerson);
  const [linkOpen, setLinkOpen] = useState(false);
  const [selectedLink, setSelectedLink] = useState<LoanAccountLink | null>(null);
  const [linkForm, setLinkForm] = useState<LoanLinkPayload>(emptyLink);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [lossOpen, setLossOpen] = useState(false);
  const [lossForm, setLossForm] = useState<LoanLossWriteoffPayload>(emptyLoss);
  const [lossChartAccountId, setLossChartAccountId] = useState<number | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const people = useQuery({ queryKey: ["loan-people"], queryFn: () => loansService.people(true) });
  const links = useQuery({ queryKey: ["loan-links"], queryFn: () => loansService.links(undefined, true) });
  const chartAccounts = useQuery({ queryKey: ["chart-accounts"], queryFn: () => chartAccountsService.list() });
  const settings = useQuery({ queryKey: ["loan-settings"], queryFn: loansService.settings });
  const movements = useQuery({
    queryKey: ["loan-movements", activePersonId],
    queryFn: () => loansService.movements(activePersonId!),
    enabled: Boolean(activePersonId)
  });

  const activePerson = useMemo(
    () => (people.data ?? []).find((person) => person.id === activePersonId) ?? null,
    [activePersonId, people.data]
  );

  const activeLinks = useMemo(
    () => (links.data ?? []).filter((link) => link.person_id === activePersonId),
    [activePersonId, links.data]
  );

  const linkedChartAccountIds = useMemo(() => {
    return new Set(
      (links.data ?? [])
        .filter((link) => link.is_active && link.id !== selectedLink?.id)
        .map((link) => link.chart_account_id)
    );
  }, [links.data, selectedLink?.id]);

  const chartAccountOptions = useMemo(
    () => (chartAccounts.data ?? []).filter((item) => item.is_active && !linkedChartAccountIds.has(item.id)),
    [chartAccounts.data, linkedChartAccountIds]
  );

  const totals = useMemo(() => {
    return (people.data ?? []).reduce(
      (acc, person) => {
        if (!person.is_active) return acc;
        const balance = Number(person.current_balance);
        acc.open += Math.max(balance, 0);
        acc.credit += Math.max(-balance, 0);
        acc.people += 1;
        return acc;
      },
      { open: 0, credit: 0, people: 0 }
    );
  }, [people.data]);

  useEffect(() => {
    if (!activePersonId && people.data?.length) {
      setActivePersonId(people.data[0].id);
    }
  }, [activePersonId, people.data]);

  useEffect(() => {
    setPersonForm(
      selectedPerson
        ? {
            name: selectedPerson.name,
            document: selectedPerson.document ?? "",
            phone: selectedPerson.phone ?? "",
            opening_balance: selectedPerson.opening_balance,
            notes: selectedPerson.notes ?? "",
            is_active: selectedPerson.is_active
          }
        : emptyPerson
    );
  }, [selectedPerson, personOpen]);

  useEffect(() => {
    setLinkForm(
      selectedLink
        ? {
            person_id: selectedLink.person_id,
            chart_account_id: selectedLink.chart_account_id,
            effect: selectedLink.effect,
            notes: selectedLink.notes ?? "",
            is_active: selectedLink.is_active
          }
        : { ...emptyLink, person_id: activePersonId ?? 0 }
    );
  }, [selectedLink, linkOpen, activePersonId]);

  useEffect(() => {
    setLossChartAccountId(settings.data?.loss_chart_account_id ?? null);
  }, [settings.data?.loss_chart_account_id, settingsOpen]);

  function invalidateLoans() {
    queryClient.invalidateQueries({ queryKey: ["loan-people"] });
    queryClient.invalidateQueries({ queryKey: ["loan-links"] });
    queryClient.invalidateQueries({ queryKey: ["loan-movements"] });
    queryClient.invalidateQueries({ queryKey: ["loan-settings"] });
    queryClient.invalidateQueries({ queryKey: ["chart-accounts"] });
    queryClient.invalidateQueries({ queryKey: ["dashboard-widgets"] });
    queryClient.invalidateQueries({ queryKey: ["report-indicator-evaluations"] });
  }

  const savePersonMutation = useMutation({
    mutationFn: () =>
      selectedPerson
        ? loansService.updatePerson(selectedPerson.id, normalizePersonPayload(personForm))
        : loansService.createPerson(normalizePersonPayload(personForm)),
    onSuccess: (person) => {
      setActivePersonId(person.id);
      setSelectedPerson(null);
      setPersonOpen(false);
      setFormError(null);
      invalidateLoans();
    },
    onError: (error: unknown) => setFormError(getErrorDetail(error) ?? "Nao foi possivel salvar.")
  });

  const deactivatePersonMutation = useMutation({
    mutationFn: loansService.deactivatePerson,
    onSuccess: () => {
      setActivePersonId(null);
      invalidateLoans();
    }
  });

  const saveLinkMutation = useMutation({
    mutationFn: () =>
      selectedLink
        ? loansService.updateLink(selectedLink.id, normalizeLinkPayload(linkForm))
        : loansService.createLink(normalizeLinkPayload(linkForm)),
    onSuccess: () => {
      setSelectedLink(null);
      setLinkOpen(false);
      setFormError(null);
      invalidateLoans();
    },
    onError: (error: unknown) => setFormError(getErrorDetail(error) ?? "Nao foi possivel salvar o vinculo.")
  });

  const deactivateLinkMutation = useMutation({
    mutationFn: loansService.deactivateLink,
    onSuccess: () => invalidateLoans()
  });

  const saveSettingsMutation = useMutation({
    mutationFn: () => loansService.updateSettings({ loss_chart_account_id: lossChartAccountId }),
    onSuccess: () => {
      setSettingsOpen(false);
      setFormError(null);
      invalidateLoans();
    },
    onError: (error: unknown) => setFormError(getErrorDetail(error) ?? "Nao foi possivel salvar a classificacao de perda.")
  });

  const createLossMutation = useMutation({
    mutationFn: () => {
      if (!activePersonId) throw new Error("Pessoa obrigatoria");
      return loansService.createLoss(activePersonId, normalizeLossPayload(lossForm));
    },
    onSuccess: () => {
      setLossOpen(false);
      setLossForm(emptyLoss);
      setFormError(null);
      invalidateLoans();
    },
    onError: (error: unknown) => setFormError(getErrorDetail(error) ?? "Nao foi possivel baixar a perda.")
  });

  return (
    <div className="grid gap-6">
      <PageToolbar>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="text-sm font-black text-gray-950">Emprestimos</div>
            <div className="grid gap-2 pt-2 text-sm text-gray-600 sm:grid-cols-3">
              <span className="rounded-lg bg-white px-3 py-2 font-bold text-gray-900">Pessoas: {totals.people}</span>
              <span className="rounded-lg bg-white px-3 py-2 font-bold text-emerald-700">A receber: {money(totals.open)}</span>
              <span className="rounded-lg bg-white px-3 py-2 font-bold text-sky-700">Credito: {money(totals.credit)}</span>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="secondary"
              icon={<Link2 size={16} />}
              disabled={!activePersonId}
              onClick={() => {
                setSelectedLink(null);
                setLinkOpen(true);
              }}
            >
              Vincular plano
            </Button>
            <Button
              variant="ghost"
              title="Configurar classificacao de perda"
              icon={<Settings2 size={16} />}
              onClick={() => setSettingsOpen(true)}
            />
            <Button
              icon={<Plus size={16} />}
              onClick={() => {
                setSelectedPerson(null);
                setPersonOpen(true);
              }}
            >
              Nova pessoa
            </Button>
          </div>
        </div>
      </PageToolbar>

      {!people.data?.length ? (
        <EmptyState
          title="Nenhum emprestimo cadastrado"
          description="Cadastre uma pessoa para acompanhar valores emprestados e pagamentos."
          action={<Button icon={<Plus size={16} />} onClick={() => setPersonOpen(true)}>Cadastrar pessoa</Button>}
        />
      ) : (
        <div className="grid gap-6 xl:grid-cols-[0.9fr_1.4fr]">
          <section className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
            <div className="border-b border-gray-200 bg-gray-50 px-4 py-3 text-xs font-bold uppercase text-gray-500">Pessoas</div>
            <div className="divide-y divide-gray-100">
              {(people.data ?? []).map((person) => (
                <button
                  key={person.id}
                  type="button"
                  className={`grid w-full gap-2 px-4 py-3 text-left hover:bg-gray-50 ${person.id === activePersonId ? "bg-emerald-50" : ""}`}
                  onClick={() => setActivePersonId(person.id)}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="font-black text-gray-950">{person.name}</div>
                      <div className="text-xs text-gray-500">{person.linked_accounts_count} vinculo(s) no plano</div>
                    </div>
                    <Badge value={person.is_active ? "ativo" : "inativo"} />
                  </div>
                  <div className={`text-xl font-black ${balanceTone(person.current_balance)}`}>{money(person.current_balance)}</div>
                </button>
              ))}
            </div>
          </section>

          <section className="grid gap-4">
            {activePerson && (
              <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2 text-lg font-black text-gray-950">
                      <UserRound size={20} />
                      {activePerson.name}
                    </div>
                    <div className="mt-1 text-sm text-gray-500">{activePerson.document || "Sem documento"} {activePerson.phone ? `| ${activePerson.phone}` : ""}</div>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="ghost"
                      title="Baixar valor perdido"
                      icon={<AlertTriangle size={15} />}
                      disabled={Number(activePerson.current_balance) <= 0}
                      onClick={() => {
                        setLossForm({ ...emptyLoss, amount: Math.max(Number(activePerson.current_balance), 0).toFixed(2) });
                        setLossOpen(true);
                      }}
                    />
                    <Button
                      variant="secondary"
                      icon={<Edit3 size={16} />}
                      onClick={() => {
                        setSelectedPerson(activePerson);
                        setPersonOpen(true);
                      }}
                    >
                      Editar
                    </Button>
                    <Button variant="ghost" icon={<Power size={16} />} onClick={() => deactivatePersonMutation.mutate(activePerson.id)}>
                      Desativar
                    </Button>
                  </div>
                </div>

                <div className="mt-4 grid gap-3 md:grid-cols-4">
                  <Metric label="Saldo inicial" value={money(activePerson.opening_balance)} />
                  <Metric label="Acrescimos" value={money(activePerson.movement_increase_total)} />
                  <Metric label="Abatimentos" value={money(activePerson.movement_decrease_total)} />
                  <Metric label="Saldo atual" value={money(activePerson.current_balance)} tone={balanceTone(activePerson.current_balance)} />
                </div>
              </div>
            )}

            <div className="rounded-xl border border-gray-200 bg-white shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-gray-200 px-4 py-3">
                <div className="text-sm font-black text-gray-950">Vinculos do plano</div>
                <Button
                  variant="secondary"
                  icon={<Link2 size={16} />}
                  disabled={!activePersonId}
                  onClick={() => {
                    setSelectedLink(null);
                    setLinkOpen(true);
                  }}
                >
                  Novo vinculo
                </Button>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 text-sm">
                  <thead className="bg-gray-100 text-left text-xs font-bold uppercase text-gray-600">
                    <tr>
                      <th className="px-3 py-3">Plano</th>
                      <th className="px-3 py-3">Efeito</th>
                      <th className="px-3 py-3">Status</th>
                      <th className="px-3 py-3 text-right">Acoes</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {activeLinks.map((link) => (
                      <tr key={link.id} className="hover:bg-gray-50">
                        <td className="px-3 py-3">
                          <div className="font-bold text-gray-950">{link.chart_account_code} - {link.chart_account_name}</div>
                          {link.notes && <div className="text-xs text-gray-500">{link.notes}</div>}
                        </td>
                        <td className="px-3 py-3">{effectLabel[link.effect]}</td>
                        <td className="px-3 py-3"><Badge value={link.is_active ? "ativo" : "inativo"} /></td>
                        <td className="px-3 py-3 text-right">
                          <div className="flex justify-end gap-2">
                            <Button
                              title="Editar"
                              variant="secondary"
                              icon={<Edit3 size={16} />}
                              onClick={() => {
                                setSelectedLink(link);
                                setLinkOpen(true);
                              }}
                            />
                            <Button title="Desativar" variant="ghost" icon={<Power size={16} />} onClick={() => deactivateLinkMutation.mutate(link.id)} />
                          </div>
                        </td>
                      </tr>
                    ))}
                    {!activeLinks.length && (
                      <tr>
                        <td className="px-3 py-8 text-center text-gray-500" colSpan={4}>Nenhum vinculo cadastrado.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="rounded-xl border border-gray-200 bg-white shadow-sm">
              <div className="border-b border-gray-200 px-4 py-3 text-sm font-black text-gray-950">Movimentos</div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 text-sm">
                  <thead className="bg-gray-100 text-left text-xs font-bold uppercase text-gray-600">
                    <tr>
                      <th className="px-3 py-3">Data</th>
                      <th className="px-3 py-3">Lancamento</th>
                      <th className="px-3 py-3">Plano</th>
                      <th className="px-3 py-3 text-right">Movimento</th>
                      <th className="px-3 py-3 text-right">Saldo</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {(movements.data ?? []).map((movement) => (
                      <tr key={movement.transaction_id ?? `loss-${movement.writeoff_id}`} className="hover:bg-gray-50">
                        <td className="whitespace-nowrap px-3 py-3">{formatDateBR(movement.transaction_date)}</td>
                        <td className="px-3 py-3">
                          <div className="font-bold text-gray-950">{movement.description}</div>
                          <div className="text-xs text-gray-500">{movement.movement_kind === "loss" ? "Baixa por perda" : movement.account_name}</div>
                        </td>
                        <td className="px-3 py-3">{movement.chart_account_code} - {movement.chart_account_name}</td>
                        <td className={`whitespace-nowrap px-3 py-3 text-right font-bold ${balanceTone(movement.debt_delta)}`}>
                          {money(movement.debt_delta)}
                        </td>
                        <td className={`whitespace-nowrap px-3 py-3 text-right font-black ${balanceTone(movement.balance_after)}`}>
                          {money(movement.balance_after)}
                        </td>
                      </tr>
                    ))}
                    {!(movements.data ?? []).length && (
                      <tr>
                        <td className="px-3 py-8 text-center text-gray-500" colSpan={5}>Nenhum movimento encontrado.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </section>
        </div>
      )}

      {personOpen && (
        <Modal
          title={selectedPerson ? "Editar pessoa" : "Nova pessoa"}
          onClose={() => {
            setSelectedPerson(null);
            setPersonOpen(false);
            setFormError(null);
          }}
          footer={
            <>
              <Button type="button" variant="secondary" onClick={() => setPersonOpen(false)}>Cancelar</Button>
              <Button type="button" disabled={!personForm.name || savePersonMutation.isPending} onClick={() => savePersonMutation.mutate()}>
                {selectedPerson ? "Salvar" : "Cadastrar"}
              </Button>
            </>
          }
        >
          {formError && <div className="mb-3 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{formError}</div>}
          <PersonForm value={personForm} onChange={setPersonForm} />
        </Modal>
      )}

      {linkOpen && (
        <Modal
          title={selectedLink ? "Editar vinculo" : "Novo vinculo"}
          onClose={() => {
            setSelectedLink(null);
            setLinkOpen(false);
            setFormError(null);
          }}
          footer={
            <>
              <Button type="button" variant="secondary" onClick={() => setLinkOpen(false)}>Cancelar</Button>
              <Button type="button" disabled={!linkForm.person_id || !linkForm.chart_account_id || saveLinkMutation.isPending} onClick={() => saveLinkMutation.mutate()}>
                {selectedLink ? "Salvar" : "Vincular"}
              </Button>
            </>
          }
        >
          {formError && <div className="mb-3 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{formError}</div>}
          <LinkForm
            value={linkForm}
            onChange={setLinkForm}
            people={people.data ?? []}
            chartAccounts={chartAccountOptions}
            selectedLink={selectedLink}
          />
        </Modal>
      )}

      {settingsOpen && (
        <Modal
          title="Classificacao de perda"
          description="Essa classificacao e unica para todos os emprestimos. Use uma conta de despesa, como 3.10 - Perdas com emprestimos."
          onClose={() => {
            setSettingsOpen(false);
            setFormError(null);
          }}
          footer={
            <>
              <Button type="button" variant="secondary" onClick={() => setSettingsOpen(false)}>Cancelar</Button>
              <Button type="button" disabled={!lossChartAccountId || saveSettingsMutation.isPending} onClick={() => saveSettingsMutation.mutate()}>
                Salvar
              </Button>
            </>
          }
        >
          {formError && <div className="mb-3 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{formError}</div>}
          <Select
            label="Classificacao para perdas"
            value={lossChartAccountId ?? ""}
            onChange={(event) => setLossChartAccountId(event.target.value ? Number(event.target.value) : null)}
          >
            <option value="">Selecione uma despesa</option>
            {(chartAccounts.data ?? [])
              .filter((account) => account.account_nature === "expense")
              .map((account) => <option key={account.id} value={account.id}>{account.code} - {account.name}</option>)}
          </Select>
        </Modal>
      )}

      {lossOpen && activePerson && (
        <Modal
          title="Baixar valor perdido"
          description="Use apenas quando o valor nao sera mais recebido. Isso reduz a divida da pessoa e registra a perda na classificacao configurada."
          onClose={() => {
            setLossOpen(false);
            setFormError(null);
          }}
          footer={
            <>
              <Button type="button" variant="secondary" onClick={() => setLossOpen(false)}>Cancelar</Button>
              <Button type="button" disabled={!lossForm.amount || createLossMutation.isPending} onClick={() => createLossMutation.mutate()}>
                Confirmar perda
              </Button>
            </>
          }
        >
          {formError && <div className="mb-3 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{formError}</div>}
          <div className="mb-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm font-semibold text-amber-800">
            Classificacao: {settings.data?.loss_chart_account_code ? `${settings.data.loss_chart_account_code} - ${settings.data.loss_chart_account_name}` : "configure antes de baixar"}
          </div>
          <LossForm value={lossForm} maxAmount={activePerson.current_balance} onChange={setLossForm} />
        </Modal>
      )}
    </div>
  );
}

function Metric({ label, value, tone = "text-gray-950" }: { label: string; value: string; tone?: string }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-gray-50 px-3 py-2">
      <div className="text-xs font-bold uppercase text-gray-500">{label}</div>
      <div className={`mt-1 text-lg font-black ${tone}`}>{value}</div>
    </div>
  );
}

function PersonForm({ value, onChange }: { value: LoanPersonPayload; onChange: (value: LoanPersonPayload) => void }) {
  return (
    <div className="grid gap-3 md:grid-cols-2">
      <Input label="Nome" value={value.name} onChange={(event) => onChange({ ...value, name: event.target.value })} required />
      <Input label="Saldo inicial" type="number" step="0.01" value={value.opening_balance} onChange={(event) => onChange({ ...value, opening_balance: event.target.value })} />
      <Input label="Documento" value={value.document ?? ""} onChange={(event) => onChange({ ...value, document: event.target.value })} />
      <Input label="Telefone" value={value.phone ?? ""} onChange={(event) => onChange({ ...value, phone: event.target.value })} />
      <label className="flex items-center gap-2 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-semibold text-gray-700 md:col-span-2">
        <input type="checkbox" checked={value.is_active} onChange={(event) => onChange({ ...value, is_active: event.target.checked })} />
        Pessoa ativa
      </label>
      <label className="grid gap-1 text-sm font-medium text-gray-700 md:col-span-2">
        <span>Observacoes</span>
        <textarea
          className="min-h-24 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
          value={value.notes ?? ""}
          onChange={(event) => onChange({ ...value, notes: event.target.value })}
        />
      </label>
    </div>
  );
}

function LinkForm({
  value,
  onChange,
  people,
  chartAccounts,
  selectedLink
}: {
  value: LoanLinkPayload;
  onChange: (value: LoanLinkPayload) => void;
  people: LoanPerson[];
  chartAccounts: ChartAccount[];
  selectedLink: LoanAccountLink | null;
}) {
  const selectedChartStillAvailable = selectedLink
    ? [{ id: selectedLink.chart_account_id, code: selectedLink.chart_account_code ?? "", name: selectedLink.chart_account_name ?? "", parent_id: null, account_nature: "expense", is_active: true, created_at: "", updated_at: "" } as ChartAccount]
    : [];
  const options = selectedLink ? [...selectedChartStillAvailable, ...chartAccounts.filter((item) => item.id !== selectedLink.chart_account_id)] : chartAccounts;

  return (
    <div className="grid gap-3 md:grid-cols-2">
      <Select label="Pessoa" value={value.person_id || ""} onChange={(event) => onChange({ ...value, person_id: Number(event.target.value) })} required>
        <option value="">Selecione</option>
        {people.map((person) => <option key={person.id} value={person.id}>{person.name}</option>)}
      </Select>
      <Select label="Efeito" value={value.effect} onChange={(event) => onChange({ ...value, effect: event.target.value as LoanMovementEffect })}>
        <option value="increase">Aumenta divida</option>
        <option value="decrease">Abate divida</option>
      </Select>
      <Select label="Plano de contas" value={value.chart_account_id || ""} onChange={(event) => onChange({ ...value, chart_account_id: Number(event.target.value) })} required>
        <option value="">Selecione</option>
        {options.map((item) => <option key={item.id} value={item.id}>{item.code} - {item.name}</option>)}
      </Select>
      <label className="flex items-center gap-2 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-semibold text-gray-700">
        <input type="checkbox" checked={value.is_active} onChange={(event) => onChange({ ...value, is_active: event.target.checked })} />
        Vinculo ativo
      </label>
      <label className="grid gap-1 text-sm font-medium text-gray-700 md:col-span-2">
        <span>Observacoes</span>
        <textarea
          className="min-h-24 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
          value={value.notes ?? ""}
          onChange={(event) => onChange({ ...value, notes: event.target.value })}
        />
      </label>
    </div>
  );
}

function LossForm({
  value,
  maxAmount,
  onChange
}: {
  value: LoanLossWriteoffPayload;
  maxAmount: string;
  onChange: (value: LoanLossWriteoffPayload) => void;
}) {
  return (
    <div className="grid gap-3 md:grid-cols-2">
      <Input label="Data da perda" type="date" value={value.writeoff_date} onChange={(event) => onChange({ ...value, writeoff_date: event.target.value })} />
      <Input label={`Valor perdido (max. ${money(maxAmount)})`} type="number" step="0.01" min="0" value={value.amount} onChange={(event) => onChange({ ...value, amount: event.target.value })} />
      <label className="grid gap-1 text-sm font-medium text-gray-700 md:col-span-2">
        <span>Observacoes</span>
        <textarea
          className="min-h-20 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
          value={value.notes ?? ""}
          onChange={(event) => onChange({ ...value, notes: event.target.value })}
        />
      </label>
    </div>
  );
}

function normalizePersonPayload(value: LoanPersonPayload): LoanPersonPayload {
  return {
    ...value,
    document: value.document || null,
    phone: value.phone || null,
    notes: value.notes || null,
    opening_balance: value.opening_balance || "0.00"
  };
}

function normalizeLinkPayload(value: LoanLinkPayload): LoanLinkPayload {
  return {
    ...value,
    notes: value.notes || null
  };
}

function normalizeLossPayload(value: LoanLossWriteoffPayload): LoanLossWriteoffPayload {
  return {
    ...value,
    amount: value.amount || "0.00",
    notes: value.notes || null
  };
}

function balanceTone(value: string | number): string {
  const number = Number(value);
  if (number > 0) return "text-emerald-700";
  if (number < 0) return "text-sky-700";
  return "text-gray-700";
}

function getErrorDetail(error: unknown): string | undefined {
  if (typeof error === "object" && error !== null && "response" in error) {
    const response = (error as { response?: { data?: { detail?: string } } }).response;
    return response?.data?.detail;
  }
  return undefined;
}
