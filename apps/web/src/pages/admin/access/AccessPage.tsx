import { useState } from 'react'
import { useParams } from 'react-router'
import { PageHeader } from '../../../components/layout/PageHeader.tsx'
import { ErrorState } from '../../../components/states/ErrorState.tsx'
import { LoadingState } from '../../../components/states/LoadingState.tsx'
import { Notice } from '../../../components/ui/Notice.tsx'
import { useAuth } from '../../../contexts/auth-context.ts'
import { useAsync } from '../../../hooks/useAsync.ts'
import { dataClient } from '../../../services/client.ts'
import { AccessSimulator } from './AccessSimulator.tsx'
import { PermissionMatrix } from './PermissionMatrix.tsx'
import { TeamRules } from './TeamRules.tsx'

// A página só junta as peças: busca as regras e os membros (em paralelo) e monta os três blocos.
export function AccessPage() {
    const { org = '' } = useParams()
    const { me } = useAuth()
    const { data, error } = useAsync(() => Promise.all([dataClient.getAccess(org), dataClient.listMembers(org)]), [org])
    const [notice, setNotice] = useState<string | null>(null)

    if (error) return <ErrorState error={error} />
    if (!data) return <LoadingState />

    const [access, members] = data
    return (
        <>
            <PageHeader
                title="Acesso"
                description="O papel diz o que a pessoa pode fazer. A equipe e as unidades dizem quais dashboards ela vê. Tudo isso é conferido no servidor."
            />
            <div className="stack">
                {notice && <Notice message={notice} onClose={() => setNotice(null)} />}
                <PermissionMatrix matrix={access.matrix} />
                <div className="access-cols">
                    <TeamRules
                        rules={access.rules}
                        onNewRule={() =>
                            setNotice('Criar regra ainda não está disponível: no MVP o Acesso é só leitura.')
                        }
                    />
                    <AccessSimulator
                        members={members.members}
                        rules={access.rules}
                        matrix={access.matrix}
                        units={me?.units ?? []}
                    />
                </div>
            </div>
        </>
    )
}
