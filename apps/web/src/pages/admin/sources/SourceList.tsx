import type { DataSource, SourceKind } from '../../../types/index.ts'
import { Icon, type IconName } from '../../../components/ui/Icon.tsx'
import { StateMessage } from '../../../components/states/StateMessage.tsx'
import { statusOf, whenLabel } from './sourcesView.ts'

// Ícone de cada tipo de fonte. Tipo novo = uma linha aqui.
const KIND_ICON: Record<SourceKind, IconName> = {
    database: 'db',
    flow: 'flow',
    finance: 'receipt',
    sheet: 'sheet',
}

// Módulo: as fontes de uma unidade (ícone, nome, última sincronização e status).
export function SourceList({ sources }: { sources: DataSource[] }) {
    if (sources.length === 0) {
        return (
            <StateMessage icon="plug" title="Nenhuma fonte conectada">
                Conecte o sistema jurídico, o LexPre ou uma planilha para os dashboards desta unidade ganharem dados.
            </StateMessage>
        )
    }
    return (
        <div className="card source-list">
            {sources.map((s) => {
                const status = statusOf(s.status)
                return (
                    <div key={s.id} className="source">
                        <span className="source-icon">
                            <Icon name={KIND_ICON[s.kind]} />
                        </span>
                        <div className="source-name">
                            <span className="unit-name">{s.name}</span>
                            <span className="muted small">{s.detail}</span>
                        </div>
                        <span className="muted small source-when">{whenLabel(s)}</span>
                        <span className={status.badge}>{status.label}</span>
                    </div>
                )
            })}
        </div>
    )
}
