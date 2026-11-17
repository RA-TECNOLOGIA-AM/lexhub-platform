import { useState } from 'react'
import type { ConnectResult, SourceCheck, SourceDetail } from '../../../types/index.ts'
import { PasswordInput } from '../../../components/ui/PasswordInput.tsx'
import { dataClient } from '../../../services/client.ts'
import { toDataError } from '../../../services/errors.ts'
import { CheckList } from './CheckList.tsx'

type ManageSourceProps = {
    org: string
    detail: SourceDetail
    onChanged: () => void // senha trocada ou teste novo: a lista e o detalhe buscam de novo
    onDisconnected: () => void
}

type Mode = 'idle' | 'secret' | 'disconnect'

// Módulo: o que a TI da LexGroup faz numa fonte conectada pela tela (banco próprio ou planilha):
// ver a configuração (sem senha nem link), testar de novo, trocar a senha/o link e desconectar.
export function ManageSource({ org, detail, onChanged, onDisconnected }: ManageSourceProps) {
    const isSheet = detail.source.connector === 'sheets'
    const key = detail.source.id
    const [mode, setMode] = useState<Mode>('idle')
    const [checks, setChecks] = useState<SourceCheck[] | null>(null)
    const [secret, setSecret] = useState('')
    const [pending, setPending] = useState<ConnectResult | null>(null) // falta "Salvar mesmo assim"
    const [busy, setBusy] = useState(false)
    const [error, setError] = useState<string | null>(null)

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
                ...(isSheet ? { url: secret.trim() } : { password: secret }),
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

    const c = detail.config
    return (
        <section aria-label="Conexão" className="stack" style={{ gap: 10 }}>
            <h3 className="source-section-title">Conexão</h3>
            <dl className="source-facts">
                {isSheet ? (
                    <>
                        <dt>Aba</dt>
                        <dd>{String(c.tab ?? '')}</dd>
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
                                Nova senha
                            </label>
                            <PasswordInput
                                id="new-source-password"
                                value={secret}
                                autoComplete="new-password"
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
                        Os dashboards desta fonte somem para a unidade, {isSheet ? 'o link' : 'a senha'} é apagado e o
                        histórico também. Fica registrado na auditoria.
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
                    <button className="btn" type="button" onClick={retest} disabled={busy}>
                        {busy ? 'Testando…' : 'Testar de novo'}
                    </button>
                    <button className="btn" type="button" onClick={() => setMode('secret')}>
                        {isSheet ? 'Trocar link' : 'Trocar senha'}
                    </button>
                    <button className="btn btn-danger" type="button" onClick={() => setMode('disconnect')}>
                        Desconectar
                    </button>
                </div>
            )}

            {checks && <CheckList checks={checks} />}
            {error && (
                <p className="invite-error" role="alert" style={{ margin: 0 }}>
                    {error}
                </p>
            )}
        </section>
    )
}
