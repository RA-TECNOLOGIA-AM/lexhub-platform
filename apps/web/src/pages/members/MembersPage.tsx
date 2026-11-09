import { useState } from 'react'
import { useParams, useSearchParams } from 'react-router'
import { useAuth } from '../../auth/auth-context.ts'
import { DataTable } from '../../components/DataTable.tsx'
import { Icon } from '../../components/Icon.tsx'
import { PageHeader } from '../../components/PageHeader.tsx'
import { ErrorState } from '../../components/states/ErrorState.tsx'
import { LoadingState } from '../../components/states/LoadingState.tsx'
import { dataClient } from '../../data/client.ts'
import type { InviteRequest } from '../../data/types.ts'
import { useAsync } from '../../hooks/useAsync.ts'
import { InvitePanel } from './InvitePanel.tsx'
import { MEMBER_COLUMNS } from './memberColumns.tsx'
import { MemberFilters } from './MemberFilters.tsx'
import { filterFromParams, filterMembers, paramsFromFilter, type MemberFilter } from './memberView.ts'

// A página só junta as peças: busca os membros, aplica o filtro da URL e abre o painel de convite.
export function MembersPage() {
    const { org = '' } = useParams()
    const { me } = useAuth()
    // version: mudar faz o useAsync buscar a lista de novo (depois de um convite).
    const [version, setVersion] = useState(0)
    const [inviteOpen, setInviteOpen] = useState(false)
    const { data, error } = useAsync(() => dataClient.listMembers(org), [org, version])

    const [params, setParams] = useSearchParams()
    const filter = filterFromParams(params)
    // replace: digitar na busca não enche o histórico do "voltar" com uma entrada por letra.
    const setFilter = (next: MemberFilter) => setParams(paramsFromFilter(next), { replace: true })

    async function sendInvite(invite: InviteRequest) {
        await dataClient.inviteMembers(org, invite) // se der erro, o painel mostra a mensagem
        setInviteOpen(false)
        setVersion((v) => v + 1) // busca a lista de novo, já com os convidados
    }

    if (error) return <ErrorState error={error} />
    if (!data) return <LoadingState />

    const units = me?.units ?? []
    const { used, total } = data.seats
    return (
        <>
            <PageHeader
                title="Membros"
                description={`${used} de ${total} assentos do plano em uso. Ninguém digita senha por outra pessoa: todos entram por convite ou pedido aprovado.`}
                actions={
                    <button className="btn btn-primary" type="button" onClick={() => setInviteOpen(true)}>
                        <Icon name="plus" size={16} />
                        Convidar pessoas
                    </button>
                }
            />
            <div className="with-aside">
                <div className="stack with-aside-main">
                    <MemberFilters value={filter} units={units} onChange={setFilter} />
                    <DataTable
                        columns={MEMBER_COLUMNS}
                        rows={filterMembers(data.members, filter)}
                        rowKey={(m) => m.id}
                        empty="Nenhum membro com esses filtros."
                    />
                </div>
                {inviteOpen && (
                    <InvitePanel
                        units={units}
                        teams={data.teams}
                        onSend={sendInvite}
                        onClose={() => setInviteOpen(false)}
                    />
                )}
            </div>
        </>
    )
}
