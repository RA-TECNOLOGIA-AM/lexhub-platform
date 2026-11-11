import { Icon } from '../../components/ui/Icon.tsx'

type NoAccessCardProps = {
    email: string | null
    onSignOut: () => void
}

// O miolo do card de login para quem entrou (ex.: com o Google) mas não está em nenhuma organização.
// "Solicitar acesso" ganha função na Fase 2 (pedido gravado e aprovado na área da equipe RA).
export function NoAccessCard({ email, onSignOut }: NoAccessCardProps) {
    return (
        <>
            <div className="stack" style={{ gap: 6 }}>
                <h1 className="h1" style={{ fontSize: 22 }}>
                    Você ainda não tem acesso
                </h1>
                <p className="muted small">
                    {email ? (
                        <>
                            Você entrou como <strong>{email}</strong>, mas essa conta ainda não faz parte de nenhuma
                            organização no LexHub.
                        </>
                    ) : (
                        'Sua conta ainda não faz parte de nenhuma organização no LexHub.'
                    )}
                </p>
            </div>

            <div className="notice info">
                <Icon name="info" />
                <div className="small">
                    Em breve você poderá pedir acesso por aqui. Por enquanto, fale com o administrador do LexHub.
                </div>
            </div>

            <div className="stack" style={{ gap: 10 }}>
                <button className="btn btn-primary btn-block" type="button" disabled title="Em breve">
                    Solicitar acesso
                </button>
                <button className="btn btn-block" type="button" onClick={onSignOut}>
                    <Icon name="logout" size={16} />
                    Usar outra conta
                </button>
            </div>
        </>
    )
}
