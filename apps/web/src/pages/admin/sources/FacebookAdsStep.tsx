import { useState } from 'react'
import type {
    AdsOptions,
    AdsPreview,
    AdsSettings,
    AdsTokenAccount,
    AdsTokenInfo,
    ConnectResult,
    FacebookAdsConnectInput,
    Unit,
} from '../../../types/index.ts'
import { Modal } from '../../../components/ui/Modal.tsx'
import { toDataError } from '../../../services/errors.ts'
import { CheckList } from './CheckList.tsx'
import { normalizeAdAccount } from './connectSource.ts'
import { AdsSettingsForm } from './AdsSettingsForm.tsx'
import { AdsPreviewView } from './AdsPreviewView.tsx'
import { AdsAccountPicker, AdsTokenView } from './AdsTokenView.tsx'
import { adsSourceName, DEFAULT_ADS_SETTINGS, defaultConversions, settingsProblem } from './facebookAds.ts'

export type AdsAccessInput = { adAccountId: string; token: string }

type FacebookAdsStepProps = {
    unit: Unit
    readToken: (token: string) => Promise<AdsTokenInfo> // quem é, permissões e as contas (com o nome)
    inspect: (input: AdsAccessInput) => Promise<AdsOptions> // testa a conta e traz as opções dela
    preview: (input: AdsAccessInput & { settings: AdsSettings }) => Promise<AdsPreview>
    onSave: (input: FacebookAdsConnectInput) => Promise<ConnectResult>
    onSaved: () => void
    onBack: () => void
    onClose: () => void
}

type Stage = 'access' | 'customize' | 'preview'
const STAGES: { key: Stage; label: string }[] = [
    { key: 'access', label: 'Acesso' },
    { key: 'customize', label: 'Personalizar' },
    { key: 'preview', label: 'Prévia' },
]

// O token do usuário do sistema começa com "EAA" e tem dezenas de caracteres; abaixo disso é engano de cópia.
const MIN_TOKEN = 20

// Módulo: o passo do Facebook Ads, em três etapas. Acesso: o token (a API mostra o que ele permite e as contas
// que ele acessa, pelo nome) e a conta. Personalizar: o que coletar. Prévia: os últimos 7 dias com essa escolha.
// O token vai só para a API, que guarda cifrado; nada é gravado antes de "Conectar conta".
export function FacebookAdsStep({
    unit,
    readToken,
    inspect,
    preview,
    onSave,
    onSaved,
    onBack,
    onClose,
}: FacebookAdsStepProps) {
    const [stage, setStage] = useState<Stage>('access')
    const [token, setToken] = useState('')
    const [tokenInfo, setTokenInfo] = useState<AdsTokenInfo | null>(null)
    const [account, setAccount] = useState('')
    const [typing, setTyping] = useState(false) // "Outra conta": digitar o ID
    const [name, setName] = useState(`Facebook Ads ${unit.name}`)
    const [nameTouched, setNameTouched] = useState(false)
    const [options, setOptions] = useState<AdsOptions | null>(null)
    const [settings, setSettings] = useState<AdsSettings>(DEFAULT_ADS_SETTINGS)
    const [sample, setSample] = useState<AdsPreview | null>(null)
    const [busy, setBusy] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [result, setResult] = useState<ConnectResult | null>(null)

    const normalized = normalizeAdAccount(account)
    const access = { adAccountId: normalized ?? account.trim(), token: token.trim() }
    const currency = options?.account?.currency || 'BRL'
    const problem = settingsProblem(settings)
    const accounts = tokenInfo?.accounts ?? []

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

    const read = (value = token) =>
        run(async () => {
            if (value.trim().length < MIN_TOKEN) return
            const info = await readToken(value.trim())
            setTokenInfo(info)
            setOptions(null)
            // Uma conta só: já escolhida. Várias: a pessoa escolhe na lista.
            const only = info.accounts.length === 1 ? info.accounts[0] : null
            if (only) choose(only)
            else setTyping(false)
        })

    function choose(a: AdsTokenAccount) {
        setAccount(a.id)
        setTyping(false)
        setOptions(null)
        if (!nameTouched) setName(adsSourceName(a.name))
    }

    const test = () =>
        run(async () => {
            const found = await inspect(access)
            setOptions(found)
            if (!found.ok) return
            if (!nameTouched && found.account) setName(adsSourceName(found.account.name))
            setSettings({ ...DEFAULT_ADS_SETTINGS, conversions: defaultConversions(found.conversions) })
            setSample(null)
            setStage('customize')
        })

    const showPreview = () =>
        run(async () => {
            setSample(await preview({ ...access, settings }))
            setStage('preview')
        })

    const save = () =>
        run(async () => {
            const res = await onSave({ connector: 'facebook_ads', name: name.trim(), ...access, settings })
            setResult(res)
            if (res.saved) {
                onSaved()
                onClose()
            }
        })

    const accountHint =
        account.trim() === ''
            ? 'Gerenciador de Anúncios > Configurações da conta: o número abaixo do nome da conta.'
            : normalized
              ? `A API vai usar ${normalized}.`
              : 'Use act_ seguido dos números, ou só os números.'
    const tokenReady = token.trim().length >= MIN_TOKEN
    const accessReady = normalized !== null && tokenReady && name.trim() !== ''
    const changeSettings = (next: AdsSettings) => {
        setSettings(next)
        setSample(null)
    }

    const footer = (
        <>
            <button
                className="btn"
                type="button"
                disabled={busy}
                onClick={() => (stage === 'access' ? onBack() : setStage(stage === 'preview' ? 'customize' : 'access'))}
            >
                Voltar
            </button>
            <span style={{ flex: 1 }} />
            <button className="btn" type="button" onClick={onClose} disabled={busy}>
                Cancelar
            </button>
            {stage === 'access' && (
                <button className="btn btn-primary" type="button" onClick={test} disabled={!accessReady || busy}>
                    {busy && tokenInfo ? 'Testando na Meta…' : 'Testar e continuar'}
                </button>
            )}
            {stage === 'customize' && (
                <>
                    <button className="btn" type="button" onClick={save} disabled={problem !== null || busy}>
                        Conectar sem prévia
                    </button>
                    <button
                        className="btn btn-primary"
                        type="button"
                        onClick={showPreview}
                        disabled={problem !== null || busy}
                    >
                        {busy ? 'Buscando na Meta…' : 'Ver prévia'}
                    </button>
                </>
            )}
            {stage === 'preview' && (
                <button className="btn btn-primary" type="button" onClick={save} disabled={busy}>
                    {busy ? 'Conectando…' : 'Conectar conta'}
                </button>
            )}
        </>
    )

    return (
        <Modal
            title="Conectar fonte · Facebook Ads"
            subtitle={
                options?.account && stage !== 'access'
                    ? `Unidade ${unit.name} (${unit.code}) · conta ${options.account.name} (${options.account.id})`
                    : `Unidade ${unit.name} (${unit.code})`
            }
            className="connect-dialog ads-dialog"
            onClose={onClose}
            footer={footer}
        >
            <ol className="ads-stepper" aria-label="Etapas">
                {STAGES.map((s, i) => {
                    const at = STAGES.findIndex((x) => x.key === stage)
                    const state = i < at ? 'done' : i === at ? 'current' : 'next'
                    return (
                        <li
                            key={s.key}
                            className={`ads-step ${state}`}
                            aria-current={state === 'current' ? 'step' : undefined}
                        >
                            <span className="ads-step-n">{i + 1}</span>
                            {s.label}
                        </li>
                    )
                })}
            </ol>

            {stage === 'access' && (
                <>
                    <ol className="connect-steps">
                        <li>
                            <strong>Crie o acesso na Meta</strong>
                            <span className="muted small">
                                No Gerenciador de Negócios: Configurações do negócio &gt; Usuários do sistema. Crie um
                                usuário do sistema, atribua a ele as contas de anúncios (ver desempenho) e o app do
                                LexHub, e gere um token com a permissão ads_read. O LexHub só lê relatórios e guarda o
                                token cifrado.
                            </span>
                        </li>
                        <li>
                            <span className="lbl">Token do usuário do sistema</span>
                            <span className="connect-row">
                                <input
                                    className="field connect-grow"
                                    type="password"
                                    value={token}
                                    spellCheck={false}
                                    autoComplete="off"
                                    placeholder="EAA..."
                                    aria-label="Token do usuário do sistema"
                                    onChange={(e) => {
                                        setToken(e.target.value)
                                        setTokenInfo(null)
                                        setOptions(null)
                                    }}
                                    onPaste={(e) => {
                                        const text = e.clipboardData.getData('text')
                                        if (text.trim().length >= MIN_TOKEN) window.setTimeout(() => read(text), 0)
                                    }}
                                />
                                <button
                                    className="btn"
                                    type="button"
                                    onClick={() => read()}
                                    disabled={!tokenReady || busy}
                                >
                                    {busy && !tokenInfo ? 'Lendo…' : 'Ler token'}
                                </button>
                            </span>
                            <span className="muted small">
                                Ao ler, a tela mostra o que o token permite e as contas de anúncios que ele acessa.
                            </span>
                        </li>
                        {tokenInfo && (
                            <li>
                                <strong>O que o token permite</strong>
                                <AdsTokenView info={tokenInfo} />
                            </li>
                        )}
                        <li>
                            <span className="lbl">Conta de anúncios</span>
                            {accounts.length > 0 && (
                                <AdsAccountPicker
                                    accounts={accounts}
                                    chosen={typing ? null : (normalized ?? null)}
                                    onChoose={choose}
                                    disabled={busy}
                                />
                            )}
                            {accounts.length > 0 && !typing && (
                                <button
                                    className="btn btn-sm btn-ghost"
                                    type="button"
                                    style={{ alignSelf: 'flex-start' }}
                                    onClick={() => {
                                        setTyping(true)
                                        setAccount('')
                                    }}
                                >
                                    A conta não está na lista? Digite o ID
                                </button>
                            )}
                            {(accounts.length === 0 || typing) && (
                                <>
                                    <input
                                        className="field"
                                        value={account}
                                        spellCheck={false}
                                        autoComplete="off"
                                        placeholder="act_1234567890"
                                        aria-label="ID da conta de anúncios"
                                        onChange={(e) => {
                                            setAccount(e.target.value)
                                            setOptions(null)
                                        }}
                                    />
                                    <span
                                        className="muted small"
                                        role={account.trim() && !normalized ? 'alert' : undefined}
                                    >
                                        {tokenInfo === null
                                            ? `Leia o token para escolher a conta pelo nome, ou digite o ID. ${accountHint}`
                                            : accountHint}
                                    </span>
                                </>
                            )}
                        </li>
                    </ol>
                    <label>
                        <span className="lbl">Nome da fonte</span>
                        <input
                            className="field"
                            value={name}
                            onChange={(e) => {
                                setName(e.target.value)
                                setNameTouched(true)
                            }}
                        />
                    </label>
                    {tokenInfo && !tokenInfo.ok && <CheckList checks={tokenInfo.checks} />}
                    {options && <CheckList checks={options.checks} />}
                </>
            )}

            {stage === 'customize' && options && (
                <>
                    <CheckList checks={options.checks} />
                    <AdsSettingsForm
                        settings={settings}
                        onChange={changeSettings}
                        campaigns={options.campaigns}
                        conversions={options.conversions}
                        currency={currency}
                        disabled={busy}
                    />
                    {problem && (
                        <p className="invite-error" role="alert" style={{ margin: 0 }}>
                            {problem}
                        </p>
                    )}
                </>
            )}

            {stage === 'preview' && sample && (
                <>
                    <AdsPreviewView preview={sample} currency={currency} />
                    <p className="muted small" style={{ margin: 0 }}>
                        Ao conectar, o LexHub busca o histórico escolhido e depois atualiza os últimos dias a cada 10
                        minutos. Os dados ficam guardados no LexHub, por anúncio e por dia.
                    </p>
                </>
            )}

            {result && !result.saved && <CheckList checks={result.checks} />}
            {error && (
                <p className="invite-error" role="alert" style={{ margin: 0 }}>
                    {error}
                </p>
            )}
        </Modal>
    )
}
