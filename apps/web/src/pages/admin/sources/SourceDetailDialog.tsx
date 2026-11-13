import type { SourceDetail } from '../../../types/index.ts'
import { Modal } from '../../../components/ui/Modal.tsx'
import { LoadingState } from '../../../components/states/LoadingState.tsx'
import { dataClient } from '../../../services/client.ts'
import { toDataError } from '../../../services/errors.ts'
import { useAsync } from '../../../hooks/useAsync.ts'
import {
    detailLabel,
    durationLabel,
    groupLabel,
    ownerLabel,
    runResultLabel,
    runWhenLabel,
    statusOf,
    whenLabel,
} from './sourcesView.ts'

type SourceDetailDialogProps = {
    org: string
    unit: string // código da unidade aberta na página
    source: string // chave da fonte ('ng', 'lexpre'...)
    name: string // nome já conhecido pela lista (o título aparece antes de carregar)
    onClose: () => void
}

// Módulo: o modal de uma fonte, vista de uma unidade — sobre, dashboards que usam e últimas sincronizações.
// Só leitura; nenhuma credencial aparece (elas ficam no cofre).
export function SourceDetailDialog({ org, unit, source, name, onClose }: SourceDetailDialogProps) {
    const { data, error } = useAsync(() => dataClient.getSourceDetail(org, unit, source), [org, unit, source])
    const status = data && statusOf(data.source.status)
    return (
        <Modal
            title={name}
            subtitle={data ? detailLabel(data.source) : undefined}
            aside={status && <span className={status.badge}>{status.label}</span>}
            className="source-dialog"
            onClose={onClose}
        >
            {error ? (
                <p className="muted" role="alert" style={{ margin: 0 }}>
                    {toDataError(error).message}
                </p>
            ) : !data ? (
                <LoadingState />
            ) : (
                <SourceDetailBody detail={data} />
            )}
        </Modal>
    )
}

// Módulo: as três seções do modal, a partir da resposta já carregada.
function SourceDetailBody({ detail }: { detail: SourceDetail }) {
    return (
        <>
            <section aria-label="Sobre a fonte">
                <dl className="source-facts">
                    <dt>Tipo</dt>
                    <dd>{groupLabel(detail.source.group)}</dd>
                    <dt>Quem cuida</dt>
                    <dd>{ownerLabel(detail)}</dd>
                    <dt>Última sincronização</dt>
                    <dd>{whenLabel(detail.source)}</dd>
                </dl>
            </section>

            <section aria-label="Dashboards que usam esta fonte">
                <h3 className="source-section-title">Dashboards que usam esta fonte em {detail.unit.name}</h3>
                {detail.dashboards.length === 0 ? (
                    <p className="muted small" style={{ margin: 0 }}>
                        Nenhum dashboard usa esta fonte ainda.
                    </p>
                ) : (
                    <ul className="source-dashboards">
                        {detail.dashboards.map((d) => (
                            <li key={d.key}>{d.name}</li>
                        ))}
                    </ul>
                )}
            </section>

            <section aria-label="Últimas sincronizações">
                <h3 className="source-section-title">Últimas sincronizações</h3>
                {detail.runs.length === 0 ? (
                    <p className="muted small" style={{ margin: 0 }}>
                        Ainda não sincronizou. O histórico aparece aqui depois da primeira sincronização.
                    </p>
                ) : (
                    <table className="source-runs">
                        <thead>
                            <tr>
                                <th scope="col">Início</th>
                                <th scope="col">Duração</th>
                                <th scope="col">Resultado</th>
                            </tr>
                        </thead>
                        <tbody>
                            {detail.runs.map((run) => (
                                <tr key={run.startedAt} className={run.ok === false ? 'run-failed' : undefined}>
                                    <td>{runWhenLabel(run)}</td>
                                    <td>{durationLabel(run)}</td>
                                    <td>{runResultLabel(run)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </section>
        </>
    )
}
