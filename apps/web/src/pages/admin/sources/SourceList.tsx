import type { DataSource, SourceKind } from '../../../types/index.ts'
import { Icon, type IconName } from '../../../components/ui/Icon.tsx'
import { StateMessage } from '../../../components/states/StateMessage.tsx'
import { detailLabel, groupSources, statusOf, whenLabel, type SourceSection } from './sourcesView.ts'

// Ícone de cada tipo de fonte. Tipo novo = uma linha aqui.
const KIND_ICON: Record<SourceKind, IconName> = {
    database: 'db',
    flow: 'flow',
    finance: 'receipt',
    sheet: 'sheet',
}

// Módulo: uma fonte (ícone, nome, de quem é, última sincronização e status).
function SourceRow({ source }: { source: DataSource }) {
    const status = statusOf(source.status)
    return (
        <div className="source">
            <span className="source-icon">
                <Icon name={KIND_ICON[source.kind]} />
            </span>
            <div className="source-name">
                <span className="unit-name">{source.name}</span>
                <span className="muted small">{detailLabel(source)}</span>
            </div>
            <span className="muted small source-when">{whenLabel(source)}</span>
            <span className={status.badge}>{status.label}</span>
        </div>
    )
}

// Módulo: um grupo de fontes num card ("Produtos contratados", "Fontes conectadas"). O título vem por parâmetro.
function SourceGroupCard({ section }: { section: SourceSection }) {
    return (
        <section className="card source-list" aria-label={section.title}>
            <div className="card-head source-group-head">
                <h2 className="h2">{section.title}</h2>
                <span className="muted small">{section.hint}</span>
            </div>
            {section.sources.map((s) => (
                <SourceRow key={s.id} source={s} />
            ))}
        </section>
    )
}

// Módulo: as fontes de uma unidade, separadas em grupos.
export function SourceList({ sources }: { sources: DataSource[] }) {
    if (sources.length === 0) {
        return (
            <StateMessage icon="plug" title="Nenhuma fonte conectada">
                Conecte o sistema jurídico, o LexPre ou uma planilha para os dashboards desta unidade ganharem dados.
            </StateMessage>
        )
    }
    return (
        <>
            {groupSources(sources).map((section) => (
                <SourceGroupCard key={section.group} section={section} />
            ))}
        </>
    )
}
