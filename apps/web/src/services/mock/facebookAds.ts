import type {
    AdsBreakdown,
    AdsCapabilityStatus,
    AdsCampaignOption,
    AdsConversionOption,
    AdsPreview,
    AdsSettings,
    AdsSummary,
    AdsTokenAccount,
    AdsTokenInfo,
    AdsTotals,
    SourceCheck,
} from '../../types/index.ts'

// Facebook Ads no mock: token, contas, campanhas, conversões, prévia e resumo fictícios, no formato da API
// (app/facebook_ads.py). Para treinar os caminhos pelo token:
//   com 'errado' = recusado pela Meta; com 'semconta' = sem conta de anúncios; com 'gerencia' = pode alterar
//   anúncios (aviso); com 'leads' = pode baixar leads de formulário.

export const CONVERSATION = 'onsite_conversion.messaging_conversation_started_7d'

const ACCOUNTS: AdsTokenAccount[] = [
    {
        id: 'act_1234567891',
        name: 'NG · Captação Previdenciária',
        currency: 'BRL',
        timezone: 'America/Manaus',
        status: 'ativa',
        active: true,
        business: 'LexGroup',
        spent: 482_310.55,
    },
    {
        id: 'act_9876543212',
        name: 'LA Advogados · Anúncios',
        currency: 'BRL',
        timezone: 'America/Manaus',
        status: 'ativa',
        active: true,
        business: 'LexGroup',
        spent: 96_420.1,
    },
    {
        id: 'act_5550001110',
        name: 'Conta antiga (2023)',
        currency: 'BRL',
        timezone: 'America/Sao_Paulo',
        status: 'desativada',
        active: false,
        business: 'LexGroup',
        spent: 12_004.9,
    },
    // O negócio tem a conta, mas ela não foi atribuída ao usuário do token (aparece bloqueada).
    {
        id: 'act_4443332221',
        name: 'RJ · Anúncios Rio',
        currency: 'BRL',
        timezone: 'America/Sao_Paulo',
        status: 'ativa',
        active: true,
        business: 'LexGroup',
        spent: 58_900,
        assigned: false,
    },
]

export const adsAccountName = (id: string) => ACCOUNTS.find((a) => a.id === id)?.name ?? `Anúncios ${id.slice(-4)}`

// As campanhas de uma conta: as mesmas do exemplo, com ids próprios por conta (os ids da Meta são únicos)
// e o gasto proporcional ao tamanho da conta.
function campaignsOf(account: string): AdsCampaignOption[] {
    const suffix = account.replace(/\D/g, '').slice(-3)
    const scale = account === 'act_1234567891' || !ACCOUNTS.some((a) => a.id === account) ? 1 : 0.3
    return CAMPAIGNS.map((c) => ({
        ...c,
        id: c.id.slice(0, -3) + suffix.padStart(3, '0') + c.id.slice(-1),
        spend30: Math.round(c.spend30 * scale * 100) / 100,
    }))
}

const CAMPAIGNS: AdsCampaignOption[] = [
    {
        id: '120210000000001',
        name: 'Captação BPC/LOAS · Manaus',
        status: 'ACTIVE',
        objective: 'OUTCOME_LEADS',
        spend30: 4820.5,
    },
    {
        id: '120210000000002',
        name: 'WhatsApp · Revisão da aposentadoria',
        status: 'ACTIVE',
        objective: 'OUTCOME_ENGAGEMENT',
        spend30: 3110.2,
    },
    {
        id: '120210000000003',
        name: 'Auxílio-doença · Interior do AM',
        status: 'ACTIVE',
        objective: 'OUTCOME_LEADS',
        spend30: 1675.9,
    },
    {
        id: '120210000000004',
        name: 'Remarketing do site',
        status: 'PAUSED',
        objective: 'OUTCOME_TRAFFIC',
        spend30: 412,
    },
    {
        id: '120210000000005',
        name: 'Institucional · Vídeo do escritório',
        status: 'PAUSED',
        objective: 'OUTCOME_AWARENESS',
        spend30: 0,
    },
]

const CONVERSIONS: AdsConversionOption[] = [
    { type: CONVERSATION, label: 'Conversas iniciadas (WhatsApp, Messenger, Direct)', count30: 642 },
    { type: 'lead', label: 'Leads (formulário + site)', count30: 318 },
    { type: 'onsite_conversion.lead_grouped', label: 'Leads de formulário da Meta', count30: 301 },
    { type: 'offsite_conversion.fb_pixel_lead', label: 'Leads no site (pixel)', count30: 17 },
    { type: 'landing_page_view', label: 'Visualizações da página de destino', count30: 2210 },
    { type: 'link_click', label: 'Cliques no link', count30: 5874 },
    { type: 'video_view', label: 'Visualizações de vídeo (3 s)', count30: 15_230 },
    { type: 'post_engagement', label: 'Engajamento com a publicação', count30: 21_004 },
]

const check = (key: SourceCheck['key'], ok: boolean, message: string): SourceCheck => ({
    key,
    ok,
    message,
    ms: 60,
    severity: 'error',
    skipped: false,
})

// inUse: as contas já ligadas a uma fonte (conta -> 'Organização · UNIDADE'), como a API marca.
export function adsTokenInfo(token: string, inUse: Record<string, string> = {}): AdsTokenInfo {
    const empty = {
        user: null,
        tokenType: null,
        expiresAt: null,
        neverExpires: null,
        app: null,
        permissions: [],
        capabilities: [],
        accounts: [],
        businesses: [],
    }
    const net = check('network', true, 'A API alcançou graph.facebook.com')
    if (token.includes('errado')) {
        const login = check(
            'login',
            false,
            'A Meta recusou o token (inválido, expirado ou revogado). Gere um novo token do usuário do sistema.',
        )
        return { ok: false, checks: [net, login], ...empty }
    }
    const manage = token.includes('gerencia')
    const leads = token.includes('leads')
    const noAccount = token.includes('semconta')
    const granted = ['ads_read', 'business_management', ...(manage ? ['ads_management'] : [])]
    if (leads) granted.push('leads_retrieval', 'pages_manage_ads', 'pages_show_list')
    const labels: Record<string, string> = {
        ads_read: 'Ler relatórios de anúncios',
        ads_management: 'Gerenciar anúncios',
        business_management: 'Gerenciar negócios',
        leads_retrieval: 'Baixar leads de formulário',
        pages_manage_ads: 'Anúncios das páginas',
        pages_show_list: 'Listar páginas',
    }
    const accounts = noAccount ? [] : ACCOUNTS.map((a) => ({ assigned: true, ...a, connectedTo: inUse[a.id] ?? null }))
    const readable = accounts.filter((a) => a.assigned !== false)
    const status = (on: boolean): AdsCapabilityStatus => (on ? 'available' : 'missing')
    return {
        ok: readable.length > 0,
        checks: [
            net,
            check('login', true, 'Token aceito pela Meta (usuário Coletor LexHub)'),
            readable.length > 0
                ? check(
                      'read',
                      true,
                      `${readable.length} conta(s) de anúncios com acesso; ${accounts.length - readable.length} do negócio sem acesso aos relatórios`,
                  )
                : check(
                      'read',
                      false,
                      'O token não acessa nenhuma conta de anúncios. No Gerenciador de Negócios, atribua a conta ao usuário do sistema.',
                  ),
        ],
        user: { id: '61550000000001', name: 'Coletor LexHub' },
        tokenType: 'Usuário do sistema',
        expiresAt: null,
        neverExpires: true,
        app: 'LexHub Ads',
        permissions: granted.map((name) => ({ name, label: labels[name] ?? name, granted: true })),
        capabilities: [
            {
                key: 'insights',
                label: 'Relatórios de anúncios',
                status: 'used',
                detail: `Métricas, detalhamentos, campanhas e criativos de ${readable.length} conta(s) de anúncios`,
            },
            {
                key: 'manage',
                label: 'Criar e alterar anúncios',
                status: manage ? 'warn' : 'missing',
                detail: manage
                    ? 'O token pode alterar anúncios. O LexHub só lê: para menos risco, gere o token só com ads_read'
                    : 'Não pode (melhor assim: o LexHub só lê)',
            },
            {
                key: 'business',
                label: 'Gerenciadores de Negócios',
                status: status(true),
                detail: 'Vê 1 negócio(s); o LexHub mostra o negócio de cada conta',
            },
            {
                key: 'leads',
                label: 'Dados dos leads de formulário',
                status: status(leads),
                detail: leads
                    ? 'O token permite baixar nome, telefone e e-mail dos formulários; o LexHub ainda não coleta'
                    : 'Precisa de leads_retrieval e pages_manage_ads, com revisão do app pela Meta',
            },
            {
                key: 'pages',
                label: 'Páginas do Facebook',
                status: status(leads),
                detail: leads
                    ? 'O token lê as páginas (seguidores, alcance orgânico); o LexHub ainda não coleta'
                    : 'Opcional: pages_show_list e pages_read_engagement',
            },
            {
                key: 'instagram',
                label: 'Contas do Instagram',
                status: 'missing',
                detail: 'Opcional: instagram_basic e instagram_manage_insights',
            },
        ],
        accounts,
        businesses: [{ id: '1000000000001', name: 'LexGroup' }],
    }
}

export const adsOptions = (account = 'act_1234567891') => ({
    campaigns: campaignsOf(account),
    conversions: CONVERSIONS.map((c) => ({ ...c })),
})

// Números de um gasto (proporções de uma conta de captação jurídica).
function totalsFor(spend: number, settings: AdsSettings): AdsTotals {
    const impressions = Math.round(spend * 52)
    const clicks = Math.round(impressions * 0.031)
    const linkClicks = Math.round(clicks * 0.66)
    const leads = Math.round(spend / 38)
    const conversations = Math.round(spend / 19)
    const by: Record<string, number> = {
        lead: leads,
        'onsite_conversion.lead_grouped': Math.round(leads * 0.95),
        'offsite_conversion.fb_pixel_lead': Math.round(leads * 0.05),
        [CONVERSATION]: conversations,
        landing_page_view: Math.round(linkClicks * 0.8),
        link_click: linkClicks,
        video_view: Math.round(impressions * 0.2),
        post_engagement: Math.round(impressions * 0.26),
    }
    return {
        spend: Math.round(spend * 100) / 100,
        impressions,
        clicks,
        linkClicks,
        leads,
        conversations,
        results: settings.conversions.reduce((sum, t) => sum + (by[t] ?? 0), 0),
        reach: settings.metrics.includes('reach') ? Math.round(impressions / 1.6) : null,
        thruplays: settings.metrics.includes('video') ? Math.round(impressions * 0.12) : null,
    }
}

const SEGMENTS: Record<AdsBreakdown, [string[], number][]> = {
    age_gender: [
        [['35-44', 'female'], 0.22],
        [['45-54', 'female'], 0.19],
        [['25-34', 'female'], 0.14],
        [['55-64', 'female'], 0.12],
        [['35-44', 'male'], 0.1],
        [['45-54', 'male'], 0.09],
        [['55-64', 'male'], 0.08],
        [['65+', 'female'], 0.06],
    ],
    platform: [
        [['facebook', 'feed'], 0.34],
        [['instagram', 'instagram_reels'], 0.21],
        [['instagram', 'feed'], 0.17],
        [['facebook', 'facebook_reels'], 0.11],
        [['instagram', 'instagram_stories'], 0.1],
        [['messenger', 'messenger_inbox'], 0.04],
        [['audience_network', 'classic'], 0.03],
    ],
    region: [
        [['Amazonas', ''], 0.71],
        [['Pará', ''], 0.12],
        [['Roraima', ''], 0.07],
        [['Acre', ''], 0.05],
        [['Rondônia', ''], 0.05],
    ],
    device: [
        [['android_smartphone', ''], 0.68],
        [['iphone', ''], 0.24],
        [['desktop', ''], 0.05],
        [['ipad', ''], 0.03],
    ],
}

const chosenCampaigns = (settings: AdsSettings, account: string) =>
    campaignsOf(account).filter((c) => settings.campaigns === null || settings.campaigns.includes(c.id))

export function adsPreview(settings: AdsSettings, account = 'act_1234567891'): AdsPreview {
    const week = (c: AdsCampaignOption) => (c.spend30 * 7) / 30
    const campaigns = chosenCampaigns(settings, account)
        .filter((c) => c.spend30 > 0)
        .map((c) => ({ id: c.id, name: c.name, ...totalsFor(week(c), settings) }))
        .sort((a, b) => b.spend - a.spend)
    const spend = campaigns.reduce((sum, c) => sum + c.spend, 0)
    const until = new Date(Date.now() - 86_400_000)
    const since = new Date(until.getTime() - 6 * 86_400_000)
    const iso = (d: Date) => d.toISOString().slice(0, 10)
    return {
        since: iso(since),
        until: iso(until),
        totals: totalsFor(spend, settings),
        campaigns,
        breakdowns: settings.breakdowns.map((key) => ({
            key,
            rows: SEGMENTS[key].map(([segment, share]) => ({ segment, ...totalsFor(spend * share, settings) })),
        })),
        ads: settings.creatives
            ? campaigns.slice(0, 4).map((c, i) => ({
                  id: `12022000000000${i + 1}`,
                  name: `Anúncio ${i + 1} · ${c.name}`,
                  campaignName: c.name,
                  creative: {
                      id: `9${i}`,
                      title: [
                          'Seu benefício foi negado?',
                          'Revise sua aposentadoria',
                          'Afastado pelo INSS?',
                          'Fale com a gente',
                      ][i],
                      body: 'Atendimento gratuito e sem sair de casa. Fale agora com um advogado pelo WhatsApp.',
                      linkUrl: 'https://wa.me/5592999990000',
                      callToAction: 'WHATSAPP_MESSAGE',
                  },
                  ...totalsFor(c.spend * 0.6, settings),
              }))
            : [],
    }
}

// O resumo do que está guardado. `progress` (0 a 1): quanto do histórico a coleta já trouxe.
export function adsSummary(settings: AdsSettings, progress: number, account = 'act_1234567891'): AdsSummary {
    const day = 86_400_000
    const iso = (ms: number) => new Date(ms).toISOString().slice(0, 10)
    const first = Date.now() - settings.backfillDays * day
    const covered = first + (Date.now() - first) * Math.min(progress, 1)
    const rows = Math.round(settings.backfillDays * 21 * Math.min(progress, 1))
    const campaigns = chosenCampaigns(settings, account)
    const spend = campaigns.reduce((sum, c) => sum + c.spend30, 0)
    const t = totalsFor(spend, settings)
    const factor: Record<AdsBreakdown, number> = { age_gender: 14, platform: 9, region: 6, device: 4 }
    return {
        firstDay: rows > 0 ? iso(first) : null,
        lastDay: rows > 0 ? iso(covered) : null,
        rows,
        breakdownRows: Object.fromEntries(
            settings.breakdowns.map((b) => [
                b,
                Math.round(settings.backfillDays * factor[b] * 3 * Math.min(progress, 1)),
            ]),
        ),
        entities: {
            campaigns: campaigns.length,
            activeCampaigns: campaigns.filter((c) => c.status === 'ACTIVE').length,
            adsets: campaigns.length * 2,
            ads: campaigns.length * 5,
            creatives: settings.creatives ? campaigns.length * 5 : 0,
        },
        last30: {
            spend: t.spend,
            impressions: t.impressions,
            clicks: t.clicks,
            linkClicks: t.linkClicks,
            landingPageViews: Math.round(t.linkClicks * 0.8),
            leads: t.leads,
            conversations: t.conversations,
            results: t.results,
        },
        topCampaigns: campaigns
            .filter((c) => c.spend30 > 0)
            .map((c) => {
                const ct = totalsFor(c.spend30, settings)
                return {
                    id: c.id,
                    name: c.name,
                    status: c.status,
                    objective: c.objective,
                    spend: ct.spend,
                    results: ct.results,
                    impressions: ct.impressions,
                    linkClicks: ct.linkClicks,
                }
            }),
        backfill: { done: progress >= 1, coveredUntil: iso(covered) },
    }
}
