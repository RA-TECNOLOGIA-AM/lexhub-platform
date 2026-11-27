import { useState } from 'react'
import type {
    MetaIntegration,
    MetaIntegrationInput,
    MetaIntegrationSaved,
    MetaIntegrationTest,
    SourceCheck,
} from '../../../types/index.ts'
import { Modal } from '../../../components/ui/Modal.tsx'
import { PasswordInput } from '../../../components/ui/PasswordInput.tsx'
import { LoadingState } from '../../../components/states/LoadingState.tsx'
import { toDataError } from '../../../services/errors.ts'
import { useAsync } from '../../../hooks/useAsync.ts'
import { CheckList } from './CheckList.tsx'
import {
    canTest,
    draftFrom,
    inputFrom,
    isDirty,
    normalizeAppId,
    originNote,
    savedNotice,
    updatedLabel,
    validateMeta,
    type MetaDraft,
} from './metaIntegration.ts'

type MetaIntegrationDialogProps = {
    load: () => Promise<MetaIntegration>
    onTest: (input: { appId: string; appSecret: string | null; graphVersion: string }) => Promise<MetaIntegrationTest>
    onSave: (input: MetaIntegrationInput) => Promise<MetaIntegrationSaved>
    onSaved: (notice: string) => void
    onClose: () => void
}

// Módulo: Integração Meta (só a TI da LexGroup) — o app da Meta que a API usa para ler os tokens, a versão da
// Graph API e a pausa da coleta, para todas as contas de anúncios. A chave secreta nunca volta da API: a tela
// só sabe se ela existe, e trocar ou apagar é uma escolha explícita. Não sabe de API: recebe load/onTest/onSave.
export function MetaIntegrationDialog({ load, onTest, onSave, onSaved, onClose }: MetaIntegrationDialogProps) {
    // Busca uma vez ao abrir (load muda de identidade a cada render de quem abre).
    const loaded = useAsync(() => load(), [])
    const meta = loaded.data
    // O rascunho nasce do que está em uso e só vira estado próprio na primeira mudança.
    const [edited, setEdited] = useState<MetaDraft | null>(null)
    const draft = edited ?? (meta && draftFrom(meta))
    const [checks, setChecks] = useState<SourceCheck[] | null>(null)
    const [busy, setBusy] = useState<'test' | 'save' | null>(null)
    const [error, setError] = useState<string | null>(null)

    function change(patch: Partial<MetaDraft>) {
        if (!draft) return
        setEdited({ ...draft, ...patch })
        setChecks(null)
        setError(null)
    }

    async function test() {
        if (!draft) return
        setBusy('test')
        setError(null)
        try {
            const input = inputFrom(draft)
            const result = await onTest({
                appId: input.appId,
                appSecret: input.appSecret || null,
                graphVersion: input.graphVersion,
            })
            setChecks(result.checks)
        } catch (err) {
            setError(toDataError(err).message)
        } finally {
            setBusy(null)
        }
    }

    async function save() {
        if (!draft || !meta) return
        const problem = validateMeta(draft)
        if (problem) {
            setError(problem)
            return
        }
        setBusy('save')
        setError(null)
        try {
            const result = await onSave(inputFrom(draft))
            if (!result.saved) {
                setChecks(result.checks)
                setError('A Meta recusou o app: nada foi gravado.')
                return
            }
            onSaved(savedNotice(meta, result.integration))
            onClose()
        } catch (err) {
            setError(toDataError(err).message)
        } finally {
            setBusy(null)
        }
    }

    const updated = meta && updatedLabel(meta)
    return (
        <Modal
            title="Integração Meta"
            subtitle="Facebook Ads · vale para todas as contas de anúncios conectadas"
            description={
                'O app da Meta deixa a API ver o tipo e a validade de cada token (usuário do sistema ou pessoal) e ' +
                'assina as chamadas. O token de cada conta continua na fonte dela.'
            }
            className="meta-dialog"
            onClose={onClose}
            footer={
                meta &&
                draft && (
                    <>
                        <button
                            className="btn foot-left"
                            type="button"
                            onClick={test}
                            disabled={busy !== null || !canTest(draft, meta)}
                            title="Confere o ID e a chave na Meta sem gravar"
                        >
                            {busy === 'test' ? 'Testando…' : 'Testar app'}
                        </button>
                        <button className="btn" type="button" onClick={onClose} disabled={busy !== null}>
                            Cancelar
                        </button>
                        <button
                            className="btn btn-primary"
                            type="button"
                            onClick={save}
                            disabled={busy !== null || !isDirty(draft, meta)}
                        >
                            {busy === 'save' ? 'Salvando…' : 'Salvar'}
                        </button>
                    </>
                )
            }
        >
            {!meta || !draft ? (
                loaded.error ? (
                    <p className="invite-error" role="alert" style={{ margin: 0 }}>
                        {loaded.error.message}
                    </p>
                ) : (
                    <LoadingState />
                )
            ) : (
                <>
                    <section className="stack meta-section" aria-label="App da Meta">
                        <h3 className="source-section-title">App da Meta</h3>
                        <label>
                            <span className="lbl">ID do app</span>
                            <input
                                className="field"
                                inputMode="numeric"
                                autoComplete="off"
                                value={draft.appId}
                                placeholder="1234567890123456"
                                onChange={(e) => change({ appId: normalizeAppId(e.target.value) })}
                            />
                            <span className="muted small">{originNote(meta.origin.appId, 'appId')}</span>
                        </label>
                        <div className="meta-field">
                            <label className="lbl" htmlFor="meta-app-secret">
                                Chave secreta do app
                            </label>
                            {draft.secretChoice === 'keep' ? (
                                <div className="meta-secret">
                                    <span className="badge ok">Chave salva</span>
                                    <span className="muted small">Não aparece de novo, nem para quem salvou.</span>
                                    <button
                                        className="btn btn-sm"
                                        type="button"
                                        onClick={() => change({ secretChoice: 'replace' })}
                                    >
                                        Trocar
                                    </button>
                                    <button
                                        className="btn btn-sm btn-danger"
                                        type="button"
                                        onClick={() => change({ secretChoice: 'remove', secret: '' })}
                                    >
                                        Apagar
                                    </button>
                                </div>
                            ) : draft.secretChoice === 'remove' ? (
                                <div className="meta-secret">
                                    <span className="badge warn">Será apagada ao salvar</span>
                                    <button
                                        className="btn btn-sm"
                                        type="button"
                                        onClick={() => change({ secretChoice: 'keep' })}
                                    >
                                        Desfazer
                                    </button>
                                </div>
                            ) : (
                                <>
                                    <PasswordInput
                                        id="meta-app-secret"
                                        value={draft.secret}
                                        autoComplete="off"
                                        onChange={(v) => change({ secret: v })}
                                    />
                                    {meta.hasAppSecret && (
                                        <button
                                            className="btn btn-sm meta-undo"
                                            type="button"
                                            onClick={() => change({ secretChoice: 'keep', secret: '' })}
                                        >
                                            Manter a chave salva
                                        </button>
                                    )}
                                </>
                            )}
                            <span className="muted small">
                                {meta.secretUnreadable
                                    ? 'A chave salva não abre com a chave de cifra atual da API: digite de novo.'
                                    : `${originNote(meta.origin.appSecret, 'appSecret')} Onde achar: developers.facebook.com › seu app › Configurações do app › Básico.`}
                            </span>
                        </div>
                        <label>
                            <span className="lbl">Versão da Graph API</span>
                            <select
                                className="field"
                                value={draft.graphVersion}
                                onChange={(e) => change({ graphVersion: e.target.value })}
                            >
                                {meta.versions.map((v) => (
                                    <option key={v} value={v}>
                                        {v}
                                    </option>
                                ))}
                            </select>
                            <span className="muted small">
                                {originNote(meta.origin.graphVersion, 'graphVersion')} A Meta mantém cada versão por uns
                                2 anos; troque quando ela avisar que a sua vai sair.
                            </span>
                        </label>
                    </section>

                    <section className="stack meta-section" aria-label="Coleta">
                        <h3 className="source-section-title">Coleta</h3>
                        <div className={`source-power ${draft.syncPaused ? 'off' : 'on'}`}>
                            <div>
                                <strong id="meta-sync-label">
                                    {draft.syncPaused ? 'Coleta pausada' : 'Coleta ligada'}
                                </strong>
                                <span className="small muted">
                                    {draft.syncPaused
                                        ? 'Nenhuma conta é coletada. O que já foi guardado fica; retomar traz os dias que faltaram.'
                                        : 'A coleta guarda as métricas de todas as contas a cada 10 minutos.'}
                                </span>
                            </div>
                            <button
                                className="switch"
                                type="button"
                                role="switch"
                                aria-checked={!draft.syncPaused}
                                aria-labelledby="meta-sync-label"
                                title={draft.syncPaused ? 'Retomar a coleta' : 'Pausar a coleta'}
                                onClick={() => change({ syncPaused: !draft.syncPaused })}
                                disabled={busy !== null}
                            />
                        </div>
                        {!meta.syncAvailable && (
                            <p className="muted small" style={{ margin: 0 }}>
                                Este servidor não coleta (FACEBOOK_ADS_SYNC_ENABLED desligado): a pausa só vale onde a
                                coleta está ligada.
                            </p>
                        )}
                    </section>

                    {checks && <CheckList checks={checks} />}
                    {error && (
                        <p className="invite-error" role="alert" style={{ margin: 0 }}>
                            {error}
                        </p>
                    )}
                    {updated && <p className="muted small meta-updated">Última alteração: {updated}</p>}
                </>
            )}
        </Modal>
    )
}
