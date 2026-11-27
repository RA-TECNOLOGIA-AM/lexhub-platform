import type {
    AdsBackfillDays,
    AdsBreakdown,
    AdsConversionOption,
    AdsMetricGroup,
    AdsSettings,
} from '../../../types/index.ts'

// Módulo: as regras e os rótulos da fonte Facebook Ads, sem React (testados em facebookAds.test.ts).
// Os nomes da Meta (status, objetivo, plataforma...) chegam em inglês: aqui viram português.

export const CONVERSATION = 'onsite_conversion.messaging_conversation_started_7d'

// O padrão de uma conta nova: alcance, leads + conversas como resultado, todas as campanhas, 3 anos.
export const DEFAULT_ADS_SETTINGS: AdsSettings = {
    metrics: ['reach'],
    conversions: ['lead', CONVERSATION],
    campaigns: null,
    breakdowns: [],
    backfillDays: 1095,
    creatives: true,
}

// O que vem sempre (não dá para desligar): o básico para custo por resultado, CTR, CPC e CPM.
export const BASE_METRICS =
    'Gasto, impressões, cliques, cliques no link e de saída, visualizações da página, leads e conversas'

export const METRIC_GROUPS: { key: AdsMetricGroup; label: string; hint: string }[] = [
    { key: 'reach', label: 'Alcance e frequência', hint: 'Quantas pessoas viram e quantas vezes, em média.' },
    {
        key: 'video',
        label: 'Vídeo',
        hint: 'Reproduções, ThruPlays e quanto foi assistido (25%, 50%, 75% e 100%).',
    },
    {
        key: 'quality',
        label: 'Qualidade do anúncio',
        hint: 'Os rankings da Meta de qualidade, engajamento e conversão (por anúncio).',
    },
]

export const BREAKDOWN_OPTIONS: { key: AdsBreakdown; label: string; hint: string; segments: string }[] = [
    {
        key: 'age_gender',
        label: 'Idade e gênero',
        hint: 'Gasto e resultados por faixa etária e gênero.',
        segments: 'até ~20 segmentos',
    },
    {
        key: 'platform',
        label: 'Plataforma e posicionamento',
        hint: 'Facebook, Instagram, Messenger e onde apareceu (Feed, Stories, Reels...).',
        segments: 'até ~15 segmentos',
    },
    { key: 'region', label: 'Região', hint: 'Por estado.', segments: 'até ~27 segmentos' },
    {
        key: 'device',
        label: 'Dispositivo',
        hint: 'Celular Android, iPhone, computador, tablet.',
        segments: 'até ~6 segmentos',
    },
]

export const BACKFILL_OPTIONS: { days: AdsBackfillDays; label: string }[] = [
    { days: 90, label: '3 meses' },
    { days: 365, label: '1 ano' },
    { days: 1095, label: '3 anos (máximo da Meta)' },
]

const STATUS: Record<string, string> = {
    ACTIVE: 'Ativa',
    PAUSED: 'Pausada',
    ARCHIVED: 'Arquivada',
    DELETED: 'Excluída',
    CAMPAIGN_PAUSED: 'Campanha pausada',
    ADSET_PAUSED: 'Conjunto pausado',
    IN_PROCESS: 'Em processamento',
    WITH_ISSUES: 'Com problemas',
    DISAPPROVED: 'Reprovada',
    PENDING_REVIEW: 'Em análise',
    PREAPPROVED: 'Pré-aprovada',
    PENDING_BILLING_INFO: 'Falta pagamento',
}

const OBJECTIVE: Record<string, string> = {
    OUTCOME_LEADS: 'Cadastros',
    OUTCOME_ENGAGEMENT: 'Engajamento',
    OUTCOME_TRAFFIC: 'Tráfego',
    OUTCOME_AWARENESS: 'Reconhecimento',
    OUTCOME_SALES: 'Vendas',
    OUTCOME_APP_PROMOTION: 'Promoção do app',
    LEAD_GENERATION: 'Cadastros',
    MESSAGES: 'Mensagens',
    LINK_CLICKS: 'Tráfego',
    CONVERSIONS: 'Conversões',
    POST_ENGAGEMENT: 'Engajamento',
    REACH: 'Alcance',
    BRAND_AWARENESS: 'Reconhecimento',
    VIDEO_VIEWS: 'Visualizações de vídeo',
}

const GENDER: Record<string, string> = { female: 'Mulheres', male: 'Homens', unknown: 'Não informado' }
const PLATFORM: Record<string, string> = {
    facebook: 'Facebook',
    instagram: 'Instagram',
    messenger: 'Messenger',
    audience_network: 'Audience Network',
    threads: 'Threads',
    whatsapp: 'WhatsApp',
}
const POSITION: Record<string, string> = {
    feed: 'Feed',
    instagram_stories: 'Stories',
    facebook_stories: 'Stories',
    story: 'Stories',
    instagram_reels: 'Reels',
    facebook_reels: 'Reels',
    facebook_reels_overlay: 'Reels (sobreposição)',
    instagram_explore: 'Explorar',
    instagram_explore_grid_home: 'Explorar (grade)',
    instagram_profile_feed: 'Feed do perfil',
    instagram_search: 'Busca',
    marketplace: 'Marketplace',
    video_feeds: 'Feed de vídeos',
    instream_video: 'Vídeo in-stream',
    search: 'Busca',
    right_hand_column: 'Coluna da direita',
    messenger_inbox: 'Caixa de entrada',
    messenger_stories: 'Stories',
    an_classic: 'Clássico',
    classic: 'Clássico',
    rewarded_video: 'Vídeo com recompensa',
    threads_feed: 'Feed',
}
const DEVICE: Record<string, string> = {
    android_smartphone: 'Celular Android',
    android_tablet: 'Tablet Android',
    iphone: 'iPhone',
    ipad: 'iPad',
    ipod: 'iPod',
    desktop: 'Computador',
    other: 'Outro',
}

// Os nomes das conversões mais comuns (a lista completa vem da API nas opções da conta).
const CONVERSION_LABELS: Record<string, string> = {
    lead: 'Leads (formulário + site)',
    'onsite_conversion.lead_grouped': 'Leads de formulário da Meta',
    'offsite_conversion.fb_pixel_lead': 'Leads no site (pixel)',
    [CONVERSATION]: 'Conversas iniciadas',
    'onsite_conversion.messaging_first_reply': 'Primeira resposta em conversa',
    link_click: 'Cliques no link',
    landing_page_view: 'Visualizações da página de destino',
    post_engagement: 'Engajamento com a publicação',
    video_view: 'Visualizações de vídeo (3 s)',
    complete_registration: 'Cadastros concluídos',
    contact: 'Contatos',
    schedule: 'Agendamentos',
    purchase: 'Compras',
}
export const conversionLabel = (type: string): string => CONVERSION_LABELS[type] ?? type

export const statusLabel = (status: string | null | undefined): string =>
    status ? (STATUS[status] ?? status) : 'Sem status'
export const objectiveLabel = (objective: string | null | undefined): string =>
    objective ? (OBJECTIVE[objective] ?? objective) : '—'
export const isActive = (status: string | null | undefined) => status === 'ACTIVE'

// O nome de um segmento na tela: ['25-34', 'female'] -> '25-34 · Mulheres'; ['instagram', 'instagram_reels']
// -> 'Instagram · Reels'.
export function segmentLabel(key: AdsBreakdown, segment: string[]): string {
    const [a = '', b = ''] = segment
    if (key === 'age_gender') return [a || '?', GENDER[b] ?? b].filter(Boolean).join(' · ')
    if (key === 'platform') return [PLATFORM[a] ?? a, POSITION[b] ?? b].filter(Boolean).join(' · ')
    if (key === 'device') return DEVICE[a] ?? a
    return a || 'Não informado'
}

export const breakdownLabel = (key: AdsBreakdown) => BREAKDOWN_OPTIONS.find((b) => b.key === key)?.label ?? key
export const backfillLabel = (days: number) => BACKFILL_OPTIONS.find((b) => b.days === days)?.label ?? `${days} dias`

// A personalização guardada em app.data_sources.config (snake_case) no formato da tela.
// Fonte conectada sem personalização (ou campo faltando) = o padrão.
export function settingsFromConfig(config: Record<string, unknown>): AdsSettings {
    const list = (v: unknown) => (Array.isArray(v) ? v.map(String) : null)
    const metrics = list(config.metrics)
    const breakdowns = list(config.breakdowns)
    const conversions = list(config.conversions)
    const backfill = Number(config.backfill_days)
    return {
        metrics: (metrics ?? DEFAULT_ADS_SETTINGS.metrics).filter((m): m is AdsMetricGroup =>
            METRIC_GROUPS.some((g) => g.key === m),
        ),
        conversions: conversions?.length ? conversions : DEFAULT_ADS_SETTINGS.conversions,
        campaigns: list(config.campaigns),
        breakdowns: (breakdowns ?? []).filter((b): b is AdsBreakdown => BREAKDOWN_OPTIONS.some((o) => o.key === b)),
        backfillDays: BACKFILL_OPTIONS.some((o) => o.days === backfill)
            ? (backfill as AdsBackfillDays)
            : DEFAULT_ADS_SETTINGS.backfillDays,
        creatives: config.creatives === undefined ? true : Boolean(config.creatives),
    }
}

// As conversões padrão de uma conta: leads e conversas, se a conta tem; senão a que mais aconteceu.
export function defaultConversions(options: AdsConversionOption[]): string[] {
    const happened = options.filter((o) => o.count30 > 0).map((o) => o.type)
    const wanted = DEFAULT_ADS_SETTINGS.conversions.filter((t) => happened.includes(t))
    if (wanted.length > 0) return wanted
    return happened.length > 0 ? [happened[0]] : ['lead']
}

// O que impede salvar (null = pode).
export function settingsProblem(settings: AdsSettings): string | null {
    if (settings.conversions.length === 0) return 'Escolha ao menos uma conversão para contar como resultado.'
    if (settings.campaigns !== null && settings.campaigns.length === 0) {
        return 'Escolha ao menos uma campanha (ou volte para "Todas as campanhas").'
    }
    return null
}

// Muda o que é coletado (a coleta refaz o histórico)? Só conversões e criativos não mudam (mesma regra da API).
export function needsRecollect(before: AdsSettings, after: AdsSettings): boolean {
    const same = (a: readonly string[] | null, b: readonly string[] | null) =>
        a === null || b === null ? a === b : a.length === b.length && a.every((x) => b.includes(x))
    return (
        !same(before.metrics, after.metrics) ||
        !same(before.campaigns, after.campaigns) ||
        !same(before.breakdowns, after.breakdowns) ||
        before.backfillDays !== after.backfillDays
    )
}

// O nome que a fonte ganha ao escolher uma conta (enquanto a pessoa não escreve outro).
export const adsSourceName = (accountName: string) => `Facebook Ads · ${accountName}`.slice(0, 80)

// Liga/desliga um item numa lista (checkbox).
export function toggle<T>(list: readonly T[], item: T, on: boolean): T[] {
    return on ? (list.includes(item) ? [...list] : [...list, item]) : list.filter((x) => x !== item)
}

// Uma linha por parte da personalização (o resumo em Personalização, no detalhe da fonte).
export function describeSettings(settings: AdsSettings, conversionLabel: (type: string) => string): [string, string][] {
    const metrics = ['Básico', ...METRIC_GROUPS.filter((g) => settings.metrics.includes(g.key)).map((g) => g.label)]
    return [
        ['Resultados', settings.conversions.map(conversionLabel).join(', ')],
        [
            'Campanhas',
            settings.campaigns === null
                ? 'Todas (inclusive as novas)'
                : `${settings.campaigns.length} escolhida${settings.campaigns.length === 1 ? '' : 's'}`,
        ],
        ['Métricas', metrics.join(', ')],
        ['Detalhamentos', settings.breakdowns.map(breakdownLabel).join(', ') || 'Nenhum'],
        ['Histórico', backfillLabel(settings.backfillDays)],
        ['Criativos', settings.creatives ? 'Guardados' : 'Não guardados'],
    ]
}

// --- Números na tela -------------------------------------------------------------------------------

export function money(value: number, currency = 'BRL'): string {
    try {
        return value.toLocaleString('pt-BR', { style: 'currency', currency: currency || 'BRL' })
    } catch {
        return `${currency} ${value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    }
}

export const count = (value: number | null | undefined): string =>
    value === null || value === undefined ? '—' : Math.round(value).toLocaleString('pt-BR')

// Custo por algo (custo por resultado, CPC): sem o divisor, '—'.
export const costPer = (spend: number, n: number, currency = 'BRL'): string =>
    n > 0 ? money(spend / n, currency) : '—'

// CTR (%), com 2 casas.
export const ctr = (clicks: number, impressions: number): string =>
    impressions > 0
        ? `${((clicks / impressions) * 100).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}%`
        : '—'

// CPM: custo por mil impressões.
export const cpm = (spend: number, impressions: number, currency = 'BRL'): string =>
    impressions > 0 ? money((spend / impressions) * 1000, currency) : '—'

// '2026-11-25' -> '25/11/2026'
export const dateLabel = (iso: string | null | undefined): string =>
    iso && /^\d{4}-\d{2}-\d{2}/.test(iso) ? `${iso.slice(8, 10)}/${iso.slice(5, 7)}/${iso.slice(0, 4)}` : '—'
