import { useEffect, useState } from 'react'
import { useParams, useSearchParams } from 'react-router'
import { Icon } from '../../../components/ui/Icon.tsx'
import { PageHeader } from '../../../components/layout/PageHeader.tsx'
import { ErrorState } from '../../../components/states/ErrorState.tsx'
import { LoadingState } from '../../../components/states/LoadingState.tsx'
import { StateMessage } from '../../../components/states/StateMessage.tsx'
import { Modal } from '../../../components/ui/Modal.tsx'
import { Segmented } from '../../../components/ui/Segmented.tsx'
import { dataClient } from '../../../services/client.ts'
import type { InviteRequest } from '../../../types/index.ts'
import { useAsync } from '../../../hooks/useAsync.ts'
import { useAutoRefresh } from '../../../hooks/useAutoRefresh.ts'
import { seatAlert } from '../../../lib/planLimits.ts'
import { InvitePanel } from './InvitePanel.tsx'
import { MemberDetail } from './MemberDetail.tsx'
import { MemberFilters } from './MemberFilters.tsx'
import { MemberCards } from './MemberCards.tsx'
import { MemberPills } from './MemberPills.tsx'
import { membersErrorView } from './membersError.ts'
import {
    activeCount,
    filterFromParams,
    filterRows,
    paramsFromFilter,
    rowKey,
    rowsOf,
    storedMembersLayout,
    storeMembersLayout,
    type MemberFilter,
    type MemberRow,
    type MembersLayout,
} from './memberView.ts'

const LAYOUTS: { value: MembersLayout; label: string; icon: 'list' | 'grid' }[] = [
    { value: 'pilulas', label: 'Pílulas', icon: 'list' },
    { value: 'cards', label: 'Cards', icon: 'grid' },
]

// A página só junta as peças: filtros (na URL), a lista (pílulas ou cards, à escolha) e, ao clicar numa pessoa,
// o detalhe numa gaveta lateral (?pessoa=). Cargos, setores e exceções se editam na aba Acesso.
export function MembersPage() {
    const { org = '' } = useParams()
    const sessionEmail = useAsync(() => dataClient.getSessionEmail(), []).data ?? null
    // version: mudar faz o useAsync buscar a lista de novo (depois de convidar, desativar...).
    const [version, setVersion] = useState(0)
    const [inviting, setInviting] = useState(false)
    const [layout, setLayout] = useState(() => storedMembersLayout())
    // Relógio da tela: "vence em N dias" e a presença ("Online agora", "Visto há 5 min") andam sozinhos.
    const [now, setNow] = useState(() => new Date())
    useEffect(() => {
        const timer = setInterval(() => setNow(new Date()), 30_000)
        return () => clearInterval(timer)
    }, [])
    const { data, error } = useAsync(() => dataClient.listMembers(org), [org, version])
    // Modo suporte ("Ver como este membro"): só para quem tem a permissão. Falhou = sem o botão.
    const perms = useAsync(() => dataClient.getMyAdminPermissions(org), [org]).data
    const canSupport = perms?.support === true
    // Assentos do plano: só quem vê Plano e cobrança busca. Falhou = sem aviso. Refaz depois de convidar.
    const canBilling = perms?.billing === true
    const billing = useAsync(
        () => (canBilling ? dataClient.getBilling(org).catch(() => null) : Promise.resolve(null)),
        [org, canBilling, version],
    ).data
    // Busca a lista de novo a cada minuto (com a aba visível): quem entrou ou saiu aparece sem recarregar.
    useAutoRefresh(60_000, () => setVersion((v) => v + 1), data)

    const [params, setParams] = useSearchParams()
    const filter = filterFromParams(params)
    // ?m=<id> (volta do modo suporte) também abre a gaveta daquela pessoa.
    const picked = params.get('pessoa') ?? params.get('m')
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
    const open = rows.find((r) => rowKey(r) === picked) ?? null

    async function sendInvite(invite: InviteRequest) {
        const result = await dataClient.inviteMembers(org, invite) // se der erro, o painel mostra a mensagem
        if (result.invited.length) reload() // busca a lista de novo, já com os convites
        return result
    }

    const count = activeCount(data)
    const listProps = {
        rows: filterRows(rows, filter, now),
        units: data.units,
        unit: filter.unit || null,
        now,
        onOpen: (row: MemberRow) => setUrl(filter, rowKey(row)),
    }
    return (
        <>
            <PageHeader
                title="Membros"
                description={
                    <>
                        {count} {count === 1 ? 'membro ativo' : 'membros ativos'}. Clique em qualquer pessoa para ver os
                        detalhes; unidades, cargos e permissões se gerenciam em <strong>Acesso</strong>.
                    </>
                }
                actions={
                    <>
                        <Segmented
                            label="Ver como"
                            className="view-toggle"
                            options={LAYOUTS}
                            value={layout}
                            onChange={(next) => {
                                setLayout(next)
                                storeMembersLayout(next)
                            }}
                        />
                        <button className="btn btn-primary" type="button" onClick={() => setInviting(true)}>
                            <Icon name="plus" size={16} />
                            Convidar pessoas
                        </button>
                    </>
                }
            />
            <div className="with-aside">
                <div className="stack with-aside-main">
                    <MemberFilters value={filter} units={data.units} onChange={(next) => setUrl(next, null)} />
                    {layout === 'cards' ? <MemberCards {...listProps} /> : <MemberPills {...listProps} />}
                </div>
                {inviting && (
                    <InvitePanel
                        units={data.units}
                        teams={data.teams}
                        canInviteAdmin={data.can_invite_admin}
                        seatAlert={seatAlert(billing?.usage)}
                        billingPath={`/${org}/admin/plano`}
                        onSend={sendInvite}
                        onClose={() => setInviting(false)}
                    />
                )}
            </div>
            {open && (
                <Modal
                    title={open.kind === 'member' ? 'Detalhes do membro' : 'Detalhes do convite'}
                    className="side-drawer mem-drawer"
                    onClose={() => setUrl(filter, null)}
                >
                    <MemberDetail
                        key={`${rowKey(open)}:${version}`}
                        row={open}
                        units={data.units}
                        teams={data.teams}
                        isSelf={open.kind === 'member' && open.member.email === sessionEmail}
                        canSupport={canSupport}
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
                </Modal>
            )}
        </>
    )
}
