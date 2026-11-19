import { useCallback, useState } from 'react'
import { useParams, useSearchParams } from 'react-router'
import { PageHeader } from '../../../components/layout/PageHeader.tsx'
import { ErrorState } from '../../../components/states/ErrorState.tsx'
import { LoadingState } from '../../../components/states/LoadingState.tsx'
import { StateMessage } from '../../../components/states/StateMessage.tsx'
import { Modal } from '../../../components/ui/Modal.tsx'
import { Segmented } from '../../../components/ui/Segmented.tsx'
import { useAsync } from '../../../hooks/useAsync.ts'
import { dataClient } from '../../../services/client.ts'
import type { Member, MemberAccessUpdate } from '../../../types/index.ts'
import { accessErrorView } from './accessError.ts'
import { PeopleList } from './PeopleList.tsx'
import { PermissionMatrix } from './PermissionMatrix.tsx'
import { PERMISSIONS } from './permissions.ts'
import { PersonEditor } from './PersonEditor.tsx'
import { RoleGrid } from './RoleGrid.tsx'
import { SectorGroups } from './SectorGroups.tsx'

const DESCRIPTION =
    'O cargo diz o que a pessoa pode fazer. Setores, grupos e unidades dizem quais dashboards ela vê; exceções por pessoa só liberam visualização. Tudo é conferido no servidor.'

type Tab = 'pessoas' | 'setores'
const TABS: { value: Tab; label: string }[] = [
    { value: 'pessoas', label: 'Pessoas' },
    { value: 'setores', label: 'Setores' },
]
const LEAVE = 'Há alterações não salvas nesta pessoa. Descartar?'

// A página junta as peças. Aba Pessoas (?aba=pessoas, padrão): lista à esquerda e o detalhe da pessoa
// escolhida (?pessoa=). Aba Setores: grupos dos setores e o que cada cargo vê, na unidade ?unidade=.
// "Regras dos papéis" abre a matriz numa gaveta.
export function AccessPage() {
    const { org = '' } = useParams()
    const [params, setParams] = useSearchParams()
    const unit = params.get('unidade')
    const tab: Tab = params.get('aba') === 'setores' ? 'setores' : 'pessoas'
    const picked = params.get('pessoa')
    // version: mudar faz o useAsync buscar de novo (depois de salvar). O resultado leva a versão
    // em que foi buscado: o detalhe remonta só quando o dado novo chega (rascunho parte do banco).
    const [version, setVersion] = useState(0)
    const [dirty, setDirty] = useState(false)
    const [rulesOpen, setRulesOpen] = useState(false)
    const onDirtyChange = useCallback((d: boolean) => setDirty(d), [])
    const { data, error } = useAsync(
        () =>
            Promise.all([
                dataClient.getAccessOverview(org, unit),
                dataClient.listMembers(org),
                dataClient.getSessionEmail(),
            ]).then((r) => [...r, version] as const),
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

    const [overview, members, selfEmail, loadedVersion] = data
    const people = members.members.filter((m) => m.status === 'active')
    const selected = people.find((m) => m.id === picked) ?? people[0] ?? null
    const self = (selfEmail ?? '').toLowerCase()

    // Troca de pessoa ou de aba com rascunho pendente: pergunta antes.
    function go(next: Record<string, string>) {
        if (dirty && !window.confirm(LEAVE)) return
        const merged = new URLSearchParams(params)
        for (const [k, v] of Object.entries(next)) merged.set(k, v)
        setParams(merged, { replace: true })
    }
    async function save(member: Member, update: MemberAccessUpdate) {
        await dataClient.updateMemberAccess(org, member.id, update) // erro: o detalhe mostra a mensagem
        setVersion((v) => v + 1) // busca de novo; o detalhe remonta com o que o banco devolveu
    }
    async function saveTeamGroups(teamId: string, groups: string[], seesAll: boolean | null) {
        await dataClient.setTeamGroups(org, teamId, groups, seesAll) // erro: a tabela mostra a mensagem
        setVersion((v) => v + 1)
    }

    return (
        <>
            <PageHeader
                title="Acesso"
                description={DESCRIPTION}
                actions={
                    <>
                        {tab === 'setores' && overview.units.length > 1 && (
                            <label className="filter">
                                <span className="lbl">Unidade</span>
                                <select
                                    className="field"
                                    value={overview.unit}
                                    onChange={(e) => go({ unidade: e.target.value })}
                                >
                                    {overview.units.map((u) => (
                                        <option key={u.code} value={u.code}>
                                            {u.name}
                                        </option>
                                    ))}
                                </select>
                            </label>
                        )}
                        <button className="btn" type="button" onClick={() => setRulesOpen(true)}>
                            Regras dos papéis
                        </button>
                    </>
                }
            />
            <div className="stack">
                <Segmented label="Ver" options={TABS} value={tab} onChange={(t) => go({ aba: t })} />
                {tab === 'pessoas' ? (
                    <div className="acc-md">
                        <PeopleList
                            members={people}
                            selectedId={selected?.id ?? null}
                            onPick={(m) => m.id !== selected?.id && go({ pessoa: m.id })}
                        />
                        {selected ? (
                            <PersonEditor
                                key={`${selected.id}:${loadedVersion}`}
                                member={selected}
                                overview={overview}
                                isSelf={selected.email.toLowerCase() === self}
                                onSave={(update) => save(selected, update)}
                                onDirtyChange={onDirtyChange}
                            />
                        ) : (
                            <StateMessage icon="users" title="Ninguém ativo ainda.">
                                Convide pessoas em Membros para dar acesso.
                            </StateMessage>
                        )}
                    </div>
                ) : (
                    <>
                        <SectorGroups overview={overview} onSave={saveTeamGroups} />
                        <RoleGrid overview={overview} />
                    </>
                )}
            </div>
            {rulesOpen && (
                <Modal
                    title="Regras dos papéis"
                    subtitle="O que cada cargo pode fazer dentro de uma unidade"
                    className="side-drawer"
                    onClose={() => setRulesOpen(false)}
                >
                    <PermissionMatrix matrix={PERMISSIONS} />
                </Modal>
            )}
        </>
    )
}
