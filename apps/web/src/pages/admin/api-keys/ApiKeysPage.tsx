import { useState } from 'react'
import { useParams } from 'react-router'
import { PageHeader } from '../../../components/layout/PageHeader.tsx'
import { validUntil } from '../../../components/settings/apiKey.ts'
import { ErrorState } from '../../../components/states/ErrorState.tsx'
import { LoadingState } from '../../../components/states/LoadingState.tsx'
import { useAsync } from '../../../hooks/useAsync.ts'
import { refreshPendingApiKeys } from '../../../hooks/usePendingApiKeys.ts'
import { DataError } from '../../../services/errors.ts'
import { dataClient } from '../../../services/client.ts'
import type { ApiKeyInfo } from '../../../types/index.ts'
import { fmtDateTime, pendingExtras, TABS, type ApiKeysTab } from './apiKeysView.ts'
import './apiKeys.css'

export type ApiKeysViewProps = {
    tab: ApiKeysTab
    keys: ApiKeyInfo[]
    selectedId: string | null
    busy: boolean
    error: string
    onTab: (tab: ApiKeysTab) => void
    onSelect: (id: string | null) => void
    onDecide: (id: string, approve: boolean, sectors: string[], note: string | null) => void
    onRevoke: (id: string) => void
    onRevokeSector: (id: string, sector: string) => void
}

const STATUS_LABEL: Record<ApiKeyInfo['status'], string> = {
    pending: 'Pendente',
    active: 'Ativa',
    rejected: 'Recusada',
    revoked: 'Revogada',
}

function Detail({
    apiKey,
    busy,
    onDecide,
    onRevoke,
    onRevokeSector,
    onClose,
}: {
    apiKey: ApiKeyInfo
    busy: boolean
    onDecide: ApiKeysViewProps['onDecide']
    onRevoke: ApiKeysViewProps['onRevoke']
    onRevokeSector: ApiKeysViewProps['onRevokeSector']
    onClose: () => void
}) {
    const [approved, setApproved] = useState<string[]>(() => pendingExtras(apiKey))
    const [note, setNote] = useState('')
    const pending = apiKey.status === 'pending'
    const active = apiKey.status === 'active'
    const extras = apiKey.sectors.filter((s) => !s.base)
    const base = apiKey.sectors.filter((s) => s.base)

    return (
        <aside className="card apikeys-detail" aria-label={`Chave de ${apiKey.userName}`}>
            <header className="apikeys-detail-head">
                <div>
                    <h2 className="h2">{apiKey.userName}</h2>
                    <p className="muted small">{apiKey.userEmail}</p>
                </div>
                <button type="button" className="btn btn-sm btn-ghost" onClick={onClose}>
                    Fechar
                </button>
            </header>
            <dl className="apikeys-facts">
                <dt>Situação</dt>
                <dd>{STATUS_LABEL[apiKey.status]}</dd>
                <dt>Pedido em</dt>
                <dd>{fmtDateTime(apiKey.requestedAt)}</dd>
                {apiKey.note && (
                    <>
                        <dt>Para que</dt>
                        <dd>{apiKey.note}</dd>
                    </>
                )}
                {!pending && (
                    <>
                        <dt>Último uso</dt>
                        <dd>
                            {apiKey.lastUsedAt ? fmtDateTime(apiKey.lastUsedAt) : 'nunca'}
                            {apiKey.lastUsedAt && apiKey.lastUsedIp && (
                                <span className="muted small"> · IP {apiKey.lastUsedIp}</span>
                            )}
                        </dd>
                    </>
                )}
                <dt>Setores da pessoa</dt>
                <dd>{base.length ? base.map((s) => s.setor).join(', ') : 'nenhum'}</dd>
            </dl>

            {extras.length > 0 && (
                <ul className="apikeys-extras">
                    {extras.map((s) => (
                        <li key={s.setor} className="apikeys-extra">
                            <div className="apikeys-extra-head">
                                {pending && s.status === 'pending' ? (
                                    <label className="row" style={{ gap: 8 }}>
                                        <input
                                            type="checkbox"
                                            checked={approved.includes(s.setor)}
                                            onChange={(ev) =>
                                                setApproved((list) =>
                                                    ev.target.checked
                                                        ? [...list, s.setor]
                                                        : list.filter((x) => x !== s.setor),
                                                )
                                            }
                                        />
                                        <strong>{s.setor}</strong>
                                    </label>
                                ) : (
                                    <strong>{s.setor}</strong>
                                )}
                                <span className="muted small">
                                    {s.expiresAt ? `até ${validUntil(s.expiresAt)}` : ''}
                                    {!pending &&
                                        ` · ${s.status === 'approved' ? 'aprovado' : s.status === 'revoked' ? 'revogado' : 'recusado'}`}
                                </span>
                            </div>
                            {s.justificativa && <p className="small">{s.justificativa}</p>}
                            {active && s.status === 'approved' && (
                                <button
                                    type="button"
                                    className="btn btn-sm btn-ghost"
                                    disabled={busy}
                                    onClick={() => onRevokeSector(apiKey.id, s.setor)}
                                >
                                    Revogar setor
                                </button>
                            )}
                        </li>
                    ))}
                </ul>
            )}

            {pending && (
                <div className="apikeys-actions">
                    <label className="apikeys-label">
                        <span className="lbl">Observação (aparece para a pessoa)</span>
                        <input className="field" value={note} onChange={(ev) => setNote(ev.target.value)} />
                    </label>
                    <div className="row" style={{ gap: 8 }}>
                        <button
                            type="button"
                            className="btn btn-primary"
                            disabled={busy}
                            onClick={() => onDecide(apiKey.id, true, approved, note.trim() || null)}
                        >
                            Aprovar
                        </button>
                        <button
                            type="button"
                            className="btn btn-ghost"
                            disabled={busy}
                            onClick={() => onDecide(apiKey.id, false, [], note.trim() || null)}
                        >
                            Recusar
                        </button>
                    </div>
                </div>
            )}
            {active && (
                <div>
                    <button
                        type="button"
                        className="btn btn-danger solid"
                        disabled={busy}
                        onClick={() => {
                            if (window.confirm(`Revogar a chave de ${apiKey.userName}? Os tokens param na hora.`)) {
                                onRevoke(apiKey.id)
                            }
                        }}
                    >
                        Revogar chave
                    </button>
                </div>
            )}
            {apiKey.decisionNote && <p className="muted small">Observação: {apiKey.decisionNote}</p>}
        </aside>
    )
}

// A tela em si (sem buscar nada): abas, lista e o detalhe da chave escolhida.
export function ApiKeysView(props: ApiKeysViewProps) {
    const { tab, keys, selectedId, busy, error } = props
    const selected = keys.find((k) => k.id === selectedId) ?? null
    const empty = TABS.find((t) => t.id === tab)?.empty ?? ''

    return (
        <div className="stack" style={{ gap: 16 }}>
            <div className="segmented" role="tablist" aria-label="Situação">
                {TABS.map((t) => (
                    <button
                        key={t.id}
                        type="button"
                        role="tab"
                        aria-selected={t.id === tab}
                        className={t.id === tab ? 'on' : undefined}
                        onClick={() => props.onTab(t.id)}
                    >
                        {t.label}
                    </button>
                ))}
            </div>
            {error && (
                <div className="notice danger" role="alert">
                    {error}
                </div>
            )}
            <div className={`apikeys-layout${selected ? ' has-detail' : ''}`}>
                {keys.length === 0 ? (
                    <p className="muted">{empty}</p>
                ) : (
                    <ul className="apikeys-list">
                        {keys.map((k) => (
                            <li key={k.id}>
                                <button
                                    type="button"
                                    className="card apikeys-row"
                                    aria-current={k.id === selectedId ? 'true' : undefined}
                                    onClick={() => props.onSelect(k.id)}
                                >
                                    <span className="apikeys-row-name">{k.userName}</span>
                                    <span className="muted small">
                                        {k.sectors.map((s) => s.setor).join(', ') || 'sem setor'} ·{' '}
                                        {fmtDateTime(k.status === 'pending' ? k.requestedAt : k.decidedAt)}
                                    </span>
                                </button>
                            </li>
                        ))}
                    </ul>
                )}
                {selected && (
                    <Detail
                        key={selected.id}
                        apiKey={selected}
                        busy={busy}
                        onDecide={props.onDecide}
                        onRevoke={props.onRevoke}
                        onRevokeSector={props.onRevokeSector}
                        onClose={() => props.onSelect(null)}
                    />
                )}
            </div>
        </div>
    )
}

// Módulo: Administração → Chaves de API (Desenvolvedor). Aprova pedidos com os setores extras marcados,
// acompanha o último uso e revoga um setor extra ou a chave inteira.
export function ApiKeysPage() {
    const { org = '' } = useParams()
    const [tab, setTab] = useState<ApiKeysTab>('pending')
    const [selectedId, setSelectedId] = useState<string | null>(null)
    const [version, setVersion] = useState(0)
    const [busy, setBusy] = useState(false)
    const [error, setError] = useState('')
    const list = useAsync(() => dataClient.listApiKeys(org, tab), [org, tab, version])

    async function run(action: () => Promise<unknown>, failure: string, keepSelection = true) {
        setBusy(true)
        setError('')
        try {
            await action()
            if (!keepSelection) setSelectedId(null)
        } catch (e) {
            setError(e instanceof DataError && e.message ? e.message : failure)
        }
        setVersion((v) => v + 1)
        void refreshPendingApiKeys(org)
        setBusy(false)
    }

    if (list.error && !list.data) return <ErrorState error={list.error} />
    return (
        <>
            <PageHeader
                title="Chaves de API"
                description="Pedidos de Owners, Gestores e Controllers. A chave consulta só os setores da pessoa e os extras aprovados aqui."
            />
            {!list.data ? (
                <LoadingState />
            ) : (
                <ApiKeysView
                    tab={tab}
                    keys={list.data}
                    selectedId={selectedId}
                    busy={busy}
                    error={error}
                    onTab={(next) => {
                        setTab(next)
                        setSelectedId(null)
                    }}
                    onSelect={setSelectedId}
                    onDecide={(id, approve, sectors, note) =>
                        void run(
                            () => dataClient.decideApiKey(id, approve, sectors, note),
                            'Não foi possível decidir o pedido.',
                            false,
                        )
                    }
                    onRevoke={(id) =>
                        void run(() => dataClient.revokeApiKey(id), 'Não foi possível revogar a chave.', false)
                    }
                    onRevokeSector={(id, sector) =>
                        void run(() => dataClient.revokeApiKeySector(id, sector), 'Não foi possível revogar o setor.')
                    }
                />
            )}
        </>
    )
}
