import { useState } from 'react'
import type {
    AdsOptions,
    AdsPreview,
    AdsSettings,
    AdsTokenInfo,
    ConnectInfo,
    ConnectInput,
    ConnectResult,
    DataSource,
    ProductKey,
    ProductOffices,
    SheetTab,
    Unit,
} from '../../../types/index.ts'
import { Modal } from '../../../components/ui/Modal.tsx'
import { Icon } from '../../../components/ui/Icon.tsx'
import { useAsync } from '../../../hooks/useAsync.ts'
import { toDataError } from '../../../services/errors.ts'
import {
    CONNECTORS,
    connectorBlock,
    isDatabase,
    isProduct,
    officeSub,
    sortOffices,
    type ConnectorKey,
} from './connectSource.ts'
import { DatabaseStep } from './DatabaseStep.tsx'
import { FacebookAdsStep, type AdsAccessInput } from './FacebookAdsStep.tsx'
import { SheetsStep } from './SheetsStep.tsx'

type ConnectSourceDialogProps = {
    unit: Unit
    sources: DataSource[] // as fontes que a unidade já tem (bloqueia produto repetido)
    loadOffices: (product: ProductKey) => Promise<ProductOffices>
    onLink: (product: ProductKey, ref: string) => Promise<void> // grava; se rejeitar, a mensagem aparece no modal
    loadConnectInfo: () => Promise<ConnectInfo> // a API cifra senha/link? qual o IP de saída?
    inspectSheet: (url: string) => Promise<SheetTab[]>
    readAdsToken: (token: string) => Promise<AdsTokenInfo> // Facebook Ads: o que o token permite e as contas
    inspectAds: (input: AdsAccessInput) => Promise<AdsOptions> // Facebook Ads: testa e traz as opções da conta
    previewAds: (input: AdsAccessInput & { settings: AdsSettings }) => Promise<AdsPreview>
    onConnect: (input: ConnectInput) => Promise<ConnectResult> // testa e salva banco, planilha ou Facebook Ads
    onSaved: () => void // banco/planilha/conta gravada: a página busca a lista de novo
    onClose: () => void
}

// Módulo: o assistente Conectar fonte. Passo 1 escolhe o tipo; passo 2 é o do tipo (escritório do
// LexPre/LexFlow, banco próprio, planilha ou conta do Facebook Ads). Não sabe de API: recebe quem busca e quem grava.
export function ConnectSourceDialog({
    unit,
    sources,
    loadOffices,
    onLink,
    loadConnectInfo,
    inspectSheet,
    readAdsToken,
    inspectAds,
    previewAds,
    onConnect,
    onSaved,
    onClose,
}: ConnectSourceDialogProps) {
    const [step, setStep] = useState<ConnectorKey | null>(null)
    const info = useAsync(loadConnectInfo, [])
    const back = () => setStep(null)

    if (step && isProduct(step)) {
        return (
            <OfficeStep
                unit={unit}
                product={step}
                loadOffices={loadOffices}
                onLink={onLink}
                onBack={back}
                onClose={onClose}
            />
        )
    }
    if (step && isDatabase(step)) {
        return (
            <DatabaseStep
                unit={unit}
                connector={step}
                egressIp={info.data?.egressIp ?? null}
                onSave={onConnect}
                onSaved={onSaved}
                onBack={back}
                onClose={onClose}
            />
        )
    }
    if (step === 'sheets') {
        return (
            <SheetsStep
                unit={unit}
                inspect={inspectSheet}
                onSave={onConnect}
                onSaved={onSaved}
                onBack={back}
                onClose={onClose}
            />
        )
    }
    if (step === 'facebook_ads') {
        return (
            <FacebookAdsStep
                unit={unit}
                readToken={readAdsToken}
                inspect={inspectAds}
                preview={previewAds}
                onSave={onConnect}
                onSaved={onSaved}
                onBack={back}
                onClose={onClose}
            />
        )
    }
    const secretsReady = Boolean(info.data?.ready)
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
                    const block = connectorBlock(c.key, c.secret, sources, secretsReady)
                    return (
                        <button
                            key={c.key}
                            type="button"
                            className="connect-type"
                            disabled={block !== null || (c.secret && info.loading)}
                            onClick={() => setStep(c.key)}
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
                Não achou a operação? Ela ainda não existe no {label}. Volte e conecte o banco próprio dela ou uma
                planilha, ou ligue depois.
            </p>
            {saveError && (
                <p className="invite-error" role="alert" style={{ margin: 0 }}>
                    {saveError}
                </p>
            )}
        </Modal>
    )
}
