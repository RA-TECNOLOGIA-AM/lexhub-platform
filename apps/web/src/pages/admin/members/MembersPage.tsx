import { useState } from 'react'
import { useParams, useSearchParams } from 'react-router'
import { Icon } from '../../../components/ui/Icon.tsx'
import { PageHeader } from '../../../components/layout/PageHeader.tsx'
import { ErrorState } from '../../../components/states/ErrorState.tsx'
import { LoadingState } from '../../../components/states/LoadingState.tsx'
import { StateMessage } from '../../../components/states/StateMessage.tsx'
import { dataClient } from '../../../services/client.ts'
import type { InviteRequest } from '../../../types/index.ts'
import { useAsync } from '../../../hooks/useAsync.ts'
import { InvitePanel } from './InvitePanel.tsx'
import { MemberDetail } from './MemberDetail.tsx'
import { MemberList } from './MemberList.tsx'
import { membersErrorView } from './membersError.ts'
import {
    activeCount,
    filterFromParams,
    filterRows,
    paramsFromFilter,
    rowKey,
    rowsOf,
    type MemberFilter,
} from './memberView.ts'

const DESCRIPTION = 'Ninguém digita senha por outra pessoa: todos entram por convite ou pedido aprovado.'

// A página só junta as peças: lista à esquerda (filtro na URL) e, à direita, a pessoa escolhida
// (?pessoa=) ou o formulário de convite. Cargos, setores e exceções se editam na aba Acesso.
export function MembersPage() {
    const { org = '' } = useParams()
    const sessionEmail = useAsync(() => dataClient.getSessionEmail(), []).data ?? null
    // version: mudar faz o useAsync buscar a lista de novo (depois de convidar, desativar...).
    const [version, setVersion] = useState(0)
    const [inviting, setInviting] = useState(false)
    const [now] = useState(() => new Date()) // para "vence em N dias"
    const { data, error } = useAsync(() => dataClient.listMembers(org), [org, version])

    const [params, setParams] = useSearchParams()
    const filter = filterFromParams(params)
    const picked = params.get('pessoa')
    // replace: digitar na busca não enche o histórico do "voltar" com uma entrada por letra.
    function setUrl(next: MemberFilter, pessoa: string | null) {
        const p = paramsFromFilter(next)
        if (pessoa) p.set('pessoa', pessoa)
        setParams(p, { replace: true })
    }
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
    const visible = filterRows(rows, filter)
    // A escolhida segue aberta mesmo fora do filtro; sem escolha, a primeira da lista.
    const open = rows.find((r) => rowKey(r) === picked) ?? visible[0] ?? null

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
                description={`${count} ${count === 1 ? 'membro ativo' : 'membros ativos'}. ${DESCRIPTION}`}
                actions={
                    <button className="btn btn-primary" type="button" onClick={() => setInviting(true)}>
                        <Icon name="plus" size={16} />
                        Convidar pessoas
                    </button>
                }
            />
            <div className="acc-md">
                <MemberList
                    rows={visible}
                    total={count}
                    filter={filter}
                    units={data.units}
                    selectedKey={inviting || !open ? null : rowKey(open)}
                    now={now}
                    onFilter={(next) => setUrl(next, picked)}
                    onPick={(row) => {
                        setInviting(false)
                        setUrl(filter, rowKey(row))
                    }}
                />
                {inviting ? (
                    <InvitePanel
                        units={data.units}
                        teams={data.teams}
                        canInviteAdmin={data.can_invite_admin}
                        onSend={sendInvite}
                        onClose={() => setInviting(false)}
                    />
                ) : open ? (
                    <MemberDetail
                        key={`${rowKey(open)}:${version}`}
                        row={open}
                        units={data.units}
                        teams={data.teams}
                        isSelf={open.kind === 'member' && open.member.email === sessionEmail}
                        accessHref={
                            open.kind === 'member'
                                ? `/${org}/admin/acesso?pessoa=${open.member.id}`
                                : `/${org}/admin/acesso`
                        }
                        onSetStatus={async (status) => {
                            if (open.kind !== 'member') return
                            await dataClient.setMemberStatus(org, open.member.id, status)
                            reload()
                        }}
                        onRevoke={async () => {
                            if (open.kind !== 'invitation') return
                            await dataClient.revokeInvitation(open.invitation.id)
                            setUrl(filter, null)
                            reload()
                        }}
                    />
                ) : (
                    <StateMessage icon="users" title="Ninguém por aqui ainda.">
                        Convide pessoas para começar.
                    </StateMessage>
                )}
            </div>
        </>
    )
}
