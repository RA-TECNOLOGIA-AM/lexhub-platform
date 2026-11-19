import { Icon } from '../../../components/ui/Icon.tsx'
import type { Unit } from '../../../types/index.ts'
import {
    initialsOf,
    lastSeenText,
    nameOf,
    noteOf,
    roleOf,
    rowKey,
    sectorsText,
    statusOf,
    unitsText,
    type MemberRow,
} from './memberView.ts'

type MemberCardsProps = {
    rows: MemberRow[] // já filtradas
    units: Unit[] // para o nome das unidades
    unit: string | null // a unidade do filtro (o cargo mostrado é o dela); null = todas
    now: Date // para "vence em N dias" nos convites
    onOpen: (row: MemberRow) => void
}

// Módulo: a lista de Membros em cards — um card por pessoa (ou convite) com cargo e situação
// no topo e Unidade · Setor · Último acesso embaixo. O card inteiro é um botão (onOpen).
export function MemberCards({ rows, units, unit, now, onOpen }: MemberCardsProps) {
    if (rows.length === 0) return <p className="muted small mem-cards-empty">Ninguém com esses filtros.</p>
    return (
        <ul className="mem-cards" aria-label="Membros">
            {rows.map((row) => {
                const role = roleOf(row, unit)
                const status = statusOf(row)
                const strong = role.badge.includes('pro') || role.label.startsWith('Gestor')
                return (
                    <li key={rowKey(row)}>
                        <button type="button" className="card mem-card" onClick={() => onOpen(row)}>
                            <span className="mem-card-head">
                                <span className={row.kind === 'invitation' ? 'av waiting' : 'av mem-av'}>
                                    {initialsOf(row)}
                                </span>
                                <span className="mem-card-name">
                                    <strong>{nameOf(row)}</strong>
                                    <span className="muted small">
                                        {row.kind === 'member' ? row.member.email : noteOf(row, now)}
                                    </span>
                                </span>
                                <Icon name="chevron-right" size={16} />
                            </span>
                            <span className="mem-card-tags">
                                <span className={strong ? 'mem-chip strong' : 'mem-chip'}>{role.label}</span>
                                <span className={status.badge}>{status.label}</span>
                            </span>
                            <span className="mem-card-facts">
                                <span className="mem-card-fact mem-card-unit">
                                    <Icon name="building" size={14} />
                                    <span>{unitsText(row, units)}</span>
                                </span>
                                <span className="mem-card-fact">
                                    <Icon name="layers" size={14} />
                                    <span>{sectorsText(row)}</span>
                                </span>
                                <span className="mem-card-fact muted">
                                    <Icon name="clock" size={14} />
                                    <span>{lastSeenText(row)}</span>
                                </span>
                            </span>
                        </button>
                    </li>
                )
            })}
        </ul>
    )
}
