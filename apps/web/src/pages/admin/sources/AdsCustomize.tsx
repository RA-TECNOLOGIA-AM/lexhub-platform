import { useState } from 'react'
import type { AdsOptions, AdsPreview, AdsSettings } from '../../../types/index.ts'
import { LoadingState } from '../../../components/states/LoadingState.tsx'
import { dataClient } from '../../../services/client.ts'
import { toDataError } from '../../../services/errors.ts'
import { useAsync } from '../../../hooks/useAsync.ts'
import { AdsSettingsForm } from './AdsSettingsForm.tsx'
import { AdsPreviewView } from './AdsPreviewView.tsx'
import { backfillLabel, needsRecollect, settingsProblem } from './facebookAds.ts'

type AdsCustomizeProps = {
    org: string
    source: string // chave da fonte
    currency: string
    onSaved: (recollect: boolean) => void
    onCancel: () => void
}

// Módulo: Personalizar coleta de uma fonte Facebook Ads já conectada (com o token salvo). Lê as opções da conta
// na Meta, mostra a personalização atual, a prévia e salva. Se o que é coletado mudar, avisa que o histórico
// vai ser buscado de novo.
export function AdsCustomize({ org, source, currency, onSaved, onCancel }: AdsCustomizeProps) {
    const { data, error } = useAsync(() => dataClient.getFacebookAdsOptions(org, source), [org, source])
    if (error) {
        return (
            <div className="stack" style={{ gap: 8 }}>
                <p className="invite-error" role="alert" style={{ margin: 0 }}>
                    {toDataError(error).message}
                </p>
                <div className="row">
                    <button className="btn" type="button" onClick={onCancel}>
                        Voltar
                    </button>
                </div>
            </div>
        )
    }
    if (!data?.settings) return <LoadingState />
    return (
        <AdsCustomizeForm
            org={org}
            source={source}
            currency={currency}
            options={data}
            initial={data.settings}
            onSaved={onSaved}
            onCancel={onCancel}
        />
    )
}

function AdsCustomizeForm({
    org,
    source,
    currency,
    options,
    initial,
    onSaved,
    onCancel,
}: AdsCustomizeProps & { options: AdsOptions; initial: AdsSettings }) {
    const [settings, setSettings] = useState<AdsSettings>(initial)
    const [sample, setSample] = useState<AdsPreview | null>(null)
    const [busy, setBusy] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const problem = settingsProblem(settings)
    const recollect = needsRecollect(initial, settings)

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

    const preview = () => run(async () => setSample(await dataClient.previewSavedFacebookAds(org, source, settings)))
    const save = () =>
        run(async () => {
            const res = await dataClient.saveFacebookAdsSettings(org, source, settings)
            onSaved(res.recollect)
        })

    return (
        <div className="stack ads-customize" style={{ gap: 12 }}>
            <AdsSettingsForm
                settings={settings}
                onChange={(next) => {
                    setSettings(next)
                    setSample(null)
                }}
                campaigns={options.campaigns}
                conversions={options.conversions}
                currency={currency}
                disabled={busy}
            />
            {recollect && (
                <p className="ads-note" role="status">
                    Isso muda o que é coletado: a coleta busca de novo o histórico (
                    {backfillLabel(settings.backfillDays)}), em segundo plano. Os dados atuais ficam até serem trocados.
                </p>
            )}
            {problem && (
                <p className="invite-error" role="alert" style={{ margin: 0 }}>
                    {problem}
                </p>
            )}
            {sample && <AdsPreviewView preview={sample} currency={currency} />}
            {error && (
                <p className="invite-error" role="alert" style={{ margin: 0 }}>
                    {error}
                </p>
            )}
            <div className="row">
                <button className="btn" type="button" onClick={onCancel} disabled={busy}>
                    Cancelar
                </button>
                <span style={{ flex: 1 }} />
                <button className="btn" type="button" onClick={preview} disabled={problem !== null || busy}>
                    {busy && !sample ? 'Buscando na Meta…' : 'Ver prévia'}
                </button>
                <button className="btn btn-primary" type="button" onClick={save} disabled={problem !== null || busy}>
                    {busy ? 'Salvando…' : 'Salvar personalização'}
                </button>
            </div>
        </div>
    )
}
