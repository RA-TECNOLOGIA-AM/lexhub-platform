import type { EstrategicoResponse, Juridico, Subfase } from '../../pages/dashboards/estrategico/estrategico.ts'
import type { Point } from '../../types/index.ts'
import { metaFor } from './helpers.ts'

// Estratégico fictício (formato de app/dashboards/estrategico.py): séries de jan/2025 a out/2026 geradas por uma
// sequência pseudoaleatória fixa (o mesmo resultado sempre), escaladas pelo tamanho da unidade.

const TAMANHO: Record<string, number> = { NG: 1, LA_AM: 0.62, LA_RJ: 0.38 }

function gerador(semente: number) {
    let s = semente
    return () => {
        s = (s * 1103515245 + 12345) % 2147483648
        return s / 2147483648
    }
}

// Uma série diária (dias úteis) de jan/2025 a out/2026 e a mensal somada dela.
function series(base: number, k: number, semente: number): { mes: Point[]; dia: Point[] } {
    const r = gerador(semente)
    const dia: Point[] = []
    const mes = new Map<string, number>()
    for (let d = new Date(2025, 0, 1); d <= new Date(2026, 9, 31); d.setDate(d.getDate() + 1)) {
        if (d.getDay() === 0 || d.getDay() === 6) continue
        const iso = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
        const v = Math.round(base * k * (0.6 + r() * 0.8))
        dia.push({ name: iso, value: v })
        mes.set(iso.slice(0, 7), (mes.get(iso.slice(0, 7)) ?? 0) + v)
    }
    return { mes: [...mes].map(([name, value]) => ({ name, value })), dia }
}

const SUB_INICIAL = ['AG. DESPACHO INICIAL', 'AG. CITAÇÃO DO RÉU', 'AG. AUDIÊNCIA', 'AG. SENTENÇA', 'SEM SUBFASE']
const SUB_RECURSAL = ['AG. CONTRARRAZÕES', 'AG. CONFECÇÃO RECURSO', 'AG. JULGAMENTO', 'AG. TRÂNSITO EM JULGADO']
const SUB_EXECUCAO = ['AG. DECISÃO CS', 'AG. PAGAMENTO VOLUNTÁRIO', 'AG. AUTORIZAÇÃO DE ALVARÁ', 'AG. CÁLCULO']
const AM = ['MANAUS', 'TABATINGA', 'PARINTINS', 'ITACOATIARA', 'MANACAPURU', 'TEFÉ', 'COARI', 'HUMAITÁ']
// As comarcas de cada unidade, com a UF (a NG atende AM, PA e PB).
const COMARCAS: Record<string, [string, string][]> = {
    NG: [
        ...AM.map((c) => [c, 'AM'] as [string, string]),
        ['BELÉM', 'PA'],
        ['SANTARÉM', 'PA'],
        ['JOÃO PESSOA', 'PB'],
        ['CAMPINA GRANDE', 'PB'],
    ],
    LA_AM: AM.map((c) => [c, 'AM']),
    LA_RJ: [
        ['RIO DE JANEIRO', 'RJ'],
        ['NITERÓI', 'RJ'],
        ['DUQUE DE CAXIAS', 'RJ'],
        ['NOVA IGUAÇU', 'RJ'],
        ['SÃO GONÇALO', 'RJ'],
    ],
}

function subfasesDe(nomes: string[], total: number, campo: keyof Subfase, r: () => number): Subfase[] {
    let resto = total
    return nomes.map((name, i) => {
        const value = i === nomes.length - 1 ? resto : Math.round(resto * (0.35 + r() * 0.3))
        resto -= value
        return { name, value, [campo]: Math.round(value * 28_000 * (0.6 + r())), tempo_medio_dias: 30 + r() * 90 }
    })
}

function juridico(unit: string, k: number, escala: number, semente: number): Juridico {
    const r = gerador(semente)
    const inicial = Math.round(350 * k * escala)
    const recursal = Math.round(530 * k * escala)
    const execucao = Math.round(130 * k * escala)
    return {
        fase_inicial_total_processos: inicial,
        fase_inicial_valor_causa_total: inicial * 31_000,
        fase_recursal_total_processos: recursal,
        fase_recursal_valor_causa_total: recursal * 41_000,
        fase_recursal_valor_sentenca_total: recursal * 700,
        fase_execucao_total_processos: execucao,
        fase_execucao_valor_causa_total: execucao * 13_000,
        fase_execucao_valor_execucao_total: execucao * 12_800,
        fase_inicial_por_subfase: subfasesDe(SUB_INICIAL, inicial, 'valor_causa', r),
        fase_recursal_por_subfase: subfasesDe(SUB_RECURSAL, recursal, 'valor_sentenca', r),
        fase_execucao_por_subfase: subfasesDe(SUB_EXECUCAO, execucao, 'valor_execucao', r).map(
            ({ tempo_medio_dias: _t, ...s }) => s,
        ),
        juridico_por_comarca: [
            ...COMARCAS[unit].map(([name, uf], i) => {
                const value = Math.max(1, Math.round(((inicial + recursal + execucao) * 0.5) / (i + 1) ** 1.3))
                return { name, value, uf, valor_causa: value * 27_500 }
            }),
            { name: 'Sem comarca', value: Math.round(4 * escala), valor_causa: Math.round(4 * escala) * 20_000 },
        ],
    }
}

export function estrategicoFor(unit: string): EstrategicoResponse {
    const meta = metaFor(unit, 'LexFlow, legado e LexPre')
    const k = TAMANHO[unit]
    if (k === undefined) return { meta }
    const contratos = series(9, k, 11)
    const acoes = series(36, k, 12)
    const protocolados = series(16, k, 13)
    const valorDia = protocolados.dia.map((p, i) => ({ name: p.name, value: p.value * (26_000 + (i % 7) * 1_500) }))
    const valorMes = new Map<string, number>()
    for (const p of valorDia) valorMes.set(p.name.slice(0, 7), (valorMes.get(p.name.slice(0, 7)) ?? 0) + p.value)
    const prot = Math.round(359 * k)
    const valor = prot * 30_400
    return {
        meta,
        unidade: unit,
        tem_uf: unit === 'NG',
        fontes: { legado: true, lexpre: true },
        comercial: {
            contratos: Math.round(200 * k),
            contratos_anterior: Math.round(186 * k),
            acoes: Math.round(794 * k),
            acoes_anterior: Math.round(714 * k),
            contratos_por_mes: contratos.mes,
            acoes_por_mes: acoes.mes,
            contratos_por_dia: contratos.dia,
            acoes_por_dia: acoes.dia,
        },
        protocolo: {
            represados: Math.round(139 * k),
            protocolados: prot,
            protocolados_anterior: Math.round(356 * k),
            valor_causa: valor,
            valor_causa_anterior: Math.round(356 * k) * 22_400,
            ticket_medio: valor / prot,
            ticket_medio_anterior: 22_400,
            protocolados_por_mes: protocolados.mes,
            valor_causa_por_mes: [...valorMes].map(([name, value]) => ({ name, value })),
            protocolados_por_dia: protocolados.dia,
            valor_causa_por_dia: valorDia,
        },
        juridico_periodo: juridico(unit, k, 1, 21),
        juridico_fixo: juridico(unit, k, 18, 22),
    }
}
