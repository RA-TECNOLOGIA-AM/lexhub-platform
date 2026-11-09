import { Link } from 'react-router'

export type PillItem = {
    id: string
    label: string
    to: string // para onde a pílula leva (a escolha fica na URL)
    active: boolean
}

type PillGroupProps = {
    label: string // nome do grupo para leitores de tela ("Unidade")
    items: PillItem[]
}

// Módulo: grupo de pílulas em que cada pílula é um link. Quem usa decide os itens e para onde levam.
export function PillGroup({ label, items }: PillGroupProps) {
    return (
        <div className="pills" role="group" aria-label={label}>
            {items.map((item) => (
                <Link key={item.id} className="pill" to={item.to} aria-pressed={item.active}>
                    {item.label}
                </Link>
            ))}
        </div>
    )
}
