import { useState } from 'react'
import type { DataSource, SourceDetail, SourceFreshness, SourceTechnical } from '../../../types/index.ts'
import { sourceWithFreshness } from './sourceFreshness.ts'
import { ManageSource } from './ManageSource.tsx'
import { AdsSummaryPanel } from './AdsSummaryPanel.tsx'
import { CopyButton } from './CheckList.tsx'
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
    // A hora da fonte no registro de leituras da API (a mesma da linha da lista); undefined = sem registro.
    freshness?: SourceFreshness
    onChanged: () => void // testou de novo ou trocou a senha: a lista da página busca de novo
    onDisconnected: () => void
    onClose: () => void
}

// Módulo: o modal de uma fonte, vista de uma unidade — sobre, conexão (só a TI da LexGroup, nas fontes
// conectadas pela tela), dados guardados (Facebook Ads), dashboards que usam e testes de conexão.
// Senha, link e token nunca aparecem.
// O status e a "Última leitura" vêm do registro de leituras (como a linha da lista); a tabela de baixo é
// só dos testes manuais (Testar de novo), que conferem a conexão sem ler dados para um dashboard.
export function SourceDetailDialog({
    org,
    unit,
    source,
    name,
    freshness,
    onChanged,
    onDisconnected,
    onClose,
}: SourceDetailDialogProps) {
    const [version, setVersion] = useState(0)
    const { data, error } = useAsync(() => dataClient.getSourceDetail(org, unit, source), [org, unit, source, version])
    const changed = () => {
        setVersion((v) => v + 1)
        onChanged()
    }
    const current = data && sourceWithFreshness(data.source, freshness)
    const status = current && statusOf(current.status)
    return (
        <Modal
            title={name}
            subtitle={data ? detailLabel(data.source) : undefined}
            aside={status && <span className={status.badge}>{status.label}</span>}
            className={`source-dialog${data?.ads ? ' ads-wide' : ''}`}
            onClose={onClose}
        >
            {error ? (
                <p className="muted" role="alert" style={{ margin: 0 }}>
                    {toDataError(error).message}
                </p>
            ) : !data ? (
                <LoadingState />
            ) : (
                <>
                    {data.canManage && (
                        <ManageSource org={org} detail={data} onChanged={changed} onDisconnected={onDisconnected} />
                    )}
                    {data.ads && (
                        <AdsSummaryPanel summary={data.ads} currency={String(data.config.currency ?? '') || 'BRL'} />
                    )}
                    <SourceDetailBody detail={data} source={current ?? data.source} />
                    {data.technical && <SourceTechnicalSection technical={data.technical} />}
                </>
            )}
        </Modal>
    )
}

// Módulo: o detalhe técnico para o analista (só a TI da LexGroup recebe): a chave que as queries usam
// e a estrutura salva no teste de conexão (tabelas e colunas do banco, ou abas e colunas da planilha).
function SourceTechnicalSection({ technical }: { technical: SourceTechnical }) {
    const tables = Object.entries(technical.schema ?? {})
    return (
        <section aria-label="Detalhe técnico">
            <h3 className="source-section-title">Detalhe técnico (só LexGroup)</h3>
            <div className="source-key">
                <span className="muted small">Chave da fonte</span>
                <code>{technical.key}</code>
                <CopyButton text={technical.key} label="Copiar chave" />
            </div>
            {tables.length === 0 ? (
                <p className="muted small" style={{ margin: '8px 0 0' }}>
                    Estrutura ainda não salva. Ela é lida no teste de conexão (Testar de novo ou Trocar
                    senha/link/token).
                </p>
            ) : (
                <div className="source-schema" style={{ marginTop: 8 }}>
                    <span className="muted small">
                        {tables.length} {tables.length === 1 ? 'tabela/aba' : 'tabelas/abas'}
                    </span>
                    {tables.map(([table, columns]) => (
                        <details key={table}>
                            <summary>
                                <code>{table}</code> <span className="muted">({columns.length} colunas)</span>
                            </summary>
                            <ul>
                                {columns.map(([column, type]) => (
                                    <li key={column}>
                                        <code>{column}</code>
                                        {type && <span className="muted"> · {type}</span>}
                                    </li>
                                ))}
                            </ul>
                        </details>
                    ))}
                </div>
            )}
        </section>
    )
}

// Módulo: as três seções do modal, a partir da resposta já carregada.
// `source` = a fonte já com a hora do registro (sourceWithFreshness).
function SourceDetailBody({ detail, source }: { detail: SourceDetail; source: DataSource }) {
    const ads = detail.source.connector === 'facebook_ads' // o log tem as coletas, além dos testes
    return (
        <>
            <section aria-label="Sobre a fonte">
                <dl className="source-facts">
                    <dt>Tipo</dt>
                    <dd>{groupLabel(detail.source.group)}</dd>
                    <dt>Quem cuida</dt>
                    <dd>{ownerLabel(detail)}</dd>
                    <dt>Última leitura</dt>
                    <dd>{whenLabel(source)}</dd>
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

            <section aria-label={ads ? 'Coletas e testes' : 'Testes de conexão'}>
                <h3 className="source-section-title">{ads ? 'Coletas e testes' : 'Testes de conexão'}</h3>
                {detail.runs.length === 0 ? (
                    <p className="muted small" style={{ margin: 0 }}>
                        {ads
                            ? 'Nenhuma coleta ainda. Cada coleta automática e cada Testar de novo aparece aqui.'
                            : 'Nenhum teste ainda. Os testes feitos em Testar de novo ou ao trocar a senha/link/token aparecem aqui.'}
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
