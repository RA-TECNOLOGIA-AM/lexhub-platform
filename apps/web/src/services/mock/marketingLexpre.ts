import { PREFIXO, type MarketingLexpreResponse } from '../../pages/dashboards/marketing-lexpre/marketingLexpre.ts'
import type { DashboardQuery, Point } from '../../types/index.ts'
import { metaFor, unitScale } from './helpers.ts'

// Marketing (LexPre) fictício, no formato da rota /marketing_lexpre_NG da v1 (chaves com o prefixo
// marketing_lexpre_ng_ nas duas unidades). Números e nomes inventados e determinísticos (sem Math.random).
// NG e LA_AM, como a v1; na LA os anúncios ficam zerados (a conta de anúncios dela não é ingerida).

const UNIDADES = new Set(['NG', 'LA_AM'])

const pts = (k: number, pares: [string, number][]): Point[] =>
    pares.map(([name, value]) => ({ name, value: Math.round(value * k) })).filter((p) => p.value > 0)

function filtrado(query: DashboardQuery | undefined): number {
    // Com filtro clicado, uma fração dos números (o mock não recalcula nada de verdade).
    const f = query?.filters ?? {}
    const n = Object.entries(f).filter(([k, v]) => k.endsWith('_marketing') && v?.length).length
    return n === 0 ? 1 : 0.5 ** n
}

export function marketingLexpreFor(unit: string, query?: DashboardQuery): MarketingLexpreResponse {
    const meta = metaFor(unit)
    if (!UNIDADES.has(unit)) return { meta }
    const k = unitScale(unit).money(1) * filtrado(query) // o tamanho da unidade (NG = 1)
    const anuncios = unit === 'NG' ? 1 : 0
    const r = (v: number) => Math.round(v * k)

    const clientes = r(412)
    const triados = r(268)
    const gasto = Math.round(18_450 * k * anuncios * 100) / 100
    const campanha = r(96)
    const leadsCampanha = r(610)
    const protocolados = r(71)
    const valorCausa = Math.round(1_284_000 * k)
    const acoes = r(138)

    const stats: Record<string, number> = {
        total_clientes: clientes,
        media_idade: 41.3,
        triados_total_clientes: triados,
        triados_media_idade: 43.8,
        facebook_cliques: r(9_840) * anuncios,
        facebook_pageview: r(6_120) * anuncios,
        facebook_leads: r(1_030) * anuncios,
        facebook_valor_gasto: gasto,
        facebook_cac_campanha: campanha && anuncios ? gasto / campanha : 0,
        facebook_cac_geral: clientes && anuncios ? gasto / clientes : 0,
        facebook_roas_campanha: gasto ? valorCausa / gasto : 0,
        facebook_roas_geral: gasto ? (valorCausa * 2.4) / gasto : 0,
        clientes_campanha: campanha,
        leads: r(1_480),
        indicacao_ativa: r(84),
        indicacao_passiva: r(132),
        retorno_ativa: r(41),
        retorno_passiva: r(57),
        campanha,
        conversao_campanha: leadsCampanha ? (campanha / leadsCampanha) * 100 : 0,
        protocolados_campanha: protocolados,
        valor_causa_campanha: valorCausa,
        ticket_medio_campanha: protocolados ? valorCausa / protocolados : 0,
        total_trackeamento: r(702),
        processos_assinados: r(118),
        leads_campanha: leadsCampanha,
        acoes_campanha: acoes,
        aproveitamento_campanha: campanha ? acoes / campanha : 0,
        cpl_campanha: leadsCampanha ? gasto / leadsCampanha : 0,
        org_leads_facebook: r(212),
        org_leads_instagram: r(305),
        org_leads_site: r(98),
        org_leads_google: r(77),
        org_total_leads: r(731),
        org_contratos: r(88),
        org_acoes: r(121),
        org_aproveitamento: 1.38,
        org_taxa_fechamento: 12.0,
        org_valor_causa: Math.round(842_000 * k),
        org_ticket_medio: 13_150,
    }

    const faixa: [string, number][] = [
        ['18-24', 38],
        ['25-34', 96],
        ['35-44', 121],
        ['45+', 157],
    ]
    const canais: [string, number][] = [
        ['CAMPANHA', 96],
        ['INDICACAO', 132],
        ['RETORNO', 58],
        ['REDES_SOCIAIS', 71],
        ['SITE', 33],
        ['RESGATE', 22],
    ]
    const rubricas: [string, number][] = [
        ['CESTA DE SERVIÇOS', 44],
        ['MORA', 31],
        ['SEGURO PRESTAMISTA', 26],
        ['TARIFA DE CADASTRO', 19],
        ['CAPITALIZAÇÃO', 11],
    ]
    const campanhas: [string, number][] = [
        ['[NG] Revisional — Lookalike', 182],
        ['[NG] Cesta — Interesses', 141],
        ['[NG] Remarketing 30d', 96],
        ['[NG] Seguro — Aberto', 64],
    ]
    const posicionamentos: [string, number][] = [
        ['Feed Instagram', 211],
        ['Stories Instagram', 164],
        ['Feed Facebook', 118],
        ['Reels', 87],
        ['(Em branco)', 140],
    ]
    const categorias: [string, number][] = [
        ['Vídeo', 248],
        ['Imagem', 191],
        ['Carrossel', 76],
        ['(Em branco)', 112],
    ]
    const conjuntos: [string, number][] = [
        ['Mulheres 35+ AM', 133],
        ['Aposentados AM', 104],
        ['Servidores públicos', 71],
    ]
    const criativos: [string, number][] = [
        ['Depoimento cliente 02', 121],
        ['Cálculo na tela', 97],
        ['Carrossel tarifas', 64],
    ]

    const charts: Record<string, unknown> = {
        faixa_etaria: pts(k, faixa),
        genero: pts(k, [
            ['FEMININO', 238],
            ['MASCULINO', 174],
        ]),
        origem: pts(k, canais),
        ocupacao: pts(k, [
            ['APOSENTADO', 131],
            ['ASSALARIADO', 118],
            ['AUTÔNOMO', 77],
            ['SERVIDOR PÚBLICO', 52],
            ['DESEMPREGADO', 34],
        ]),
        tipo_trafego: pts(k, [
            ['PAGO', 228],
            ['ORGÂNICO', 184],
        ]),
        prospeccao: pts(k, [
            ['PASSIVA', 301],
            ['ATIVA', 111],
        ]),
        faixa_salarial: pts(k, [
            ['Não informado', 144],
            ['Até 2500', 67],
            ['De 2.500 a 5.000', 34],
            ['De 5.000 a 10.000', 10],
            ['Acima de 10.000', 4],
        ]),
        triados_faixa_etaria: pts(k * 0.65, faixa),
        triados_genero: pts(k, [
            ['FEMININO', 161],
            ['MASCULINO', 107],
        ]),
        triados_origem: pts(k * 0.65, canais),
        triados_ocupacao: pts(k, [
            ['APOSENTADO', 98],
            ['ASSALARIADO', 81],
            ['AUTÔNOMO', 52],
            ['DESEMPREGADO', 37],
        ]),
        triados_tipo_trafego: pts(k, [
            ['PAGO', 151],
            ['ORGÂNICO', 117],
        ]),
        triados_prospeccao: pts(k, [
            ['PASSIVA', 203],
            ['ATIVA', 65],
        ]),
        triados_faixa_salarial: pts(k, [
            ['Até 2500', 67],
            ['De 2.500 a 5.000', 34],
            ['De 5.000 a 10.000', 10],
            ['Acima de 10.000', 4],
        ]),
        triados_tipo_residencia: pts(k, [
            ['Própria', 139],
            ['Alugada', 88],
            ['Cedida', 41],
        ]),
        triados_pessoas_dependentes: pts(k, [
            ['5 pessoas', 24],
            ['3 pessoas', 23],
            ['2 pessoas', 22],
            ['4 pessoas', 22],
            ['Acima de 6 pessoas', 13],
            ['1 pessoa', 11],
        ]),
        investimento_cliques_leads: anuncios
            ? Array.from({ length: 20 }, (_, i) => ({
                  name: `${String(i + 1).padStart(2, '0')}/10`,
                  investimento: Math.round((820 + 260 * Math.sin(i * 0.7)) * k * 100) / 100,
                  cliques: Math.round((470 + 140 * Math.sin(i * 0.6 + 1)) * k),
                  leads: Math.round((48 + 17 * Math.sin(i * 0.5 + 2)) * k),
              }))
            : [],
        total_clientes_campanha: pts(k, [
            ['Campanha', 96],
            ['Demais canais', 316],
        ]),
        protocolo_resolvido_total: pts(k, [
            ['Campanha', 71],
            ['Demais canais', 204],
        ]),
        valor_causa_total: pts(k, [
            ['Campanha', 1_284_000],
            ['Demais canais', 3_910_000],
        ]),
        rubrica_campanha: pts(k, rubricas),
        rubrica_protocolado: pts(k * 0.7, rubricas),
        trackeamento_categoria: pts(k, categorias),
        trackeamento_posicionamento: pts(k, posicionamentos),
        trackeamento_canal_aquisicao: pts(k, canais),
        trackeamento_campanha: pts(k, campanhas),
        fechamento_categoria: pts(k * 0.2, categorias),
        fechamento_posicionamento: pts(k * 0.2, posicionamentos),
        fechamento_canal_aquisicao: pts(k * 0.2, canais),
        fechamento_campanha: pts(k * 0.2, campanhas),
        ind_campanha: pts(k * 0.4, campanhas),
        ind_posicionamento: pts(k * 0.4, posicionamentos),
        ind_conjunto: pts(k * 0.4, conjuntos),
        ind_criativo: pts(k * 0.4, criativos),
        ind_categoria: pts(k * 0.4, categorias),
        org_campanha: pts(k * 0.3, campanhas),
        org_posicionamento: pts(k * 0.3, posicionamentos),
        org_conjunto: pts(k * 0.3, conjuntos),
        org_criativo: pts(k * 0.3, criativos),
        org_categoria: pts(k * 0.3, categorias),
        org_rubricas_total: pts(k, rubricas),
        org_rubricas_facebook: pts(k * 0.3, rubricas),
        org_rubricas_instagram: pts(k * 0.4, rubricas),
        org_rubricas_site: pts(k * 0.15, rubricas),
        org_rubricas_google: pts(k * 0.1, rubricas),
    }

    return {
        meta,
        dashboard: unit === 'NG' ? 'marketing_lexpre_NG' : 'marketing_lexpre_LA',
        stats: Object.fromEntries(Object.entries(stats).map(([c, v]) => [PREFIXO + c, v])),
        charts: Object.fromEntries(Object.entries(charts).map(([c, v]) => [PREFIXO + c, v])),
    }
}
