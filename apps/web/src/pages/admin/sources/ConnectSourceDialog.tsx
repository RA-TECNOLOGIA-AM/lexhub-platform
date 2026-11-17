import { useState } from 'react'
import type { DataSource, ProductKey, ProductOffices, Unit } from '../../../types/index.ts'
import { Modal } from '../../../components/ui/Modal.tsx'
import { Icon } from '../../../components/ui/Icon.tsx'
import { useAsync } from '../../../hooks/useAsync.ts'
import { toDataError } from '../../../services/errors.ts'
import { CONNECTORS, connectorBlock, isProduct, officeSub, sortOffices, type ConnectorKey } from './connectSource.ts'

type ConnectSourceDialogProps = {
    unit: Unit
    sources: DataSource[] // as fontes que a unidade já tem (bloqueia produto repetido)
    loadOffices: (product: ProductKey) => Promise<ProductOffices>
    onLink: (product: ProductKey, ref: string) => Promise<void> // grava; se rejeitar, a mensagem aparece no modal
    onClose: () => void
}

// Módulo: o assistente Conectar fonte. Passo 1 escolhe o tipo; passo 2 é o do tipo (hoje: o escritório do
// LexPre/LexFlow). Não sabe de API: recebe quem busca a lista (loadOffices) e quem grava (onLink).
export function ConnectSourceDialog({ unit, sources, loadOffices, onLink, onClose }: ConnectSourceDialogProps) {
    const [product, setProduct] = useState<ProductKey | null>(null)

    if (product) {
        return (
            <OfficeStep
                unit={unit}
                product={product}
                loadOffices={loadOffices}
                onLink={onLink}
                onBack={() => setProduct(null)}
                onClose={onClose}
            />
        )
    }
    return (
        <Modal
            title="Conectar fonte"
            subtitle={`Unidade ${unit.name} (${unit.code})`}
            className="connect-dialog"
            onClose={onClose}
            footer={
                <button className="btn" type="button" onClick={onClose}>
                    Cancelar
                </button>
            }
        >
            <p className="muted small" style={{ margin: 0 }}>
                De onde vêm os dados desta unidade?
            </p>
            <div className="connect-types">
                {CONNECTORS.map((c) => {
                    const block = connectorBlock(c.key, c.ready, sources)
                    return (
                        <button
                            key={c.key}
                            type="button"
                            className="connect-type"
                            disabled={block !== null}
                            onClick={() => pick(c.key)}
                        >
                            <span className="source-icon">
                                <Icon name={c.icon} />
                            </span>
                            <strong>{c.label}</strong>
                            <span className="muted small">{block ?? c.hint}</span>
                        </button>
                    )
                })}
            </div>
        </Modal>
    )

    function pick(key: ConnectorKey) {
        if (isProduct(key)) setProduct(key)
    }
}

type OfficeStepProps = {
    unit: Unit
    product: ProductKey
    loadOffices: (product: ProductKey) => Promise<ProductOffices>
    onLink: (product: ProductKey, ref: string) => Promise<void>
    onBack: () => void
    onClose: () => void
}

// Passo do LexPre/LexFlow: a lista de escritórios do banco do produto; os já ligados ficam bloqueados.
function OfficeStep({ unit, product, loadOffices, onLink, onBack, onClose }: OfficeStepProps) {
    const { data, error } = useAsync(() => loadOffices(product), [product])
    const [chosen, setChosen] = useState<string | null>(null)
    const [saving, setSaving] = useState(false)
    const [saveError, setSaveError] = useState<string | null>(null)
    const label = CONNECTORS.find((c) => c.key === product)!.label

    async function link() {
        if (!chosen) return
        setSaving(true)
        setSaveError(null)
        try {
            await onLink(product, chosen)
            onClose()
        } catch (err) {
            setSaveError(toDataError(err).message)
            setSaving(false)
        }
    }

    return (
        <Modal
            title={`Conectar fonte · ${label}`}
            subtitle={`Unidade ${unit.name} (${unit.code})`}
            description={`Escritórios encontrados no banco do ${label}. Os que já têm unidade ficam bloqueados.`}
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
                    <button className="btn btn-primary" type="button" onClick={link} disabled={!chosen || saving}>
                        {saving ? 'Ligando…' : 'Ligar escritório'}
                    </button>
                </>
            }
        >
            {error && (
                <p className="invite-error" role="alert" style={{ margin: 0 }}>
                    {error.message}
                </p>
            )}
            {!data && !error && <p className="muted small">Buscando escritórios no {label}…</p>}
            {data && (
                <div className="card connect-offices" role="radiogroup" aria-label={`Escritórios do ${label}`}>
                    {sortOffices(data.offices).map((o) => (
                        <button
                            key={o.ref}
                            type="button"
                            role="radio"
                            aria-checked={chosen === o.ref}
                            className="source source-btn connect-office"
                            disabled={o.linkedTo !== null || saving}
                            onClick={() => setChosen(o.ref)}
                        >
                            <div className="source-name">
                                <span className="unit-name">
                                    {o.name} <span className="muted small">(id {o.ref})</span>
                                </span>
                                <span className="muted small">{officeSub(o, data.activityLabel)}</span>
                            </div>
                            {o.linkedTo ? (
                                <span className="badge neutral">Em uso</span>
                            ) : o.activity > 0 ? (
                                <span className="badge ok">Com dados</span>
                            ) : (
                                <span className="badge warn">Sem dados ainda</span>
                            )}
                        </button>
                    ))}
                </div>
            )}
            <p className="muted small" style={{ margin: 0 }}>
                Não achou a operação? Ela ainda não existe no {label}. Ligue depois, ou conecte um banco próprio ou uma
                planilha quando estiverem disponíveis.
            </p>
            {saveError && (
                <p className="invite-error" role="alert" style={{ margin: 0 }}>
                    {saveError}
                </p>
            )}
        </Modal>
    )
}
