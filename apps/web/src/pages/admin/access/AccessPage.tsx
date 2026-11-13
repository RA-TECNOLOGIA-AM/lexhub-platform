import { useState } from 'react'
import { useParams, useSearchParams } from 'react-router'
import { PageHeader } from '../../../components/layout/PageHeader.tsx'
import { ErrorState } from '../../../components/states/ErrorState.tsx'
import { LoadingState } from '../../../components/states/LoadingState.tsx'
import { StateMessage } from '../../../components/states/StateMessage.tsx'
import { useAsync } from '../../../hooks/useAsync.ts'
import { dataClient } from '../../../services/client.ts'
import type { Member, MemberAccessUpdate } from '../../../types/index.ts'
import { accessErrorView } from './accessError.ts'
import { AccessDialog } from './AccessDialog.tsx'
import { PeopleList } from './PeopleList.tsx'
import { PermissionMatrix } from './PermissionMatrix.tsx'
import { PERMISSIONS } from './permissions.ts'
import { RoleGrid } from './RoleGrid.tsx'

const DESCRIPTION =
    'O papel diz o que a pessoa pode fazer. A equipe e as unidades dizem quais dashboards ela vê. Tudo isso é conferido no servidor.'

// A página só junta as peças: a grade da unidade (?unidade=), a matriz de papéis e o editor de pessoas.
export function AccessPage() {
    const { org = '' } = useParams()
    const [params, setParams] = useSearchParams()
    const unit = params.get('unidade')
    // version: mudar faz o useAsync buscar de novo (depois de salvar uma pessoa).
    const [version, setVersion] = useState(0)
    const [editing, setEditing] = useState<Member | null>(null) // pessoa com a janela aberta
    const { data, error } = useAsync(
        () =>
            Promise.all([
                dataClient.getAccessOverview(org, unit),
                dataClient.listMembers(org),
                dataClient.getSessionEmail(),
            ]),
        [org, unit, version],
    )

    if (error) {
        if (!accessErrorView(error).forbidden) return <ErrorState error={error} />
        return (
            <>
                <PageHeader title="Acesso" description={DESCRIPTION} />
                <div className="stack">
                    <PermissionMatrix matrix={PERMISSIONS} />
                    <StateMessage icon="shield" title="Você não gere acesso nesta organização.">
                        Quem muda cargos e equipes é o Owner, o Desenvolvedor ou o Gestor da unidade.
                    </StateMessage>
                </div>
            </>
        )
    }
    if (!data) return <LoadingState />

    const [overview, members, selfEmail] = data
    async function save(memberId: string, update: MemberAccessUpdate) {
        await dataClient.updateMemberAccess(org, memberId, update) // erro: a janela mostra a mensagem
        setVersion((v) => v + 1) // busca a grade e a lista de novo
    }
    const self = (selfEmail ?? '').toLowerCase()

    return (
        <>
            <PageHeader
                title="Acesso"
                description={DESCRIPTION}
                actions={
                    overview.units.length > 1 && (
                        <label className="filter">
                            <span className="lbl">Unidade</span>
                            <select
                                className="field"
                                value={overview.unit}
                                onChange={(e) => setParams({ unidade: e.target.value }, { replace: true })}
                            >
                                {overview.units.map((u) => (
                                    <option key={u.code} value={u.code}>
                                        {u.name}
                                    </option>
                                ))}
                            </select>
                        </label>
                    )
                }
            />
            <div className="stack">
                <RoleGrid overview={overview} />
                <div className="access-cols">
                    <PeopleList members={members.members.filter((m) => m.status === 'active')} onPick={setEditing} />
                    <div className="access-main">
                        <PermissionMatrix matrix={PERMISSIONS} />
                    </div>
                </div>
            </div>
            {editing && (
                <AccessDialog
                    key={editing.id}
                    member={editing}
                    overview={overview}
                    isSelf={editing.email.toLowerCase() === self}
                    onSave={(update) => save(editing.id, update)}
                    onClose={() => setEditing(null)}
                />
            )}
        </>
    )
}
