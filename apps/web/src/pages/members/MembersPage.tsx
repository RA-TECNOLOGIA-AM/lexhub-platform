import { useParams, useSearchParams } from 'react-router'
import { useAuth } from '../../auth/auth-context.ts'
import { DataTable, type Column } from '../../components/DataTable.tsx'
import { Icon } from '../../components/Icon.tsx'
import { PageHeader } from '../../components/PageHeader.tsx'
import { ErrorState } from '../../components/states/ErrorState.tsx'
import { LoadingState } from '../../components/states/LoadingState.tsx'
import { dataClient } from '../../data/client.ts'
import type { Member } from '../../data/types.ts'
import { useAsync } from '../../hooks/useAsync.ts'
import { MemberFilters } from './MemberFilters.tsx'
import {
    filterFromParams,
    filterMembers,
    initialsOf,
    isWaiting,
    paramsFromFilter,
    roleOf,
    scopeOf,
    statusOf,
    type MemberFilter,
} from './memberView.ts'
// As colunas da tabela, como no protótipo.
const COLUMNS: Column<Member>[] = [
    {
        header: 'Pessoa',
        render: (m) => (
            <div className="person">
                <span className={isWaiting(m) ? 'av waiting' : 'av'}>{initialsOf(m)}</span>
                <span className="stack" style={{ gap: 0 }}>
                    <span style={{ fontWeight: 500 }}>{m.name ?? m.email}</span>
                    <span className="muted small">{m.note ?? m.email}</span>
                </span>
            </div>
        ),
    },
    { header: 'Papel', render: (m) => <span className={roleOf(m).badge}>{roleOf(m).label}</span> },
    { header: 'Unidades e equipe', render: (m) => <span className="muted">{scopeOf(m)}</span> },
    { header: 'Situação', render: (m) => <span className={statusOf(m).badge}>{statusOf(m).label}</span> },
    { header: 'Segurança', render: (m) => <span className="muted small">{m.security ?? '—'}</span> },
]

export function MembersPage() {
    const { org = '' } = useParams()
    const { data, error } = useAsync(() => dataClient.listMembers(org), [org])

    const { me } = useAuth()
    const [params, setParams] = useSearchParams()
    const filter = filterFromParams(params)
    // replace: digitar na busca não enche o histórico do "voltar" com uma entrada por letra.
    const setFilter = (next: MemberFilter) => setParams(paramsFromFilter(next), { replace: true })

    if (error) return <ErrorState error={error} />
    if (!data) return <LoadingState />

    const { used, total } = data.seats
    return (
        <>
            <PageHeader
                title="Membros"
                description={`${used} de ${total} assentos do plano em uso. Ninguém digita senha por outra pessoa: todos entram por convite ou pedido aprovado.`}
                actions={
                    <button className="btn btn-primary" type="button">
                        <Icon name="plus" size={16} />
                        Convidar pessoas
                    </button>
                }
            />
            <MemberFilters value={filter} units={me?.units ?? []} onChange={setFilter} />
            <DataTable
                columns={COLUMNS}
                rows={filterMembers(data.members, filter)}
                rowKey={(m) => m.id}
                empty="Nenhum membro com esses filtros."
            />
        </>
    )
}
