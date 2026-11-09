import { useEffect, useState } from 'react'
import { Outlet, useParams } from 'react-router'
import { useAuth } from '../../contexts/auth-context.ts'
import { orgDecision } from '../../lib/orgs.ts'
import { LoadingState } from '../states/LoadingState.tsx'
import { StateMessage } from '../states/StateMessage.tsx'

// Porteiro das rotas /:org/...: a organização ativa é a da URL.
// Se a URL aponta para outra organização da pessoa, troca (busca o "me" dela) antes de mostrar a página;
// se a pessoa não faz parte, não mostra nada dela (nem diz se ela existe).
export function OrgScope() {
    const { org = '' } = useParams()
    const { me, switchOrg } = useAuth()
    const [failed, setFailed] = useState<string | null>(null) // slug cuja troca deu erro
    const decision = me ? orgDecision(org, me) : 'deny'

    useEffect(() => {
        if (decision !== 'switch') return
        switchOrg(org).catch(() => setFailed(org))
    }, [decision, org, switchOrg])

    if (decision === 'show') return <Outlet />
    if (decision === 'deny' || failed === org) {
        return (
            <StateMessage icon="lock" title="Organização não encontrada" alert>
                Confira o endereço ou escolha uma das suas organizações no menu ao lado.
            </StateMessage>
        )
    }
    return <LoadingState />
}
