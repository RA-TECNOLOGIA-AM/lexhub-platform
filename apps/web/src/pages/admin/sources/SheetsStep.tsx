import { useState } from 'react'
import type { ConnectResult, SheetConnectInput, SheetTab, Unit } from '../../../types/index.ts'
import { Modal } from '../../../components/ui/Modal.tsx'
import { toDataError } from '../../../services/errors.ts'
import { CheckList } from './CheckList.tsx'

type SheetsStepProps = {
    unit: Unit
    inspect: (url: string) => Promise<SheetTab[]> // link -> abas (a API baixa a planilha)
    onSave: (input: SheetConnectInput) => Promise<ConnectResult>
    onSaved: () => void
    onBack: () => void
    onClose: () => void
}

// Módulo: o passo da planilha. 1. publicar na Web; 2. colar o link (a API lista as abas); 3. escolher a aba.
// O link dá acesso aos dados: vai só para a API, que guarda cifrado.
export function SheetsStep({ unit, inspect, onSave, onSaved, onBack, onClose }: SheetsStepProps) {
    const [url, setUrl] = useState('')
    const [name, setName] = useState(`Planilha ${unit.name}`)
    const [tabs, setTabs] = useState<SheetTab[] | null>(null)
    const [tab, setTab] = useState('')
    const [reading, setReading] = useState(false)
    const [saving, setSaving] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [result, setResult] = useState<ConnectResult | null>(null)

    async function readTabs(link = url) {
        if (!link.trim()) return
        setReading(true)
        setError(null)
        setTabs(null)
        setTab('')
        try {
            const found = await inspect(link.trim())
            setTabs(found)
            if (found.length === 1) setTab(found[0].name)
        } catch (err) {
            setError(toDataError(err).message)
        }
        setReading(false)
    }

    async function save() {
        setSaving(true)
        setError(null)
        try {
            const res = await onSave({ connector: 'sheets', name: name.trim(), url: url.trim(), tab })
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

    return (
        <Modal
            title="Conectar fonte · Google Planilhas"
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
                    <button
                        className="btn btn-primary"
                        type="button"
                        onClick={save}
                        disabled={!tab || !name.trim() || saving}
                    >
                        {saving ? 'Conectando…' : 'Conectar planilha'}
                    </button>
                </>
            }
        >
            <ol className="connect-steps">
                <li>
                    <strong>Publique a planilha na Web</strong>
                    <span className="muted small">
                        No Google Planilhas: Arquivo &gt; Compartilhar &gt; Publicar na Web, formato Microsoft Excel
                        (.xlsx). Quem tiver o link consegue baixar: o LexHub guarda o link cifrado.
                    </span>
                </li>
                <li>
                    <label>
                        <span className="lbl">Link da planilha</span>
                        <span className="connect-row">
                            <input
                                className="field connect-grow"
                                value={url}
                                spellCheck={false}
                                autoComplete="off"
                                placeholder="https://docs.google.com/spreadsheets/d/..."
                                onChange={(e) => {
                                    setUrl(e.target.value)
                                    setTabs(null)
                                    setTab('')
                                    setResult(null)
                                }}
                                onPaste={(e) => {
                                    const text = e.clipboardData.getData('text')
                                    if (text) window.setTimeout(() => readTabs(text), 0)
                                }}
                            />
                            <button
                                className="btn"
                                type="button"
                                onClick={() => readTabs()}
                                disabled={!url.trim() || reading}
                            >
                                {reading ? 'Lendo…' : 'Ler abas'}
                            </button>
                        </span>
                    </label>
                </li>
                <li>
                    <label>
                        <span className="lbl">Aba dos dados</span>
                        <select
                            className="field"
                            value={tab}
                            disabled={!tabs || tabs.length === 0}
                            onChange={(e) => {
                                setTab(e.target.value)
                                setResult(null)
                            }}
                        >
                            <option value="">{tabs ? 'Escolha a aba' : 'Cole o link para ver as abas'}</option>
                            {tabs?.map((t) => (
                                <option key={t.name} value={t.name}>
                                    {t.name} ({t.rows.toLocaleString('pt-BR')} linhas)
                                </option>
                            ))}
                        </select>
                    </label>
                </li>
            </ol>
            <label>
                <span className="lbl">Nome da fonte</span>
                <input className="field" value={name} onChange={(e) => setName(e.target.value)} />
            </label>
            {result && <CheckList checks={result.checks} />}
            {error && (
                <p className="invite-error" role="alert" style={{ margin: 0 }}>
                    {error}
                </p>
            )}
        </Modal>
    )
}
