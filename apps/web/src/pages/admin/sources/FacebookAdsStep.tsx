import { useState } from 'react'
import type {
    AdsOptions,
    AdsPreview,
    AdsSettings,
    AdsTokenInfo,
    ConnectResult,
    FacebookAdsConnectInput,
    SourceCheck,
    Unit,
} from '../../../types/index.ts'
import { Modal } from '../../../components/ui/Modal.tsx'
import { toDataError } from '../../../services/errors.ts'
import { CheckList } from './CheckList.tsx'
import { normalizeAdAccount } from './connectSource.ts'
import { AdsSettingsForm } from './AdsSettingsForm.tsx'
import { AdsPreviewView } from './AdsPreviewView.tsx'
import { AdsAccountPicker, AdsTokenView } from './AdsTokenView.tsx'
import {
    accountsWithoutCampaigns,
    adsSourceName,
    DEFAULT_ADS_SETTINGS,
    defaultConversions,
    mergeOptions,
    settingsForAccount,
    settingsProblem,
} from './facebookAds.ts'

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

// Uma conta escolhida e testada: o nome e a moeda que a Meta devolveu e as opções dela.
type Picked = { id: string; name: string; currency: string; options: AdsOptions }
// O teste ou a gravação de uma conta que não deu certo (a tela mostra as checagens com o nome da conta).
type Failure = { id: string; name: string; checks: SourceCheck[]; message?: string }

// O token do usuário do sistema começa com "EAA" e tem dezenas de caracteres; abaixo disso é engano de cópia.
const MIN_TOKEN = 20

// Módulo: o passo do Facebook Ads, em três etapas. Acesso: o token (a API mostra o que ele permite e as contas
// que ele acessa, pelo nome) e uma ou várias contas. Personalizar: o que coletar (a mesma escolha para todas;
// as campanhas ficam separadas por conta). Prévia: os últimos 7 dias de cada conta. Cada conta escolhida vira
// uma fonte. O token vai só para a API, que guarda cifrado; nada é gravado antes de "Conectar".
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
    const [chosen, setChosen] = useState<string[]>([])
    const [typed, setTyped] = useState('') // "A conta não está na lista": o ID digitado
    const [typing, setTyping] = useState(false)
    const [name, setName] = useState(`Facebook Ads ${unit.name}`)
    const [nameTouched, setNameTouched] = useState(false)
    const [picked, setPicked] = useState<Picked[]>([])
    const [failures, setFailures] = useState<Failure[]>([])
    const [settings, setSettings] = useState<AdsSettings>(DEFAULT_ADS_SETTINGS)
    const [samples, setSamples] = useState<Record<string, AdsPreview>>({})
    const [sampleOf, setSampleOf] = useState<string | null>(null)
    const [busy, setBusy] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const typedId = normalizeAdAccount(typed)
    const accounts = tokenInfo?.accounts ?? []
    const accountIds = [...new Set([...chosen, ...((typing || accounts.length === 0) && typedId ? [typedId] : [])])]
    const accountName = (id: string) =>
        picked.find((p) => p.id === id)?.name ?? accounts.find((a) => a.id === id)?.name ?? id
    const single = accountIds.length === 1
    const merged = mergeOptions(picked.map((p) => ({ account: p.name, options: p.options })))
    const campaignsOf = (p: Picked) => p.options.campaigns.map((c) => c.id)
    const problem =
        settingsProblem(settings) ??
        accountsWithoutCampaigns(
            settings,
            picked.map((p) => ({ name: p.name, campaigns: campaignsOf(p) })),
        )

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

    function choose(ids: string[]) {
        setChosen(ids)
        setPicked([])
        setFailures([])
        // Uma conta só: a fonte ganha o nome dela (enquanto a pessoa não escreve outro).
        const one = ids.length === 1 ? accounts.find((a) => a.id === ids[0]) : undefined
        if (one && !nameTouched) setName(adsSourceName(one.name))
    }

    const read = (value = token) =>
        run(async () => {
            if (value.trim().length < MIN_TOKEN) return
            const info = await readToken(value.trim())
            setTokenInfo(info)
            setPicked([])
            setFailures([])
            setTyping(false)
            // Uma conta livre só: já marcada. Várias: a pessoa marca na lista.
            const free = info.accounts.filter((a) => a.assigned !== false && !a.connectedTo)
            const ids = free.length === 1 ? [free[0].id] : []
            setChosen(ids)
            if (ids.length === 1 && !nameTouched) setName(adsSourceName(free[0].name))
        })

    // Testa cada conta escolhida, uma por vez. Todas passaram: segue para Personalizar.
    const test = () =>
        run(async () => {
            const ok: Picked[] = []
            const bad: Failure[] = []
            for (const id of accountIds) {
                const found = await inspect({ adAccountId: id, token: token.trim() })
                if (found.ok && found.account) {
                    ok.push({ id, name: found.account.name, currency: found.account.currency, options: found })
                } else {
                    bad.push({ id, name: accountName(id), checks: found.checks })
                }
            }
            setPicked(ok)
            setFailures(bad)
            if (bad.length > 0) return
            if (ok.length === 1 && !nameTouched) setName(adsSourceName(ok[0].name))
            const conversions = mergeOptions(ok.map((p) => ({ account: p.name, options: p.options }))).conversions
            setSettings({ ...DEFAULT_ADS_SETTINGS, conversions: defaultConversions(conversions) })
            setSamples({})
            setStage('customize')
        })

    async function loadSample(p: Picked) {
        setSampleOf(p.id)
        if (samples[p.id]) return
        const got = await preview({
            adAccountId: p.id,
            token: token.trim(),
            settings: settingsForAccount(settings, campaignsOf(p)),
        })
        setSamples((s) => ({ ...s, [p.id]: got }))
    }

    const showPreview = () =>
        run(async () => {
            await loadSample(picked[0])
            setStage('preview')
        })

    // Uma fonte por conta, uma de cada vez. As que derem certo saem da lista; as que falharem ficam, com o motivo.
    const save = () =>
        run(async () => {
            const left: Picked[] = []
            const bad: Failure[] = []
            let saved = 0
            for (const p of picked) {
                try {
                    const res = await onSave({
                        connector: 'facebook_ads',
                        name: picked.length === 1 ? name.trim() : adsSourceName(p.name),
                        adAccountId: p.id,
                        token: token.trim(),
                        settings: settingsForAccount(settings, campaignsOf(p)),
                    })
                    if (res.saved) {
                        saved++
                        continue
                    }
                    bad.push({ id: p.id, name: p.name, checks: res.checks })
                } catch (err) {
                    bad.push({ id: p.id, name: p.name, checks: [], message: toDataError(err).message })
                }
                left.push(p)
            }
            if (saved > 0) onSaved()
            if (bad.length === 0) {
                onClose()
                return
            }
            setPicked(left)
            setFailures(bad)
        })

    const tokenReady = token.trim().length >= MIN_TOKEN
    const accessReady = accountIds.length > 0 && tokenReady && (!single || name.trim() !== '')
    const changeSettings = (next: AdsSettings) => {
        setSettings(next)
        setSamples({})
    }
    const currentSample = sampleOf ? samples[sampleOf] : undefined
    const currency = picked.find((p) => p.id === sampleOf)?.currency || picked[0]?.currency || 'BRL'
    const connectLabel = picked.length > 1 ? `Conectar ${picked.length} contas` : 'Conectar conta'

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
                    {busy && tokenInfo
                        ? 'Testando na Meta…'
                        : accountIds.length > 1
                          ? `Testar ${accountIds.length} contas e continuar`
                          : 'Testar e continuar'}
                </button>
            )}
            {stage === 'customize' && (
                <>
                    <button className="btn" type="button" onClick={save} disabled={problem !== null || busy}>
                        {picked.length > 1 ? `Conectar ${picked.length} sem prévia` : 'Conectar sem prévia'}
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
                    {busy ? 'Conectando…' : connectLabel}
                </button>
            )}
        </>
    )

    const subtitle =
        stage !== 'access' && picked.length > 0
            ? `Unidade ${unit.name} (${unit.code}) · ${
                  picked.length === 1 ? `conta ${picked[0].name} (${picked[0].id})` : `${picked.length} contas`
              }`
            : `Unidade ${unit.name} (${unit.code})`

    return (
        <Modal
            title="Conectar fonte · Facebook Ads"
            subtitle={subtitle}
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
                                        setPicked([])
                                        setFailures([])
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
                            <span className="lbl">Contas de anúncios</span>
                            {accounts.length > 0 && (
                                <>
                                    <span className="muted small">
                                        Marque uma ou várias. Cada conta vira uma fonte desta unidade, com a mesma
                                        personalização.
                                    </span>
                                    <AdsAccountPicker
                                        accounts={accounts}
                                        chosen={chosen}
                                        onChange={choose}
                                        disabled={busy}
                                    />
                                </>
                            )}
                            {accounts.length > 0 && !typing && (
                                <button
                                    className="btn btn-sm btn-ghost"
                                    type="button"
                                    style={{ alignSelf: 'flex-start' }}
                                    onClick={() => setTyping(true)}
                                >
                                    A conta não está na lista? Digite o ID
                                </button>
                            )}
                            {(accounts.length === 0 || typing) && (
                                <>
                                    <input
                                        className="field"
                                        value={typed}
                                        spellCheck={false}
                                        autoComplete="off"
                                        placeholder="act_1234567890"
                                        aria-label="ID da conta de anúncios"
                                        onChange={(e) => {
                                            setTyped(e.target.value)
                                            setPicked([])
                                        }}
                                    />
                                    <span className="muted small" role={typed.trim() && !typedId ? 'alert' : undefined}>
                                        {typed.trim() === ''
                                            ? tokenInfo === null
                                                ? 'Leia o token para escolher as contas pelo nome, ou digite o ID (Gerenciador de Anúncios > Configurações da conta).'
                                                : 'Gerenciador de Anúncios > Configurações da conta: o número abaixo do nome da conta.'
                                            : typedId
                                              ? `A API vai usar ${typedId}.`
                                              : 'Use act_ seguido dos números, ou só os números.'}
                                    </span>
                                </>
                            )}
                        </li>
                    </ol>
                    {single ? (
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
                    ) : (
                        accountIds.length > 1 && (
                            <p className="ads-note" role="status">
                                {accountIds.length} fontes vão ser criadas, uma por conta:{' '}
                                {accountIds.map((id) => adsSourceName(accountName(id))).join('; ')}.
                            </p>
                        )
                    )}
                    {tokenInfo && !tokenInfo.ok && <CheckList checks={tokenInfo.checks} />}
                </>
            )}

            {stage === 'customize' && picked.length > 0 && (
                <>
                    <AdsSettingsForm
                        settings={settings}
                        onChange={changeSettings}
                        campaigns={merged.campaigns}
                        conversions={merged.conversions}
                        currency={picked[0].currency || 'BRL'}
                        disabled={busy}
                    />
                    {problem && (
                        <p className="invite-error" role="alert" style={{ margin: 0 }}>
                            {problem}
                        </p>
                    )}
                </>
            )}

            {stage === 'preview' && (
                <>
                    {picked.length > 1 && (
                        <div className="segmented" role="tablist" aria-label="Prévia de qual conta">
                            {picked.map((p) => (
                                <button
                                    key={p.id}
                                    type="button"
                                    role="tab"
                                    aria-selected={sampleOf === p.id}
                                    className={sampleOf === p.id ? 'on' : undefined}
                                    disabled={busy}
                                    onClick={() => run(() => loadSample(p))}
                                >
                                    {p.name}
                                </button>
                            ))}
                        </div>
                    )}
                    {currentSample ? (
                        <AdsPreviewView preview={currentSample} currency={currency} />
                    ) : (
                        <p className="muted small">Buscando na Meta…</p>
                    )}
                    <p className="muted small" style={{ margin: 0 }}>
                        Ao conectar, o LexHub busca o histórico escolhido e depois atualiza os últimos dias a cada 10
                        minutos. Os dados ficam guardados no LexHub, por anúncio e por dia.
                    </p>
                </>
            )}

            {failures.length > 0 && (
                <div className="stack" style={{ gap: 8 }}>
                    {failures.map((f) => (
                        <div key={f.id} className="stack" style={{ gap: 4 }}>
                            <strong className="small">
                                {f.name} ({f.id})
                            </strong>
                            {f.checks.length > 0 && <CheckList checks={f.checks} />}
                            {f.message && (
                                <p className="invite-error" role="alert" style={{ margin: 0 }}>
                                    {f.message}
                                </p>
                            )}
                        </div>
                    ))}
                    {stage !== 'access' && (
                        <p className="muted small" style={{ margin: 0 }}>
                            As contas acima não foram conectadas. As outras já estão na lista de fontes.
                        </p>
                    )}
                </div>
            )}
            {error && (
                <p className="invite-error" role="alert" style={{ margin: 0 }}>
                    {error}
                </p>
            )}
        </Modal>
    )
}
