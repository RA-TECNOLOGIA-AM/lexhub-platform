import { useState } from 'react'
import type { ConnectResult, DatabaseConnectInput, DatabaseConnector, Unit } from '../../../types/index.ts'
import { Modal } from '../../../components/ui/Modal.tsx'
import { PasswordInput } from '../../../components/ui/PasswordInput.tsx'
import { toDataError } from '../../../services/errors.ts'
import { CheckList, CopyButton } from './CheckList.tsx'
import { DEFAULT_PORT, parseConnectionUrl, readOnlySql } from './connectionUrl.ts'
import { failedChecks } from './connectSource.ts'

type DatabaseStepProps = {
    unit: Unit
    connector: DatabaseConnector
    egressIp: string | null
    onSave: (input: DatabaseConnectInput) => Promise<ConnectResult> // testa e, se passar, grava
    onSaved: () => void
    onBack: () => void
    onClose: () => void
}

const LABEL: Record<DatabaseConnector, string> = { postgres: 'Postgres', mysql: 'MySQL' }

// Módulo: o passo do banco próprio (Postgres/MySQL). URL de conexão no topo preenche os campos; botão único
// "Testar e salvar" (vira "Salvar mesmo assim" se o usuário puder escrever). A senha só vai para a API.
export function DatabaseStep({ unit, connector, egressIp, onSave, onSaved, onBack, onClose }: DatabaseStepProps) {
    const [url, setUrl] = useState('')
    const [name, setName] = useState(`Banco ${unit.name}`)
    const [host, setHost] = useState('')
    const [port, setPort] = useState('')
    const [database, setDatabase] = useState('')
    const [user, setUser] = useState('')
    const [password, setPassword] = useState('')
    const [ssl, setSsl] = useState(true)
    const [result, setResult] = useState<ConnectResult | null>(null)
    const [saving, setSaving] = useState(false)
    const [error, setError] = useState<string | null>(null)

    // Qualquer mudança nos campos invalida o teste anterior (e a confirmação de "Salvar mesmo assim").
    const edit =
        <T,>(set: (v: T) => void) =>
        (v: T) => {
            set(v)
            setResult(null)
        }

    function pasteUrl(text: string) {
        setUrl(text)
        setResult(null)
        const parsed = parseConnectionUrl(text)
        if (!parsed) return
        setHost(parsed.host)
        setPort(parsed.port ? String(parsed.port) : '')
        setDatabase(parsed.database)
        setUser(parsed.user)
        if (parsed.password) setPassword(parsed.password)
        if (parsed.ssl !== null) setSsl(parsed.ssl)
    }

    const portNumber = port.trim() ? Number(port) : null
    const portValid = portNumber === null || (Number.isInteger(portNumber) && portNumber >= 1 && portNumber <= 65535)
    const complete = name.trim() && host.trim() && database.trim() && user.trim() && password && portValid

    async function save() {
        setSaving(true)
        setError(null)
        try {
            const res = await onSave({
                connector,
                name: name.trim(),
                host: host.trim(),
                port: portNumber,
                database: database.trim(),
                user: user.trim(),
                password,
                ssl,
                writerAck: Boolean(result?.needsWriterAck),
            })
            setResult(res)
            if (res.saved) {
                onSaved()
                onClose()
                return
            }
        } catch (err) {
            setError(toDataError(err).message)
        }
        setSaving(false)
    }

    const failed = result ? failedChecks(result.checks) : []
    const scheme = connector === 'postgres' ? 'postgresql' : 'mysql'

    return (
        <Modal
            title={`Conectar fonte · ${LABEL[connector]}`}
            subtitle={`Unidade ${unit.name} (${unit.code})`}
            className="connect-dialog"
            onClose={onClose}
            footer={
                <>
                    <button className="btn" type="button" onClick={onBack} disabled={saving}>
                        Voltar
                    </button>
                    <span style={{ flex: 1 }} />
                    <button className="btn" type="button" onClick={onClose} disabled={saving}>
                        Cancelar
                    </button>
                    <button className="btn btn-primary" type="button" onClick={save} disabled={!complete || saving}>
                        {saving ? 'Testando…' : result?.needsWriterAck ? 'Salvar mesmo assim' : 'Testar e salvar'}
                    </button>
                </>
            }
        >
            <details className="connect-howto">
                <summary>Como pedir o acesso ao cliente</summary>
                <ol>
                    <li>
                        Peça um usuário <strong>só de leitura</strong> para o LexHub:
                        <pre className="connect-sql">{readOnlySql(connector, database, egressIp)}</pre>
                        <CopyButton text={readOnlySql(connector, database, egressIp)} label="Copiar SQL" />
                    </li>
                    <li>
                        Peça para liberar o IP do LexHub no firewall do banco:{' '}
                        {egressIp ? (
                            <>
                                <code>{egressIp}</code> <CopyButton text={egressIp} label="Copiar IP" />
                            </>
                        ) : (
                            <span className="muted">o IP de saída ainda não foi configurado na API.</span>
                        )}
                    </li>
                </ol>
            </details>

            <label>
                <span className="lbl">URL de conexão (opcional, preenche os campos)</span>
                <input
                    className="field"
                    value={url}
                    spellCheck={false}
                    autoComplete="off"
                    placeholder={`${scheme}://lexhub_leitura:senha@db.operacao.com.br:${DEFAULT_PORT[connector]}/operacao`}
                    onChange={(e) => pasteUrl(e.target.value)}
                />
            </label>
            <div className="connect-or">ou preencha</div>
            <label>
                <span className="lbl">Nome da fonte</span>
                <input className="field" value={name} onChange={(e) => edit(setName)(e.target.value)} />
            </label>
            <div className="connect-row">
                <label className="connect-grow">
                    <span className="lbl">IP ou nome do host</span>
                    <input
                        className="field"
                        value={host}
                        spellCheck={false}
                        autoComplete="off"
                        onChange={(e) => edit(setHost)(e.target.value)}
                    />
                </label>
                <label className="connect-port">
                    <span className="lbl">Porta (opcional)</span>
                    <input
                        className="field"
                        value={port}
                        inputMode="numeric"
                        placeholder={String(DEFAULT_PORT[connector])}
                        onChange={(e) => edit(setPort)(e.target.value.replace(/\D/g, ''))}
                    />
                </label>
            </div>
            <label>
                <span className="lbl">Banco de dados</span>
                <input
                    className="field"
                    value={database}
                    spellCheck={false}
                    autoComplete="off"
                    onChange={(e) => edit(setDatabase)(e.target.value)}
                />
            </label>
            <div className="connect-row">
                <label className="connect-grow">
                    <span className="lbl">Nome de usuário</span>
                    <input
                        className="field"
                        value={user}
                        spellCheck={false}
                        autoComplete="off"
                        onChange={(e) => edit(setUser)(e.target.value)}
                    />
                </label>
                <div className="connect-grow">
                    <label className="lbl" htmlFor="connect-password">
                        Senha
                    </label>
                    <PasswordInput
                        id="connect-password"
                        value={password}
                        autoComplete="new-password"
                        onChange={edit(setPassword)}
                    />
                </div>
            </div>
            <label className="check-row">
                <input type="checkbox" checked={ssl} onChange={(e) => edit(setSsl)(e.target.checked)} />
                Ativar SSL
            </label>

            {result && <CheckList checks={result.checks} />}
            {result && failed.length === 0 && result.needsWriterAck && (
                <p className="muted small" style={{ margin: 0 }}>
                    O teste passou, mas esse usuário pode alterar dados. Salvar assim fica registrado na auditoria.
                </p>
            )}
            {error && (
                <p className="invite-error" role="alert" style={{ margin: 0 }}>
                    {error}
                </p>
            )}
        </Modal>
    )
}
