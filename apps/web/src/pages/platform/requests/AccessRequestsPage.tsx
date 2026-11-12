import { useState } from 'react'
import { useSearchParams } from 'react-router'
import { PageHeader } from '../../../components/layout/PageHeader.tsx'
import { ErrorState } from '../../../components/states/ErrorState.tsx'
import { LoadingState } from '../../../components/states/LoadingState.tsx'
import { StateMessage } from '../../../components/states/StateMessage.tsx'
import { DataTable } from '../../../components/ui/DataTable.tsx'
import { Notice } from '../../../components/ui/Notice.tsx'
import { PillGroup } from '../../../components/ui/PillGroup.tsx'
import { useAuth } from '../../../contexts/auth-context.ts'
import { useAsync } from '../../../hooks/useAsync.ts'
import { refreshPendingRequests } from '../../../hooks/usePendingRequests.ts'
import { dataClient } from '../../../services/client.ts'
import type { AccessRequest, ApprovalTarget } from '../../../types/index.ts'
import { ApprovePanel } from './ApprovePanel.tsx'
import { RejectPanel } from './RejectPanel.tsx'
import { requestColumns } from './requestColumns.tsx'

// Porteiro da página: só a equipe RA (platform_staff) entra. O menu já esconde o item;
// as funções do banco também barram (403).
export function AccessRequestsPage() {
    const { me } = useAuth()
    if (!me?.user.platform_staff) {
        return (
            <StateMessage icon="lock" title="Área da equipe RA Tecnologia" alert>
                Os pedidos de acesso são aprovados só pela equipe RA.
            </StateMessage>
        )
    }
    return <RequestsContent />
}

type Panel = { kind: 'approve' | 'reject'; request: AccessRequest } | null

// A página em si: abas Pendentes/Decididos (na URL), a tabela e os painéis de aprovar e recusar.
function RequestsContent() {
    const [params] = useSearchParams()
    const tab = params.get('aba') === 'decididos' ? 'decided' : 'pending'
    const [version, setVersion] = useState(0) // mudar = buscar de novo (depois de uma decisão)
    const { data, error } = useAsync(
        () => Promise.all([dataClient.listAccessRequests(tab), dataClient.getApprovalOptions()]),
        [tab, version],
    )
    const [panel, setPanel] = useState<Panel>(null)
    const [notice, setNotice] = useState<string | null>(null)

    if (error) return <ErrorState error={error} />
    if (!data) return <LoadingState />
    const [requests, orgs] = data

    // Depois de decidir: fecha o painel, avisa, busca a lista e o selo de novo.
    function decided(message: string) {
        setPanel(null)
        setNotice(message)
        setVersion((v) => v + 1)
        void refreshPendingRequests()
    }

    async function approve(request: AccessRequest, target: ApprovalTarget) {
        await dataClient.approveAccessRequest(request.id, target) // erro: o painel mostra
        const where = target.kind === 'new' ? `na organização nova "${target.name}"` : 'na organização escolhida'
        decided(`${request.full_name} foi aprovado(a) ${where}. No próximo "Verificar de novo", entra no LexHub.`)
    }

    async function reject(request: AccessRequest, note: string | null) {
        await dataClient.rejectAccessRequest(request.id, note)
        decided(`O pedido de ${request.full_name} foi recusado.`)
    }

    return (
        <>
            <PageHeader
                title="Pedidos de acesso"
                badge={<span className="badge pro">Plataforma</span>}
                description="Quem entrou (ex.: pelo Google) sem fazer parte de nenhuma organização e pediu acesso. Aprovar cria a associação; tudo fica na auditoria."
            />
            <div className="stack">
                {notice && <Notice message={notice} onClose={() => setNotice(null)} />}
                <PillGroup
                    label="Situação dos pedidos"
                    items={[
                        { id: 'pending', label: 'Pendentes', to: '?aba=pendentes', active: tab === 'pending' },
                        { id: 'decided', label: 'Decididos', to: '?aba=decididos', active: tab === 'decided' },
                    ]}
                />
                <div className="with-aside">
                    <div className="stack with-aside-main">
                        <DataTable
                            columns={
                                tab === 'pending'
                                    ? requestColumns({
                                          onApprove: (request) => setPanel({ kind: 'approve', request }),
                                          onReject: (request) => setPanel({ kind: 'reject', request }),
                                      })
                                    : requestColumns()
                            }
                            rows={requests}
                            rowKey={(r) => r.id}
                            empty={tab === 'pending' ? 'Nenhum pedido aguardando.' : 'Nenhum pedido decidido ainda.'}
                        />
                    </div>
                    {panel?.kind === 'approve' && (
                        <ApprovePanel
                            key={panel.request.id}
                            request={panel.request}
                            orgs={orgs}
                            onConfirm={(target) => approve(panel.request, target)}
                            onClose={() => setPanel(null)}
                        />
                    )}
                    {panel?.kind === 'reject' && (
                        <RejectPanel
                            key={panel.request.id}
                            request={panel.request}
                            onConfirm={(note) => reject(panel.request, note)}
                            onClose={() => setPanel(null)}
                        />
                    )}
                </div>
            </div>
        </>
    )
}
