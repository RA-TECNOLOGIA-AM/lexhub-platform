import type { MarketingNgResponse } from '../../pages/dashboards/marketing/marketingNg.ts'
import { PREFIXO_NG } from '../../pages/dashboards/marketing/marketingNg.ts'
import { PREFIXO } from '../../pages/dashboards/marketing-lexpre/marketingLexpre.ts'
import type { DashboardQuery } from '../../types/index.ts'
import { metaFor } from './helpers.ts'
import { marketingLexpreFor } from './marketingLexpre.ts'

// Marketing (banco NG) fictício, no formato da rota /marketing_NG da v1: números em `stats` e gráficos soltos na
// resposta, com o prefixo marketing_ng_. Parte do mock do LexPre (mesmas seções) + o que só o banco NG tem:
// dispositivo, funil de pipeline, as campanhas RA e NG e as rubricas RA x NG. Só a NG, como a v1.
export function marketingNgFor(unit: string, query?: DashboardQuery): MarketingNgResponse {
    const meta = metaFor(unit, 'NG')
    if (unit !== 'NG') return { meta }
    const base = marketingLexpreFor('NG', query)
    const trocar = (o: Record<string, unknown> = {}) =>
        Object.fromEntries(Object.entries(o).map(([c, v]) => [PREFIXO_NG + c.slice(PREFIXO.length), v]))
    const stats = trocar(base.stats) as Record<string, number>
    const g = (c: string) => stats[PREFIXO_NG + c] ?? 0
    const k = g('total_clientes') / 412

    const r = (v: number) => Math.round(v * k)
    const extra: Record<string, number> = {
        campanha_ra: r(38),
        campanha_ng: r(58),
        conversao_ra: 9.4,
        conversao_ng: 11.2,
        protocolados_ra: r(27),
        protocolados_ng: r(44),
        valor_causa_ra: Math.round(486_000 * k),
        valor_causa_ng: Math.round(798_000 * k),
        ticket_medio_ra: 12_400,
        ticket_medio_ng: 13_050,
        leads_ng: r(518),
        acoes_ng: r(82),
        aproveitamento_ng: 1.41,
        cpl_ng: 35.6,
    }
    const rubricas: [string, number, number][] = [
        ['CESTA DE SERVIÇOS', 17, 27],
        ['MORA', 12, 19],
        ['SEGURO PRESTAMISTA', 9, 17],
        ['TARIFA DE CADASTRO', 7, 12],
    ]
    const raNg = (f: number) => rubricas.map(([name, ra, ng]) => ({ name, ra: r(ra * f), ng: r(ng * f) }))

    return {
        meta,
        dashboard: 'marketing_NG',
        lexpre: { somado: true, motivo: null },
        stats: { ...stats, ...Object.fromEntries(Object.entries(extra).map(([c, v]) => [PREFIXO_NG + c, v])) },
        ...trocar(base.charts),
        [PREFIXO_NG + 'dispositivo']: [
            { name: 'Mobile', value: r(331) },
            { name: 'Desktop', value: r(81) },
        ],
        [PREFIXO_NG + 'triados_dispositivo']: [
            { name: 'Mobile', value: r(219) },
            { name: 'Desktop', value: r(49) },
        ],
        [PREFIXO_NG + 'funil_pipeline']: [
            { name: 'LEAD', value: r(1480) },
            { name: 'CONTATO', value: r(1012) },
            { name: 'TRIAGEM', value: r(604) },
            { name: 'PROPOSTA', value: r(388) },
            { name: 'ASSINADO', value: r(412) },
        ],
        [PREFIXO_NG + 'rubrica_campanha']: raNg(1),
        [PREFIXO_NG + 'rubrica_protocolado']: raNg(0.7),
        [PREFIXO_NG + 'ind_rubricas']: rubricas.map(([name, , ng]) => ({ name, value: r(ng) })),
    }
}
