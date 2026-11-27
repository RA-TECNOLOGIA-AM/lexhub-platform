import { useMemo, useState } from 'react'
import type { AdsCampaignOption, AdsConversionOption, AdsSettings } from '../../../types/index.ts'
import {
    BACKFILL_OPTIONS,
    BASE_METRICS,
    BREAKDOWN_OPTIONS,
    METRIC_GROUPS,
    count,
    isActive,
    money,
    objectiveLabel,
    statusLabel,
    toggle,
} from './facebookAds.ts'

type AdsSettingsFormProps = {
    settings: AdsSettings
    onChange: (settings: AdsSettings) => void
    campaigns: AdsCampaignOption[]
    conversions: AdsConversionOption[]
    currency: string
    disabled?: boolean
}

// Acima disso a lista de campanhas ganha a busca.
const SEARCH_FROM = 8

// Módulo: a personalização da coleta do Facebook Ads, em seções (resultados, campanhas, métricas,
// detalhamentos, histórico e criativos). Controlado: quem usa guarda o estado (Conectar e Personalizar coleta).
export function AdsSettingsForm({
    settings,
    onChange,
    campaigns,
    conversions,
    currency,
    disabled = false,
}: AdsSettingsFormProps) {
    const set = (patch: Partial<AdsSettings>) => onChange({ ...settings, ...patch })
    const [search, setSearch] = useState('')
    const shown = useMemo(() => {
        const q = search.trim().toLocaleLowerCase('pt-BR')
        return q ? campaigns.filter((c) => c.name.toLocaleLowerCase('pt-BR').includes(q)) : campaigns
    }, [campaigns, search])
    const chosen = settings.campaigns ?? []
    const activeIds = campaigns.filter((c) => isActive(c.status)).map((c) => c.id)

    return (
        <div className="ads-form">
            <fieldset className="ads-section" disabled={disabled}>
                <legend>O que conta como resultado</legend>
                <p className="muted small">
                    As conversões que somam em “Resultados” e no custo por resultado. Os números são dos últimos 30 dias
                    desta conta. Trocar depois não precisa coletar de novo.
                </p>
                <div className="ads-checks">
                    {conversions.map((c) => (
                        <label key={c.type} className="ads-check">
                            <input
                                type="checkbox"
                                checked={settings.conversions.includes(c.type)}
                                onChange={(e) =>
                                    set({ conversions: toggle(settings.conversions, c.type, e.target.checked) })
                                }
                            />
                            <span className="ads-check-text">
                                <span>{c.label}</span>
                                <span className="muted small">
                                    {c.count30 > 0
                                        ? `${count(c.count30)} nos últimos 30 dias`
                                        : 'Nenhuma nos últimos 30 dias'}
                                </span>
                            </span>
                        </label>
                    ))}
                </div>
            </fieldset>

            <fieldset className="ads-section" disabled={disabled}>
                <legend>Campanhas</legend>
                <div className="segmented" role="radiogroup" aria-label="Quais campanhas coletar">
                    <button
                        type="button"
                        role="radio"
                        aria-checked={settings.campaigns === null}
                        className={settings.campaigns === null ? 'on' : undefined}
                        onClick={() => set({ campaigns: null })}
                    >
                        Todas (inclusive as novas)
                    </button>
                    <button
                        type="button"
                        role="radio"
                        aria-checked={settings.campaigns !== null}
                        className={settings.campaigns !== null ? 'on' : undefined}
                        onClick={() => set({ campaigns: settings.campaigns ?? activeIds })}
                    >
                        Só as escolhidas
                    </button>
                </div>
                {settings.campaigns !== null && (
                    <>
                        <div className="ads-campaign-tools">
                            {campaigns.length > SEARCH_FROM && (
                                <input
                                    className="field connect-grow"
                                    type="search"
                                    placeholder="Buscar campanha"
                                    value={search}
                                    onChange={(e) => setSearch(e.target.value)}
                                    aria-label="Buscar campanha"
                                />
                            )}
                            <button className="btn btn-sm" type="button" onClick={() => set({ campaigns: activeIds })}>
                                Só as ativas
                            </button>
                            <button
                                className="btn btn-sm"
                                type="button"
                                onClick={() => set({ campaigns: campaigns.map((c) => c.id) })}
                            >
                                Marcar todas
                            </button>
                            <span className="muted small">
                                {chosen.length} de {campaigns.length} escolhida{chosen.length === 1 ? '' : 's'}
                            </span>
                        </div>
                        <div className="ads-campaigns" role="group" aria-label="Campanhas da conta">
                            {shown.length === 0 && <p className="muted small">Nenhuma campanha com esse nome.</p>}
                            {shown.map((c) => (
                                <label key={c.id} className="ads-campaign">
                                    <input
                                        type="checkbox"
                                        checked={chosen.includes(c.id)}
                                        onChange={(e) => set({ campaigns: toggle(chosen, c.id, e.target.checked) })}
                                    />
                                    <span className="ads-check-text">
                                        <span>{c.name}</span>
                                        <span className="muted small">
                                            {objectiveLabel(c.objective)} · {money(c.spend30, currency)} em 30 dias
                                        </span>
                                    </span>
                                    <span className={`badge ${isActive(c.status) ? 'ok' : 'neutral'}`}>
                                        {statusLabel(c.status)}
                                    </span>
                                </label>
                            ))}
                        </div>
                    </>
                )}
            </fieldset>

            <fieldset className="ads-section" disabled={disabled}>
                <legend>Métricas</legend>
                <label className="ads-check">
                    <input type="checkbox" checked disabled />
                    <span className="ads-check-text">
                        <span>Básico (sempre)</span>
                        <span className="muted small">{BASE_METRICS}. Dá CTR, CPC, CPM e custo por resultado.</span>
                    </span>
                </label>
                {METRIC_GROUPS.map((g) => (
                    <label key={g.key} className="ads-check">
                        <input
                            type="checkbox"
                            checked={settings.metrics.includes(g.key)}
                            onChange={(e) => set({ metrics: toggle(settings.metrics, g.key, e.target.checked) })}
                        />
                        <span className="ads-check-text">
                            <span>{g.label}</span>
                            <span className="muted small">{g.hint}</span>
                        </span>
                    </label>
                ))}
            </fieldset>

            <fieldset className="ads-section" disabled={disabled}>
                <legend>Detalhamentos</legend>
                <p className="muted small">
                    Por campanha e por dia. Cada um guarda uma linha por segmento, então aumenta o espaço usado.
                </p>
                <div className="ads-checks ads-checks-grid">
                    {BREAKDOWN_OPTIONS.map((b) => (
                        <label key={b.key} className="ads-check">
                            <input
                                type="checkbox"
                                checked={settings.breakdowns.includes(b.key)}
                                onChange={(e) =>
                                    set({ breakdowns: toggle(settings.breakdowns, b.key, e.target.checked) })
                                }
                            />
                            <span className="ads-check-text">
                                <span>{b.label}</span>
                                <span className="muted small">
                                    {b.hint} {b.segments}.
                                </span>
                            </span>
                        </label>
                    ))}
                </div>
            </fieldset>

            <fieldset className="ads-section" disabled={disabled}>
                <legend>Histórico</legend>
                <p className="muted small">
                    Quanto buscar para trás na primeira coleta. A Meta guarda 3 anos de totais; o alcance por
                    detalhamento, só 13 meses.
                </p>
                <div className="segmented" role="radiogroup" aria-label="Histórico da primeira coleta">
                    {BACKFILL_OPTIONS.map((o) => (
                        <button
                            key={o.days}
                            type="button"
                            role="radio"
                            aria-checked={settings.backfillDays === o.days}
                            className={settings.backfillDays === o.days ? 'on' : undefined}
                            onClick={() => set({ backfillDays: o.days })}
                        >
                            {o.label}
                        </button>
                    ))}
                </div>
            </fieldset>

            <fieldset className="ads-section" disabled={disabled}>
                <legend>Campanhas, conjuntos e anúncios</legend>
                <p className="muted small">
                    Objetivo, status e orçamento de cada campanha e conjunto são guardados sempre (atualizados uma vez
                    por dia).
                </p>
                <label className="ads-check">
                    <input
                        type="checkbox"
                        checked={settings.creatives}
                        onChange={(e) => set({ creatives: e.target.checked })}
                    />
                    <span className="ads-check-text">
                        <span>Guardar os criativos</span>
                        <span className="muted small">
                            Título, texto, imagem, link e chamada de cada anúncio. O link da imagem da Meta expira; o
                            texto fica.
                        </span>
                    </span>
                </label>
            </fieldset>
        </div>
    )
}
