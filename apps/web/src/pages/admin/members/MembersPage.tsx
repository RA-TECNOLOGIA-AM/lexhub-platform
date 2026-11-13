import { useState } from 'react'
import { useParams, useSearchParams } from 'react-router'
import { DataTable } from '../../../components/ui/DataTable.tsx'
import { Icon } from '../../../components/ui/Icon.tsx'
import { PageHeader } from '../../../components/layout/PageHeader.tsx'
import { ErrorState } from '../../../components/states/ErrorState.tsx'
import { LoadingState } from '../../../components/states/LoadingState.tsx'
import { StateMessage } from '../../../components/states/StateMessage.tsx'
import { dataClient } from '../../../services/client.ts'
import type { InviteRequest } from '../../../types/index.ts'
import { useAsync } from '../../../hooks/useAsync.ts'
import { InvitePanel } from './InvitePanel.tsx'
import { memberColumns } from './memberColumns.tsx'
import { MemberFilters } from './MemberFilters.tsx'
import { MemberPanel } from './MemberPanel.tsx'
import { membersErrorView } from './membersError.ts'
import {
    activeCount,
    filterFromParams,
    filterRows,
    paramsFromFilter,
    rowKey,
    rowsOf,
    type MemberFilter,
    type MemberRow,
} from './memberView.ts'

// Painel aberto ao lado da lista: o convite ou uma pessoa (pela chave da linha).
type Aside = { kind: 'invite' } | { kind: 'row'; key: string } | null

// A página só junta as peças: busca a lista, aplica o filtro da URL e abre os painéis.
export function MembersPage() {
    const { org = '' } = useParams()
    const sessionEmail = useAsync(() => dataClient.getSessionEmail(), []).data ?? null
    // version: mudar faz o useAsync buscar a lista de novo (depois de convidar, desativar...).
    const [version, setVersion] = useState(0)
    const [aside, setAside] = useState<Aside>(null)
    const [now] = useState(() => new Date()) // para "vence em N dias"
    const { data, error } = useAsync(() => dataClient.listMembers(org), [org, version])

    const [params, setParams] = useSearchParams()
    const filter = filterFromParams(params)
    // replace: digitar na busca não enche o histórico do "voltar" com uma entrada por letra.
    const setFilter = (next: MemberFilter) => setParams(paramsFromFilter(next), { replace: true })
    const reload = () => setVersion((v) => v + 1)

    if (error) {
        if (!membersErrorView(error).forbidden) return <ErrorState error={error} />
        return (
            <>
                <PageHeader title="Membros" description="Quem faz parte da organização." />
                <StateMessage icon="users" title="Você não gere membros nesta organização.">
                    Quem convida e desativa pessoas é o Owner, o Desenvolvedor ou o Gestor da unidade.
                </StateMessage>
            </>
        )
    }
    if (!data) return <LoadingState />

    const rows = rowsOf(data)
    const open = aside?.kind === 'row' ? rows.find((r) => rowKey(r) === aside.key) : undefined
    const columns = memberColumns(filter.unit || null, now, (row: MemberRow) =>
        setAside({ kind: 'row', key: rowKey(row) }),
    )

    async function sendInvite(invite: InviteRequest) {
        const result = await dataClient.inviteMembers(org, invite) // se der erro, o painel mostra a mensagem
        if (result.invited.length) reload() // busca a lista de novo, já com os convites
        return result
    }

    const count = activeCount(data)
    return (
        <>
            <PageHeader
                title="Membros"
                description={`${count} ${count === 1 ? 'membro ativo' : 'membros ativos'}. Ninguém digita senha por outra pessoa: todos entram por convite ou pedido aprovado.`}
                actions={
                    <button className="btn btn-primary" type="button" onClick={() => setAside({ kind: 'invite' })}>
                        <Icon name="plus" size={16} />
                        Convidar pessoas
                    </button>
                }
            />
            <div className="with-aside">
                <div className="stack with-aside-main">
                    <MemberFilters value={filter} units={data.units} onChange={setFilter} />
                    <DataTable
                        columns={columns}
                        rows={filterRows(rows, filter)}
                        rowKey={rowKey}
                        empty="Ninguém com esses filtros."
                    />
                </div>
                {aside?.kind === 'invite' && (
                    <InvitePanel
                        units={data.units}
                        teams={data.teams}
                        canInviteAdmin={data.can_invite_admin}
                        onSend={sendInvite}
                        onClose={() => setAside(null)}
                    />
                )}
                {open && (
                    <MemberPanel
                        key={rowKey(open)}
                        row={open}
                        isSelf={open.kind === 'member' && open.member.email === sessionEmail}
                        accessHref={`/${org}/admin/acesso`}
                        onSetStatus={async (status) => {
                            if (open.kind !== 'member') return
                            await dataClient.setMemberStatus(org, open.member.id, status)
                            reload()
                        }}
                        onRevoke={async () => {
                            if (open.kind !== 'invitation') return
                            await dataClient.revokeInvitation(open.invitation.id)
                            setAside(null)
                            reload()
                        }}
                        onClose={() => setAside(null)}
                    />
                )}
            </div>
        </>
    )
}
