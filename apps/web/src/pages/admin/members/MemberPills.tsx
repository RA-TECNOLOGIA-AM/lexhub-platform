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

type MemberPillsProps = {
    rows: MemberRow[] // já filtradas
    units: Unit[] // para o nome das unidades
    unit: string | null // a unidade do filtro (o cargo mostrado é o dela); null = todas
    now: Date // para "vence em N dias" nos convites
    onOpen: (row: MemberRow) => void
}

// Módulo: a lista de Membros em "pílulas" — uma linha arredondada por pessoa (ou convite) com
// Pessoa · Unidade · Setor · Cargo · Último acesso · Situação. A linha inteira é um botão (onOpen).
export function MemberPills({ rows, units, unit, now, onOpen }: MemberPillsProps) {
    return (
        <div className="mem-pills" role="table" aria-label="Membros">
            <div className="mem-pill mem-pill-head" role="row">
                <span role="columnheader">Pessoa</span>
                <span role="columnheader">Unidade</span>
                <span role="columnheader">Setor</span>
                <span role="columnheader">Cargo</span>
                <span role="columnheader">Último acesso</span>
                <span role="columnheader" className="mem-pill-end">
                    Situação
                </span>
            </div>
            {rows.length === 0 && <p className="muted small mem-pills-empty">Ninguém com esses filtros.</p>}
            {rows.map((row) => {
                const role = roleOf(row, unit)
                const status = statusOf(row)
                const strong = role.badge.includes('pro') || role.label.startsWith('Gestor')
                return (
                    <button
                        key={rowKey(row)}
                        type="button"
                        role="row"
                        className="mem-pill mem-pill-row"
                        onClick={() => onOpen(row)}
                    >
                        <span className="mem-pill-person" role="cell">
                            <span className={row.kind === 'invitation' ? 'av waiting' : 'av mem-av'}>
                                {initialsOf(row)}
                            </span>
                            <span className="mem-pill-name">
                                <strong>{nameOf(row)}</strong>
                                <span className="muted small">
                                    {row.kind === 'member' ? row.member.email : noteOf(row, now)}
                                </span>
                            </span>
                        </span>
                        <span className="mem-pill-cell mem-pill-unit" role="cell">
                            <Icon name="building" size={14} />
                            <span>{unitsText(row, units)}</span>
                        </span>
                        <span className="mem-pill-cell" role="cell">
                            <Icon name="layers" size={14} />
                            <span>{sectorsText(row)}</span>
                        </span>
                        <span role="cell">
                            <span className={strong ? 'mem-chip strong' : 'mem-chip'}>{role.label}</span>
                        </span>
                        <span className="mem-pill-cell muted" role="cell">
                            <Icon name="clock" size={14} />
                            <span>{lastSeenText(row)}</span>
                        </span>
                        <span className="mem-pill-end" role="cell">
                            <span className={status.badge}>{status.label}</span>
                            <Icon name="chevron-right" size={16} />
                        </span>
                    </button>
                )
            })}
        </div>
    )
}
