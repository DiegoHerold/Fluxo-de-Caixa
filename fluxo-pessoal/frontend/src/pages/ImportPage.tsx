import { RotateCcw, Trash2, Upload } from "lucide-react";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AccountForm } from "../components/forms/AccountForm";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { EmptyState } from "../components/ui/EmptyState";
import { Modal } from "../components/ui/Modal";
import { Select } from "../components/ui/Input";
import { PageToolbar } from "../components/ui/PageToolbar";
import { formatDateTimeBR } from "../services/api";
import { accountsService } from "../services/accountsService";
import { importsService, type ImportSource } from "../services/importsService";

export function ImportPage() {
  const queryClient = useQueryClient();
  const accounts = useQuery({ queryKey: ["accounts"], queryFn: accountsService.list });
  const imports = useQuery({ queryKey: ["imports"], queryFn: importsService.list });
  const [accountId, setAccountId] = useState("");
  const [source, setSource] = useState<ImportSource>("nubank-csv");
  const [file, setFile] = useState<File | null>(null);
  const [accountModalOpen, setAccountModalOpen] = useState(false);
  const hasMatchingAccount = (accounts.data ?? []).some((account) => {
    const text = `${account.name} ${account.institution ?? ""}`.toLowerCase();
    return text.includes(suggestedInstitution(source).toLowerCase());
  });

  const uploadMutation = useMutation({
    mutationFn: () => importsService.upload(source, Number(accountId), file!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["imports"] });
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["pending-transactions"] });
      queryClient.invalidateQueries({ queryKey: ["account-balances"] });
      queryClient.invalidateQueries({ queryKey: ["consolidated-balance"] });
      queryClient.invalidateQueries({ queryKey: ["reserves"] });
    }
  });

  const createAccountMutation = useMutation({
    mutationFn: accountsService.create,
    onSuccess: (account) => {
      setAccountId(String(account.id));
      setAccountModalOpen(false);
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      queryClient.invalidateQueries({ queryKey: ["account-balances"] });
    }
  });

  const removeMutation = useMutation({
    mutationFn: importsService.remove,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["imports"] });
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["pending-transactions"] });
      queryClient.invalidateQueries({ queryKey: ["account-balances"] });
      queryClient.invalidateQueries({ queryKey: ["consolidated-balance"] });
      queryClient.invalidateQueries({ queryKey: ["reserves"] });
    }
  });

  return (
    <div className="grid gap-6">
      <PageToolbar>
        <form
          className="grid gap-3 md:grid-cols-[1fr_1fr_1.2fr_auto]"
          onSubmit={(event) => {
            event.preventDefault();
            if (!accountId) {
              setAccountModalOpen(true);
              return;
            }
            if (file) uploadMutation.mutate();
          }}
        >
          <Select label="Conta" value={accountId} onChange={(event) => setAccountId(event.target.value)} required>
            <option value="">Selecione</option>
            {accounts.data?.map((account) => (
              <option key={account.id} value={account.id}>{account.name}</option>
            ))}
          </Select>
          <Select label="Extrato" value={source} onChange={(event) => setSource(event.target.value as ImportSource)}>
            <option value="nubank-csv">Nubank CSV</option>
            <option value="nubank-ofx">Nubank OFX</option>
            <option value="mercado-pago-xlsx">Mercado Pago XLSX</option>
          </Select>
          <label className="grid gap-1 text-sm font-medium text-gray-700">
            <span>Arquivo</span>
            <input className="min-h-10 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm" type="file" onChange={(event) => setFile(event.target.files?.[0] ?? null)} required />
          </label>
          <div className="flex items-end">
            <Button className="w-full" disabled={uploadMutation.isPending} icon={<Upload size={16} />}>Importar</Button>
          </div>
        </form>

        {!accounts.data?.length && (
          <div className="mt-3 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
            Nenhuma conta cadastrada. Crie uma conta para vincular este extrato antes de importar.
            <Button className="ml-3" type="button" variant="secondary" onClick={() => setAccountModalOpen(true)}>Criar conta</Button>
          </div>
        )}
        {Boolean(accounts.data?.length) && !hasMatchingAccount && (
          <div className="mt-3 rounded-xl border border-sky-200 bg-sky-50 p-3 text-sm text-sky-900">
            Não encontrei uma conta parecida com {suggestedInstitution(source)}. Você pode criar uma nova conta para manter os extratos separados.
            <Button className="ml-3" type="button" variant="secondary" onClick={() => setAccountModalOpen(true)}>Criar {suggestedAccountName(source)}</Button>
          </div>
        )}
      </PageToolbar>

      {uploadMutation.data && (
        <div className="grid gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900 md:grid-cols-4">
          <strong>Importadas: {uploadMutation.data.imported_rows}</strong>
          <span>Duplicadas: {uploadMutation.data.duplicated_rows}</span>
          <span>Pendentes: {uploadMutation.data.pending_rows}</span>
          <span>Automáticas: {uploadMutation.data.automatic_rows}</span>
        </div>
      )}

      {!imports.data?.length ? (
        <EmptyState title="Nenhum lote importado" description="Importe um extrato para começar a classificar as movimentações." />
      ) : (
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-100 text-left text-xs font-bold uppercase text-gray-600">
                <tr>
                  <th className="px-3 py-3">Arquivo</th>
                  <th className="px-3 py-3">Fonte</th>
                  <th className="px-3 py-3">Período</th>
                  <th className="px-3 py-3 text-right">Linhas</th>
                  <th className="px-3 py-3">Status</th>
                  <th className="px-3 py-3 text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {imports.data?.map((batch) => (
                  <tr key={batch.id} className="hover:bg-gray-50">
                    <td className="px-3 py-3">
                      <div className="font-bold text-gray-950">{batch.filename}</div>
                      <div className="text-xs text-gray-500">Importado em {formatDateTimeBR(batch.imported_at)}</div>
                    </td>
                    <td className="px-3 py-3">{batch.source_bank} .{batch.file_type}</td>
                    <td className="px-3 py-3">{batch.period_start ?? "-"} até {batch.period_end ?? "-"}</td>
                    <td className="px-3 py-3 text-right">{batch.imported_rows}/{batch.total_rows}</td>
                    <td className="px-3 py-3"><Badge value={batch.status} /></td>
                    <td className="px-3 py-3 text-right">
                      <Button
                        title="Desfazer importação"
                        variant="ghost"
                        icon={<Trash2 size={16} />}
                        onClick={() => {
                          if (confirm("Desfazer esta importação e apagar as movimentações importadas por ela?")) {
                            removeMutation.mutate(batch.id);
                          }
                        }}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="rounded-xl border border-gray-200 bg-white p-4 text-sm text-gray-600 shadow-sm">
        <div className="flex items-center gap-2 font-bold text-gray-900">
          <RotateCcw size={16} />
          Reimportação segura
        </div>
        <p className="mt-1">O fingerprint impede duplicidade quando o mesmo extrato é enviado mais de uma vez.</p>
      </div>

      {accountModalOpen && (
        <Modal
          title="Criar conta para este extrato"
          description="Depois de criada, a conta fica selecionada automaticamente para importar o arquivo."
          onClose={() => setAccountModalOpen(false)}
        >
          <AccountForm
            defaults={{
              name: suggestedAccountName(source),
              institution: suggestedInstitution(source),
              account_type: source === "mercado-pago-xlsx" ? "wallet" : "checking"
            }}
            onSubmit={(payload) =>
              createAccountMutation.mutate({
                ...payload,
                name: payload.name || suggestedAccountName(source),
                institution: payload.institution || suggestedInstitution(source)
              })
            }
          />
        </Modal>
      )}
    </div>
  );
}

function suggestedInstitution(source: ImportSource): string {
  if (source.startsWith("nubank")) return "Nubank";
  return "Mercado Pago";
}

function suggestedAccountName(source: ImportSource): string {
  if (source === "mercado-pago-xlsx") return "Mercado Pago";
  return "Nubank";
}
