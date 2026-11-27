import { Fragment, useState } from 'react'
import type { AdsTokenInfo, ConnectResult, SourceCheck, SourceDetail } from '../../../types/index.ts'
import { PasswordInput } from '../../../components/ui/PasswordInput.tsx'
import { dataClient } from '../../../services/client.ts'
import { toDataError } from '../../../services/errors.ts'
import { CheckList } from './CheckList.tsx'
import { AdsCustomize } from './AdsCustomize.tsx'
import { AdsTokenView } from './AdsTokenView.tsx'
import { conversionLabel, describeSettings, settingsFromConfig } from './facebookAds.ts'

type ManageSourceProps = {
    org: string
    detail: SourceDetail
    onChanged: () => void // senha trocada, teste novo ou ligou/desligou: a lista e o detalhe buscam de novo
    onDisconnected: () => void
}

type Mode = 'idle' | 'secret' | 'disconnect' | 'customize'

// Módulo: o que a TI da LexGroup faz numa fonte com o segredo no banco (banco próprio, planilha ou conta do
// Facebook Ads): ligar/desligar (pausa, em destaque), ver a configuração (sem senha, link nem token), testar de
// novo, trocar a senha/o link/o token e desconectar (destrutivo, ação secundária com confirmação).
export function ManageSource({ org, detail, onChanged, onDisconnected }: ManageSourceProps) {
    const isSheet = detail.source.connector === 'sheets'
    // Facebook Ads: não é lida na hora; a coleta da API guarda as métricas no LexHub (o token é o segredo).
    const isAds = detail.source.connector === 'facebook_ads'
    // Planilha inteira (as antigas, sheets_financeiro_*): a chave está no código dos dashboards, então
    // não se desconecta pela tela; desliga-se (o banco também recusa).
    const wholeSheet = isSheet && !('tab' in detail.config)
    const key = detail.source.id
    const [mode, setMode] = useState<Mode>('idle')
    const [checks, setChecks] = useState<SourceCheck[] | null>(null)
    const [secret, setSecret] = useState('')
    const [pending, setPending] = useState<ConnectResult | null>(null) // falta "Salvar mesmo assim"
    const [busy, setBusy] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [notice, setNotice] = useState<string | null>(null) // Facebook Ads: personalização salva
    const [tokenInfo, setTokenInfo] = useState<AdsTokenInfo | null>(null) // Facebook Ads: o que o token permite

    async function run(action: () => Promise<void>) {
        setBusy(true)
        setError(null)
        try {
            await action()
        } catch (err) {
            setError(toDataError(err).message)
        }
        setBusy(false)
    }

    const retest = () =>
        run(async () => {
            const res = await dataClient.retestSource(org, key)
            setChecks(res.checks)
            onChanged()
        })

    const saveSecret = () =>
        run(async () => {
            const res = await dataClient.changeSourceSecret(org, key, {
                ...(isSheet ? { url: secret.trim() } : isAds ? { token: secret.trim() } : { password: secret }),
                writerAck: Boolean(pending?.needsWriterAck),
            })
            setChecks(res.checks)
            setPending(res.needsWriterAck ? res : null)
            if (res.saved) {
                setMode('idle')
                setSecret('')
                onChanged()
            }
        })

    const disconnect = () =>
        run(async () => {
            await dataClient.disconnectSource(org, key)
            onDisconnected()
        })

    const showToken = () =>
        run(async () => {
            setTokenInfo(tokenInfo ? null : await dataClient.getFacebookAdsToken(org, key))
        })

    const toggle = () =>
        run(async () => {
            await dataClient.setSourceEnabled(org, key, !detail.enabled)
            setChecks(null)
            onChanged()
        })

    const c = detail.config
    const secretName = isSheet ? 'o link' : isAds ? 'o token' : 'a senha'
    const secretKept = isSheet ? 'O link continua salvo' : isAds ? 'O token continua salvo' : 'A senha continua salva'
    return (
        <section aria-label="Conexão" className="stack" style={{ gap: 10 }}>
            <h3 className="source-section-title">Conexão</h3>
            <div className={`source-power ${detail.enabled ? 'on' : 'off'}`}>
                <div>
                    <strong id="source-power-label">{detail.enabled ? 'Fonte ligada' : 'Fonte desligada'}</strong>
                    <span className="small muted">
                        {isAds
                            ? detail.enabled
                                ? 'A coleta guarda as métricas desta conta a cada 10 minutos.'
                                : `A coleta está parada; o que já foi guardado fica. ${secretKept}: religar não pede de novo e traz os dias que faltaram.`
                            : detail.enabled
                              ? 'A API lê esta fonte para os dashboards.'
                              : `Os dashboards mostram "Fonte desligada". ${secretKept}: religar não pede de novo.`}
                    </span>
                </div>
                <button
                    className="switch"
                    type="button"
                    role="switch"
                    aria-checked={detail.enabled}
                    aria-labelledby="source-power-label"
                    title={detail.enabled ? 'Desligar a fonte' : 'Ligar a fonte'}
                    onClick={toggle}
                    disabled={busy}
                />
            </div>
            <dl className="source-facts">
                {isAds ? (
                    <>
                        <dt>Conta</dt>
                        <dd>
                            {String(c.account_name ?? '')} <code>{String(c.ad_account_id ?? '')}</code>
                        </dd>
                        <dt>Moeda</dt>
                        <dd>{String(c.currency ?? '') || '—'}</dd>
                        <dt>Fuso</dt>
                        <dd>{String(c.timezone ?? '') || '—'}</dd>
                        <dt>Token</dt>
                        <dd className="muted">guardado cifrado (não aparece na tela)</dd>
                    </>
                ) : isSheet ? (
                    <>
                        <dt>Aba</dt>
                        <dd>{wholeSheet ? 'todas (planilha inteira)' : String(c.tab ?? '')}</dd>
                        <dt>Link</dt>
                        <dd className="muted">guardado cifrado (não aparece na tela)</dd>
                    </>
                ) : (
                    <>
                        <dt>Host</dt>
                        <dd>
                            <code>
                                {String(c.host ?? '')}:{String(c.port ?? '')}
                            </code>
                        </dd>
                        <dt>Banco</dt>
                        <dd>{String(c.database ?? '')}</dd>
                        <dt>Usuário</dt>
                        <dd>
                            {String(c.user ?? '')}
                            {detail.writerAck && (
                                <span className="badge warn" style={{ marginLeft: 8 }}>
                                    pode escrever
                                </span>
                            )}
                        </dd>
                        <dt>SSL</dt>
                        <dd>{c.ssl ? 'Ativo' : 'Desligado'}</dd>
                        <dt>Senha</dt>
                        <dd className="muted">•••••••• (cifrada)</dd>
                    </>
                )}
            </dl>

            {isAds && mode !== 'customize' && (
                <section aria-label="Personalização da coleta">
                    <h3 className="source-section-title">Personalização da coleta</h3>
                    <dl className="source-facts">
                        {describeSettings(settingsFromConfig(c), conversionLabel).map(([label, value]) => (
                            <Fragment key={label}>
                                <dt>{label}</dt>
                                <dd>{value}</dd>
                            </Fragment>
                        ))}
                    </dl>
                </section>
            )}

            {mode === 'customize' && (
                <AdsCustomize
                    org={org}
                    source={key}
                    currency={String(c.currency ?? '') || 'BRL'}
                    onCancel={() => setMode('idle')}
                    onSaved={(recollect) => {
                        setMode('idle')
                        setNotice(
                            recollect
                                ? 'Personalização salva. A coleta já começou a buscar o histórico de novo com a escolha nova.'
                                : 'Personalização salva. Os resultados já foram recalculados com as conversões novas.',
                        )
                        onChanged()
                    }}
                />
            )}

            {mode === 'secret' && (
                <div className="stack" style={{ gap: 8 }}>
                    {isSheet ? (
                        <label>
                            <span className="lbl">Novo link da planilha</span>
                            <input
                                className="field"
                                value={secret}
                                spellCheck={false}
                                onChange={(e) => {
                                    setSecret(e.target.value)
                                    setPending(null)
                                }}
                            />
                        </label>
                    ) : (
                        <div>
                            <label className="lbl" htmlFor="new-source-password">
                                {isAds ? 'Novo token do usuário do sistema' : 'Nova senha'}
                            </label>
                            <PasswordInput
                                id="new-source-password"
                                value={secret}
                                autoComplete={isAds ? 'off' : 'new-password'}
                                onChange={(v) => {
                                    setSecret(v)
                                    setPending(null)
                                }}
                            />
                        </div>
                    )}
                    <div className="row">
                        <button className="btn" type="button" onClick={() => setMode('idle')} disabled={busy}>
                            Cancelar
                        </button>
                        <button
                            className="btn btn-primary"
                            type="button"
                            onClick={saveSecret}
                            disabled={!secret || busy}
                        >
                            {busy ? 'Testando…' : pending ? 'Salvar mesmo assim' : 'Testar e salvar'}
                        </button>
                    </div>
                </div>
            )}

            {mode === 'disconnect' && (
                <div className="connect-confirm" role="alert">
                    <strong>
                        Desconectar {detail.source.name} de {detail.unit.name}?
                    </strong>
                    <span className="small">
                        {isAds
                            ? 'A coleta para, o token é apagado e as métricas guardadas também (o que a Meta já não guarda não volta).'
                            : `Os dashboards desta fonte somem para a unidade, ${secretName} é ${isSheet ? 'apagado' : 'apagada'} e o histórico também.`}{' '}
                        Não dá para desfazer; para só pausar, desligue a fonte. Fica registrado na auditoria.
                    </span>
                    <div className="row">
                        <button className="btn" type="button" onClick={() => setMode('idle')} disabled={busy}>
                            Manter
                        </button>
                        <button className="btn btn-danger" type="button" onClick={disconnect} disabled={busy}>
                            {busy ? 'Desconectando…' : 'Desconectar'}
                        </button>
                    </div>
                </div>
            )}

            {mode === 'idle' && (
                <div className="row">
                    <button className="btn" type="button" onClick={retest} disabled={busy || !detail.enabled}>
                        {busy ? 'Aguarde…' : 'Testar de novo'}
                    </button>
                    <button className="btn" type="button" onClick={() => setMode('secret')}>
                        {isSheet ? 'Trocar link' : isAds ? 'Trocar token' : 'Trocar senha'}
                    </button>
                    {isAds && (
                        <button className="btn" type="button" onClick={showToken} disabled={busy}>
                            {tokenInfo ? 'Esconder o token' : 'O que o token permite'}
                        </button>
                    )}
                    {isAds && (
                        <button
                            className="btn btn-primary"
                            type="button"
                            onClick={() => {
                                setNotice(null)
                                setChecks(null)
                                setMode('customize')
                            }}
                            disabled={busy}
                        >
                            Personalizar coleta
                        </button>
                    )}
                </div>
            )}
            {mode === 'idle' && tokenInfo && <AdsTokenView info={tokenInfo} />}
            {notice && (
                <p className="ads-note" role="status">
                    {notice}
                </p>
            )}

            {checks && <CheckList checks={checks} />}
            {error && (
                <p className="invite-error" role="alert" style={{ margin: 0 }}>
                    {error}
                </p>
            )}
            {mode === 'idle' && !wholeSheet && (
                <button
                    className="btn btn-sm btn-ghost btn-danger source-disconnect"
                    type="button"
                    onClick={() => setMode('disconnect')}
                >
                    Desconectar fonte…
                </button>
            )}
        </section>
    )
}
