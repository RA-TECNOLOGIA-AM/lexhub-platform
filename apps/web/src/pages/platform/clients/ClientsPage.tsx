import { useState } from 'react'
import { PageHeader } from '../../../components/layout/PageHeader.tsx'
import { ErrorState } from '../../../components/states/ErrorState.tsx'
import { LoadingState } from '../../../components/states/LoadingState.tsx'
import { StateMessage } from '../../../components/states/StateMessage.tsx'
import { DataTable } from '../../../components/ui/DataTable.tsx'
import { Icon } from '../../../components/ui/Icon.tsx'
import { Notice } from '../../../components/ui/Notice.tsx'
import { useAuth } from '../../../contexts/auth-context.ts'
import { useAsync } from '../../../hooks/useAsync.ts'
import { dataClient } from '../../../services/client.ts'
import type { PlatformClient } from '../../../types/index.ts'
import { ClientKpis } from './ClientKpis.tsx'
import { clientColumns } from './clientColumns.tsx'
import { kpisOf } from './clientsView.ts'
import { SupportPanel } from './SupportPanel.tsx'

// Porteiro da página: só a equipe RA (platformStaff) entra. O menu já esconde o item,
// mas quem digitar o endereço cai aqui. A API também barra (403).
export function ClientsPage() {
    const { me } = useAuth()
    if (!me?.user.platformStaff) {
        return (
            <StateMessage icon="lock" title="Área da equipe RA Tecnologia" alert>
                Esta página mostra todas as organizações da plataforma e é só para a equipe RA.
            </StateMessage>
        )
    }
    return <ClientsContent />
}

// A página em si: busca os clientes e junta indicadores, tabela e o painel de suporte.
function ClientsContent() {
    const { data, error } = useAsync(() => dataClient.listClients(), [])
    const [notice, setNotice] = useState<string | null>(null)
    const [supportFor, setSupportFor] = useState<PlatformClient | null>(null)

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
                description="Visível só para a equipe RA Tecnologia. O suporte nunca contorna o isolamento: só lê, com motivo, MFA e prazo."
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
