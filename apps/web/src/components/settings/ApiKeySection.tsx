import { useState } from 'react'
import { useAuth } from '../../contexts/auth-context.ts'
import { useAsync } from '../../hooks/useAsync.ts'
import { refreshPendingApiKeys } from '../../hooks/usePendingApiKeys.ts'
import { DataError } from '../../services/errors.ts'
import { dataClient } from '../../services/client.ts'
import type {
    ApiKeyEligibility,
    ApiKeyExtraRequest,
    ApiKeyInfo,
    ApiKeyTokens,
} from '../../types/index.ts'
import { addDays, DEFAULT_DAYS, MAX_DAYS, todayInBrazil, validateRequest, validUntil } from './apiKey.ts'

export type ApiKeyViewProps = {
    eligibility: ApiKeyEligibility
    apiKey: ApiKeyInfo | null
    tokens: ApiKeyTokens | null
    busy: boolean
    error: string
    today: string
    guideHref: string // o guia da API pública na Documentação
    onRequest: (note: string | null, extras: ApiKeyExtraRequest[]) => void
    onIssueTokens: () => void
    onHideTokens: () => void
    onRevoke: () => void
}

function Sectors({ apiKey }: { apiKey: ApiKeyInfo }) {
    const visible = apiKey.sectors.filter((s) => s.base || s.status === 'approved' || s.status === 'pending')
    return (
        <ul className="settings-card apikey-sectors">
            {visible.map((s) => (
                <li key={s.setor} className="apikey-sector">
                    <span>{s.setor}</span>
                    <span className="muted small">
                        {s.base
                            ? 'seu setor'
                            : s.status === 'pending'
                              ? 'extra · aguardando'
                              : `extra · até ${s.expiresAt ? validUntil(s.expiresAt) : '—'}`}
                    </span>
                </li>
            ))}
        </ul>
    )
}

function CopyField({ label, value, hint }: { label: string; value: string; hint: string }) {
    return (
        <div className="settings-field">
            <div className="settings-field-head">
                <span className="settings-field-label">{label}</span>
                <button type="button" className="btn btn-sm btn-ghost" onClick={() => void navigator.clipboard?.writeText(value)}>
                    Copiar
                </button>
            </div>
            <code className="apikey-token">{value}</code>
            <p className="muted small">{hint}</p>
        </div>
    )
}

function RequestForm({
    eligibility,
    today,
    busy,
    onRequest,
}: Pick<ApiKeyViewProps, 'eligibility' | 'today' | 'busy' | 'onRequest'>) {
    const [note, setNote] = useState('')
    const [extras, setExtras] = useState<ApiKeyExtraRequest[]>([])
    const [touched, setTouched] = useState(false)
    const options = eligibility.sectors.filter((s) => !eligibility.baseSectors.includes(s))
    const problem = validateRequest(eligibility.baseSectors, extras, today)
    const update = (i: number, patch: Partial<ApiKeyExtraRequest>) =>
        setExtras((list) => list.map((e, j) => (j === i ? { ...e, ...patch } : e)))

    return (
        <form
            className="settings-stack apikey-form"
            onSubmit={(event) => {
                event.preventDefault()
                setTouched(true)
                if (!problem) onRequest(note.trim() || null, extras)
            }}
        >
            <div className="settings-field">
                <span className="settings-field-label">Seus setores</span>
                {eligibility.baseSectors.length > 0 ? (
                    <p className="settings-field-value">{eligibility.baseSectors.join(', ')}</p>
                ) : (
                    <p className="small settings-warn">
                        Você não tem setor cadastrado. Peça setores extras abaixo ou fale com um Desenvolvedor.
                    </p>
                )}
            </div>

            {extras.map((e, i) => (
                <fieldset key={i} className="settings-card apikey-extra">
                    <legend className="settings-field-label">Setor extra</legend>
                    <label className="apikey-label">
                        <span className="lbl">Setor</span>
                        <select className="field" value={e.setor} onChange={(ev) => update(i, { setor: ev.target.value })}>
                            <option value="">Escolha…</option>
                            {options.map((s) => (
                                <option key={s} value={s}>
                                    {s}
                                </option>
                            ))}
                        </select>
                    </label>
                    <label className="apikey-label">
                        <span className="lbl">Por que precisa</span>
                        <textarea
                            className="field"
                            rows={2}
                            value={e.justificativa}
                            onChange={(ev) => update(i, { justificativa: ev.target.value })}
                        />
                    </label>
                    <label className="apikey-label">
                        <span className="lbl">Vale até</span>
                        <input
                            className="field"
                            type="date"
                            min={addDays(today, 1)}
                            max={addDays(today, MAX_DAYS)}
                            value={e.validade}
                            onChange={(ev) => update(i, { validade: ev.target.value })}
                        />
                    </label>
                    <button
                        type="button"
                        className="btn btn-sm btn-ghost"
                        onClick={() => setExtras((list) => list.filter((_, j) => j !== i))}
                    >
                        Tirar
                    </button>
                </fieldset>
            ))}
            {options.length > 0 && (
                <div>
                    <button
                        type="button"
                        className="btn btn-sm btn-ghost"
                        onClick={() =>
                            setExtras((list) => [
                                ...list,
                                { setor: '', justificativa: '', validade: addDays(today, DEFAULT_DAYS) },
                            ])
                        }
                    >
                        + Pedir setor extra
                    </button>
                </div>
            )}

            <label className="apikey-label">
                <span className="lbl">Para que vai usar (opcional)</span>
                <input className="field" value={note} onChange={(ev) => setNote(ev.target.value)} placeholder="Ex.: Power BI das metas" />
            </label>
            {touched && problem && (
                <p className="small settings-warn" role="status">
                    {problem}
                </p>
            )}
            <div>
                <button type="submit" className="btn btn-primary" disabled={busy}>
                    Pedir chave de API
                </button>
            </div>
        </form>
    )
}

// A tela em si (sem buscar nada), um estado por vez: sem chave, pendente, ativa (e tokens) ou encerrada.
export function ApiKeyView(props: ApiKeyViewProps) {
    const { apiKey, tokens, busy, error } = props
    const [again, setAgain] = useState(false)
    const closed = apiKey && (apiKey.status === 'rejected' || apiKey.status === 'revoked')

    let body
    if (!apiKey || (closed && again)) {
        body = <RequestForm {...props} />
    } else if (apiKey.status === 'pending') {
        body = (
            <>
                <p className="small settings-warn" role="status">
                    Aguardando aprovação de um Desenvolvedor.
                </p>
                <Sectors apiKey={apiKey} />
            </>
        )
    } else if (apiKey.status === 'active') {
        body = (
            <>
                <Sectors apiKey={apiKey} />
                {tokens ? (
                    <div className="settings-card apikey-tokens">
                        <p className="small settings-warn" role="status">
                            Guarde agora: os tokens não aparecem de novo. Gerar de novo invalida os anteriores.
                        </p>
                        <CopyField
                            label="Access token"
                            value={tokens.accessToken}
                            hint={`Vale até ${new Date(tokens.accessExpiresAt).toLocaleString('pt-BR')}.`}
                        />
                        <CopyField
                            label="Refresh token"
                            value={tokens.refreshToken}
                            hint={`Renova o access em POST /v1/auth/token; vale até ${new Date(tokens.refreshExpiresAt).toLocaleDateString('pt-BR')}.`}
                        />
                        <div>
                            <button type="button" className="btn btn-sm btn-ghost" onClick={props.onHideTokens}>
                                Já guardei
                            </button>
                        </div>
                    </div>
                ) : (
                    <div className="apikey-actions">
                        <button type="button" className="btn btn-primary" disabled={busy} onClick={props.onIssueTokens}>
                            Gerar tokens
                        </button>
                        <button type="button" className="btn btn-ghost" disabled={busy} onClick={props.onRevoke}>
                            Encerrar chave
                        </button>
                    </div>
                )}
                <p className="muted small">
                    Último uso: {apiKey.lastUsedAt ? new Date(apiKey.lastUsedAt).toLocaleString('pt-BR') : 'nunca'}.
                    Como usar: <a href={props.guideHref}>guia da API pública</a>.
                </p>
            </>
        )
    } else {
        body = (
            <>
                <p className="small settings-warn" role="status">
                    {apiKey.status === 'rejected' ? 'Pedido recusado' : 'Chave encerrada'}
                    {apiKey.decisionNote ? `: ${apiKey.decisionNote}` : '.'}
                </p>
                <div>
                    <button type="button" className="btn btn-primary" onClick={() => setAgain(true)}>
                        Pedir de novo
                    </button>
                </div>
            </>
        )
    }

    return (
        <div className="settings-stack">
            <p className="muted">
                Consulte por API os mesmos dados do Exportar dos dashboards dos seus setores (Power BI, planilhas,
                scripts). Setor extra precisa de justificativa e tem validade; um Desenvolvedor aprova.
            </p>
            {error && (
                <p className="small settings-warn" role="alert">
                    {error}
                </p>
            )}
            {body}
        </div>
    )
}

// Módulo: Configurações → Chave de API (só Owner, Gestor e Controller veem a seção).
export function ApiKeySection() {
    const { me } = useAuth()
    const org = me?.org.slug ?? ''
    const [version, setVersion] = useState(0)
    const [busy, setBusy] = useState(false)
    const [error, setError] = useState('')
    const [tokens, setTokens] = useState<ApiKeyTokens | null>(null)
    const data = useAsync(
        async () => {
            const [eligibility, apiKey] = await Promise.all([
                dataClient.getApiKeyEligibility(org),
                dataClient.getMyApiKey(org),
            ])
            return { eligibility, apiKey }
        },
        [org, version],
    )

    async function run(action: () => Promise<unknown>, failure: string) {
        setBusy(true)
        setError('')
        try {
            await action()
        } catch (e) {
            setError(e instanceof DataError && e.message ? e.message : failure)
        }
        setVersion((v) => v + 1)
        // Quem é Desenvolvedor e pede a própria chave vê o selo do menu subir na hora.
        void refreshPendingApiKeys(org)
        setBusy(false)
    }

    if (!data.data) {
        return <p className="muted small">{data.error ? 'Não foi possível carregar a chave de API.' : 'Carregando…'}</p>
    }
    return (
        <ApiKeyView
            eligibility={data.data.eligibility}
            apiKey={data.data.apiKey}
            tokens={tokens}
            busy={busy}
            error={error}
            today={todayInBrazil()}
            guideHref={`/${org}/documentacao/api-publica`}
            onRequest={(note, extras) =>
                void run(() => dataClient.requestApiKey(org, note, extras), 'Não foi possível pedir a chave.')
            }
            onIssueTokens={() =>
                void run(
                    async () => setTokens(await dataClient.issueApiKeyTokens(org)),
                    'Não foi possível gerar os tokens.',
                )
            }
            onHideTokens={() => setTokens(null)}
            onRevoke={() =>
                void run(async () => {
                    if (data.data?.apiKey) await dataClient.revokeApiKey(data.data.apiKey.id)
                    setTokens(null)
                }, 'Não foi possível encerrar a chave.')
            }
        />
    )
}
