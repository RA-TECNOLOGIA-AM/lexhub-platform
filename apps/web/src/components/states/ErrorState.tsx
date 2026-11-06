import { Link } from 'react-router'
import { useAuth } from '../../auth/auth-context.ts'
import type { DataError } from '../../data/errors.ts'
import type { IconName } from '../Icon.tsx'
import { StateMessage } from './StateMessage.tsx'

type ErrorStateProps = {
    error: DataError
    backTo?: string // se informado, mostra "Voltar aos dashboards" apontando para cá
}

// O que mostrar para cada status. Status novo = uma linha nova aqui, sem mexer nas telas.
const BY_STATUS: Record<number, { icon: IconName; title: string; text: string }> = {
    401: { icon: 'lock', title: 'Sua sessão expirou', text: 'Entre de novo para continuar.' },
    403: {
        icon: 'lock',
        title: 'Você não tem acesso a este dashboard nesta unidade',
        text: 'Peça liberação ao gestor da unidade. A tentativa foi registrada na auditoria.',
    },
    404: { icon: 'inbox', title: 'Não encontrado', text: 'O endereço pode estar errado ou o item não existe mais.' },
}

// Módulo: transforma um DataError na mensagem certa para o usuário.
export function ErrorState({ error, backTo }: ErrorStateProps) {
    const { signOut } = useAuth()
    const known = BY_STATUS[error.status]
    const icon = known?.icon ?? 'alert'
    const title = known?.title ?? 'Não foi possível carregar'
    const text = known?.text ?? error.message

    // 401: a sessão acabou. Sair limpa a sessão e o porteiro (RequireAuth) leva ao /login.
    const action =
        error.status === 401 ? (
            <button className="btn btn-primary" type="button" onClick={signOut}>
                Entrar de novo
            </button>
        ) : backTo ? (
            <Link className="btn" to={backTo}>
                Voltar aos dashboards
            </Link>
        ) : null

    return (
        <StateMessage icon={icon} title={title} action={action} alert>
            {text}
        </StateMessage>
    )
}