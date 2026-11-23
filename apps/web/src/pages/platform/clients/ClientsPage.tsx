import { useState } from 'react'
import { PageHeader } from '../../../components/layout/PageHeader.tsx'
import { ErrorState } from '../../../components/states/ErrorState.tsx'
import { LoadingState } from '../../../components/states/LoadingState.tsx'
import { StateMessage } from '../../../components/states/StateMessage.tsx'
import { DataTable } from '../../../components/ui/DataTable.tsx'
import { Icon } from '../../../components/ui/Icon.tsx'
import { Notice } from '../../../components/ui/Notice.tsx'
import { useAsync } from '../../../hooks/useAsync.ts'
import { dataClient } from '../../../services/client.ts'
import type { PlatformClient } from '../../../types/index.ts'
import { ClientKpis } from './ClientKpis.tsx'
import { clientColumns } from './clientColumns.tsx'
import { kpisOf, withFailing } from './clientsView.ts'
import { SupportPanel } from './SupportPanel.tsx'

// A página: busca os clientes e junta indicadores, tabela e o painel de suporte.
// Quem vê: Owner/Desenvolvedor da LexGroup e equipe RA. O menu já esconde o item; quem digitar o
// endereço sem poder recebe 403 do banco (api.list_clients) e cai na mensagem abaixo.
export function ClientsPage() {
    // A lista vem do Supabase; a contagem de fontes com falha, da API (registro de leituras). Falhou a
    // contagem = "Sem informação" (withFailing), a página abre do mesmo jeito.
    const { data, error } = useAsync(async () => {
        const [list, failing] = await Promise.all([
            dataClient.listClients(),
            dataClient.getFailingSources().catch(() => null),
        ])
        return withFailing(list, failing)
    }, [])
    const [notice, setNotice] = useState<string | null>(null)
    const [supportFor, setSupportFor] = useState<PlatformClient | null>(null)

    if (error?.status === 403) {
        return (
            <StateMessage icon="lock" title="Área da plataforma" alert>
                Esta página mostra todas as organizações da plataforma. Só Owner e Desenvolvedor da LexGroup (e a equipe
                RA) veem.
            </StateMessage>
        )
    }
    if (error) return <ErrorState error={error} />
    if (!data) return <LoadingState />

    function startSupport(reason: string) {
        setSupportFor(null)
        setNotice(
            `Sessão de suporte ainda não está disponível: precisa da API para o MFA e para registrar na auditoria (motivo: "${reason}").`,
        )
    }

    return (
        <>
            <PageHeader
                title="Clientes"
                badge={<span className="badge pro">Plataforma</span>}
                description="As operações que usam o LexHub. Só Owner e Desenvolvedor da LexGroup veem. O suporte nunca contorna o isolamento: só lê, com motivo, MFA e prazo."
                actions={
                    <button
                        className="btn btn-primary"
                        type="button"
                        onClick={() =>
                            setNotice(
                                'Criar organização ainda não está disponível: plano e unidades são definidos pela equipe RA.',
                            )
                        }
                    >
                        <Icon name="plus" size={16} />
                        Nova organização
                    </button>
                }
            />
            <div className="stack">
                {notice && <Notice message={notice} onClose={() => setNotice(null)} />}
                <ClientKpis kpis={kpisOf(data)} />
                <DataTable columns={clientColumns(setSupportFor)} rows={data.clients} rowKey={(c) => c.slug} />
                {supportFor && (
                    <SupportPanel
                        key={supportFor.slug}
                        orgName={supportFor.name}
                        onConfirm={startSupport}
                        onClose={() => setSupportFor(null)}
                    />
                )}
            </div>
        </>
    )
}
