import type { V1GenericoResponse } from '../../pages/dashboards/v1Stats.ts'
import type { Point } from '../../types/index.ts'
import { nomeNaUnidade, type Unidade } from '../../pages/dashboards/execucao/unidade.ts'
import { funcionarios, metaFor } from './helpers.ts'

// Execução Condenação e Execução Acordos (LexFlow) fictícias, no formato das rotas da v1 da NG (/execucao e
// /execucao_acordos_NG) e na ordem de grandeza das telas da v1. LA e RJ: os mesmos números com os nomes das
// rotas deles (naUnidade).
// Números de processo inventados (20 dígitos, como o LexFlow) e determinísticos, sem Math.random.

const MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']

// Série "mês a mês" de 2024 até novembro/2026 ('nov 2026'), com uma onda para não ficar reta.
function porMes(base: number, amp: number, inicio = 2024): Point[] {
    const out: Point[] = []
    for (let ano = inicio; ano <= 2026; ano++) {
        for (let m = 0; m < 12; m++) {
            if (ano === 2026 && m > 10) break
            const v = base * (1 + (ano - inicio) * 0.18) + amp * Math.sin((ano * 12 + m) * 0.9)
            out.push({ name: `${MESES[m]} ${ano}`, value: Math.max(0, Math.round(v * 100) / 100) })
        }
    }
    return out
}

// Atividades cumpridas por dia (dias úteis de setembro a novembro/2026): '2026-11-03'.
function porDia(base: number): Point[] {
    const out: Point[] = []
    for (const [mes, dias] of [
        [9, 30],
        [10, 31],
        [11, 17],
    ]) {
        for (let d = 1; d <= dias; d++) {
            const wd = new Date(2026, mes - 1, d).getDay()
            if (wd === 0 || wd === 6) continue
            out.push({
                name: `2026-${String(mes).padStart(2, '0')}-${String(d).padStart(2, '0')}`,
                value: Math.max(0, Math.round(base + 6 * Math.sin(d * 1.3) + (d % 4))),
            })
        }
    }
    return out
}

const processo = (i: number) =>
    `0${String(600000 + ((i * 7919) % 399999)).padStart(6, '0')}${String(10 + (i % 89)).padStart(2, '0')}2024804${String(1 + (i % 9)).padStart(4, '0')}`

const SUBFASES = [
    ['AGUARDANDO ALVARÁ', 412, 9_800_000],
    ['CUMPRIMENTO DE SENTENÇA', 365, 8_100_000],
    ['CÁLCULO', 240, 5_200_000],
    ['IMPUGNAÇÃO', 151, 3_900_000],
    ['PENHORA', 98, 2_300_000],
    ['ALVARÁ EXPEDIDO', 64, 1_450_000],
    ['AGUARDANDO TRÂNSITO EM JULGADO', 52, 1_120_000],
    ['EMBARGOS À EXECUÇÃO', 41, 980_000],
    ['AGUARDANDO DEPÓSITO JUDICIAL', 33, 760_000],
    ['BLOQUEIO SISBAJUD', 27, 610_000],
    ['RECURSO DO RÉU', 19, 420_000],
    ['AGUARDANDO HOMOLOGAÇÃO DO CÁLCULO', 12, 260_000],
] as const

const MATERIAS: [string, number][] = [
    ['CESTA', 402],
    ['RMC', 288],
    ['MORA', 251],
    ['ANP', 160],
    ['PARC_CRED_PESS', 114],
    ['GASTO_C_CRED', 61],
    ['ESPECIFICA', 54],
]

const COMARCAS: [string, number, string, number][] = [
    // nome (igual ao município do IBGE), processos, UF, tempo médio na comarca (dias)
    ['MANAUS', 690, 'AM', 182.4],
    ['ITACOATIARA', 112, 'AM', 240.1],
    ['PARINTINS', 96, 'AM', 265.7],
    ['MANACAPURU', 81, 'AM', 198.3],
    ['TEFÉ', 64, 'AM', 301.2],
    ['COARI', 51, 'AM', 287.9],
    ['BELÉM', 40, 'PA', 150.6],
    ['RIO BRANCO', 22, 'AC', 133.2],
]

const ATIVIDADES: [string, number][] = [
    ['CÁLCULO DE EXECUÇÃO', 61],
    ['DILIGÊNCIA PARA EXPEDIÇÃO DE ALVARÁ', 44],
    ['PETIÇÃO DE CUMPRIMENTO DE SENTENÇA', 38],
    ['IMPUGNAÇÃO AO CÁLCULO', 21],
    ['CONFERÊNCIA DE ALVARÁ', 12],
]

const comarcas = (k = 1) =>
    COMARCAS.map(([name, v, uf, tempo]) => ({ name, value: Math.round(v * k), uf, tempo_medio_dias: tempo }))

const pts = (xs: readonly (readonly [string, number])[], k = 1): Point[] =>
    xs.map(([name, v]) => ({ name, value: Math.round(v * k) }))

// As partes comuns das duas rotas (Atividades e Diligências), com o prefixo da rota.
function setor(prefixo: 'execucao' | 'execucao_acordos', k: number) {
    const sufixo = (nome: string) => `${prefixo}_${nome}_NG`
    const equipe = funcionarios.slice(0, 5)
    const demandas = equipe.map((name, i) => {
        const cumpridas = Math.round((48 - i * 8) * k)
        const nao = Math.round((6 - i) * k)
        return { name, total: cumpridas + nao, encerrado_cumprido: cumpridas, encerrado_nao_cumprido: nao }
    })
    const lista = Array.from({ length: 23 }, (_, i) => {
        const [atividade] = ATIVIDADES[i % ATIVIDADES.length]
        const vencida = i % 6 === 2
        const concluida = i % 3 === 0
        return {
            id: 90_000 + i * 13,
            status: concluida ? 'Encerrado Cumprido' : vencida ? 'Recebido' : 'Visualizado',
            descricao: `${atividade.toLowerCase()} do processo`,
            pessoa_setor: prefixo === 'execucao' ? 'EXECUÇÃO' : 'ACORDOS',
            funcionario: equipe[i % equipe.length],
            funcionario_atribuido: equipe[i % equipe.length],
            funcionario_encerramento: i % 7 === 0 ? equipe[(i + 1) % equipe.length] : equipe[i % equipe.length],
            encerrado_pelo_responsavel: concluida ? i % 7 !== 0 : null,
            atividade,
            numero_processo: processo(i),
            criado_em: `2026-11-${String(1 + (i % 16)).padStart(2, '0')}`,
            prazo: `2026-11-${String(3 + (i % 20)).padStart(2, '0')}`,
            vencida,
            vence_hoje: i % 11 === 5,
            concluida,
            em_andamento: !concluida,
            valor_execucao: 8_000 + i * 1_337.5,
        }
    })
    const opcoes = {
        funcionarios: equipe,
        atividades: ATIVIDADES.map(([a]) => a),
        status: ['Encerrado Cumprido', 'Recebido', 'Visualizado'],
        situacoes: [
            { id: 'em_andamento', label: 'Em andamento' },
            { id: 'vencidas', label: 'Vencidas' },
            { id: 'vencem_hoje', label: 'Vencem hoje' },
            { id: 'concluidas', label: 'Concluídas' },
        ],
    }
    const media = equipe.map((name, i) => ({ name, value: Math.round((18.5 - i * 3.4) * k * 10) / 10 }))
    const processosAlvara = Array.from({ length: 9 }, (_, i) => ({
        id: i,
        numero_processo: processo(i + 40),
        uf: i % 4 === 3 ? 'PA' : 'AM',
        data_execucao: `2025-${String(1 + (i % 12)).padStart(2, '0')}-1${i % 9}`,
        valor_execucao: 12_500 + i * 4_250.75,
        subfase: 'ALVARÁ EXPEDIDO',
    }))
    return {
        [sufixo('processos_por_atividade')]: pts(ATIVIDADES, k),
        [sufixo('processos_por_atividade_por_prazo')]: pts(ATIVIDADES, k * 0.7),
        [sufixo('demandas_por_funcionario')]: demandas,
        [sufixo('demandas_por_funcionario_por_prazo')]: demandas.map((d) => ({
            ...d,
            total: Math.round(d.total * 0.7),
        })),
        [sufixo('media_resolvidos_por_funcionario')]: media,
        [sufixo('media_resolvidos_por_funcionario_por_prazo')]: media,
        [sufixo('resolvidos_por_dia')]: porDia(14 * k),
        [sufixo('resolvidos_por_dia_por_prazo')]: porDia(11 * k),
        [sufixo('atividades_lista')]: lista,
        [sufixo('atividades_lista_por_prazo')]: lista.slice(0, 15),
        [sufixo('atividades_lista_filtros_opcoes')]: opcoes,
        [sufixo('atividades_lista_filtros_opcoes_por_prazo')]: opcoes,
        [sufixo('atrasos_detalhamento')]: {
            total: 17,
            buckets: [
                { dias: 1, label: '1 dia', descricao: 'Venceu ontem', count: 6, pct: 35.3 },
                { dias: 2, label: '2 dias', descricao: '', count: 4, pct: 23.5 },
                { dias: 3, label: '3 dias', descricao: '', count: 3, pct: 17.6 },
                { dias: 4, label: '4 dias', descricao: '', count: 2, pct: 11.8 },
                { dias: 5, label: '5 dias', descricao: '', count: 1, pct: 5.9 },
                { dias: 6, label: '6 dias ou mais', descricao: 'Atraso crítico', count: 1, pct: 5.9 },
            ],
        },
        [sufixo('diligencias_por_processo')]: Array.from({ length: 8 }, (_, i) => ({
            name: processo(i + 70),
            value: 5 - Math.floor(i / 2),
            valor_execucao: 20_000 + i * 3_100,
        })),
        [sufixo('diligencias_por_funcionario')]: equipe.map((name, i) => ({ name, total: 31 - i * 5 })),
        [sufixo('diligencias_expedicao_alvara_processos')]: processosAlvara,
        _valorAlvaras: processosAlvara.reduce((s, p) => s + p.valor_execucao, 0),
        _qtdAlvaras: processosAlvara.length,
    }
}

const statsAtividades = (alvo: 'execucao_NG' | 'execucao_acordos_NG', k: number) => {
    const acordos = alvo === 'execucao_acordos_NG'
    const nome = (base: string) => (acordos ? `${base}_acordos_NG` : `${base}_NG`)
    return {
        [acordos ? 'total_atividades_execucao_acordos_NG' : 'total_atividades_execucao_NG']: Math.round(176 * k),
        [nome('atividades_execucao_em_andamento')]: Math.round(58 * k),
        [nome('atividades_execucao_vencidas')]: 17,
        [nome('atividades_execucao_vencem_hoje')]: 4,
        [nome('atividades_execucao_concluidas')]: Math.round(97 * k),
        [`total_por_prazo_${alvo}`]: Math.round(132 * k),
        [`por_prazo_em_andamento_${alvo}`]: Math.round(40 * k),
        [`por_prazo_vencidas_${alvo}`]: 17,
        [`por_prazo_vencem_hoje_${alvo}`]: 4,
        [`por_prazo_concluidas_${alvo}`]: Math.round(71 * k),
        [`total_diligencias_${alvo}`]: Math.round(124 * k),
        [`total_diligencias_expedicao_alvara_${alvo}`]: Math.round(38 * k),
        [`cumpridas_diligencias_expedicao_alvara_${alvo}`]: Math.round(21 * k),
    }
}

function execucaoNG(): V1GenericoResponse {
    const { _valorAlvaras, _qtdAlvaras, ...partes } = setor('execucao', 1)
    void _qtdAlvaras
    const total = SUBFASES.reduce((s, [, q]) => s + q, 0)
    const valorTotal = SUBFASES.reduce((s, [, , v]) => s + v, 0)
    return {
        meta: metaFor('NG', 'LexFlow'),
        dashboard: 'execucao',
        stats: {
            total_em_execucao_historico: total,
            valor_total_em_execucao: valorTotal,
            valor_remanescente_em_execucao: 2_874_310.4,
            total_em_execucao: 46,
            valor_em_execucao: 1_312_904.77,
            total_saida_execucao_periodo: 39,
            total_incontroverso_saida_execucao_periodo: 6,
            valor_execucao_saida_periodo: 1_046_220.18,
            valor_ted_saida_execucao_periodo: 972_014.6,
            valor_incontroverso_saida_execucao_periodo: 188_450.0,
            media_tempo_execucao: 214.6,
            mediana_tempo_execucao: 187,
            estoque_inicial: 1_323,
            tre: 2.23,
            total_valor_execucao_vazio: 3,
            total_valor_execucao_vazio_detalhe: [0, 1, 2].map((i) => ({
                numero_processo: processo(i + 90),
                campo: 'Valor da Execução',
            })),
            execucao_uf_opcoes_NG: ['AC', 'AM', 'PA'],
            execucao_comarca_opcoes_NG: COMARCAS.map(([c]) => c),
            execucao_materia_opcoes_NG: MATERIAS.map(([m]) => m),
            execucao_subfase_opcoes_NG: SUBFASES.map(([s]) => s),
            valor_diligencias_expedicao_alvara_execucao_NG: _valorAlvaras,
            ...statsAtividades('execucao_NG', 1),
        },
        execucao_por_subfase: SUBFASES.map(([name, value]) => ({ name, value })),
        valor_execucao_por_subfase: SUBFASES.map(([name, , value]) => ({ name, value })),
        execucao_por_materia: pts(MATERIAS),
        execucao_por_comarca_total: comarcas(),
        execucao_valor_por_comarca_total: comarcas(23_500),
        execucao_por_comarca_entrada: comarcas(0.04),
        execucao_valor_por_comarca_entrada: comarcas(1_100),
        execucao_por_comarca_saida: comarcas(0.03),
        execucao_valor_por_comarca_saida: comarcas(900),
        valor_remanescente_por_mes: porMes(52_000, 21_000),
        valor_execucao_saida_periodo_por_mes: porMes(690_000, 240_000),
        quantidade_entrada_execucao_por_mes: porMes(41, 12),
        valor_entrada_execucao_por_mes: porMes(1_050_000, 310_000),
        ...partes,
    } as V1GenericoResponse
}

function acordosNG(): V1GenericoResponse {
    const { _valorAlvaras, _qtdAlvaras, ...partes } = setor('execucao_acordos', 0.6)
    void _qtdAlvaras
    const listaDe = (n: number, desloc: number, subfase: string) =>
        Array.from({ length: n }, (_, i) => ({
            id: desloc + i,
            numero_processo: processo(desloc + i),
            uf: i % 5 === 4 ? 'PA' : 'AM',
            data_execucao: `2026-${String(1 + (i % 10)).padStart(2, '0')}-${String(3 + (i % 25)).padStart(2, '0')}`,
            valor_execucao: 3_500 + i * 812.4,
            subfase,
        }))
    const entrada = listaDe(14, 200, 'AGUARDANDO PAGAMENTO')
    const saida = listaDe(9, 300, 'ACORDO PAGO')
    return {
        meta: metaFor('NG', 'LexFlow'),
        dashboard: 'execucao_acordos_NG',
        stats: {
            total_em_execucao_acordos_NG: 518,
            valor_total_em_execucao_acordos_NG: 3_904_772.1,
            total_entrada_execucao_acordos_periodo_NG: entrada.length,
            valor_entrada_execucao_acordos_periodo_NG: entrada.reduce((s, p) => s + p.valor_execucao, 0),
            total_saida_execucao_acordos_periodo_NG: saida.length,
            valor_saida_execucao_acordos_periodo_NG: saida.reduce((s, p) => s + p.valor_execucao, 0),
            media_tempo_execucao_acordos_NG: 64.2,
            mediana_tempo_execucao_acordos_NG: 51,
            estoque_inicial_execucao_acordos_NG: 513,
            tre_execucao_acordos_NG: 0.97,
            total_valor_alcada_final_vazio_acordos_NG: 2,
            total_valor_alcada_final_vazio_acordos_NG_detalhe: [0, 1].map((i) => ({
                numero_processo: processo(i + 95),
            })),
            execucao_acordos_uf_opcoes_NG: ['AM', 'PA'],
            execucao_acordos_comarca_opcoes_NG: COMARCAS.map(([c]) => c),
            execucao_acordos_materia_opcoes_NG: MATERIAS.map(([m]) => m),
            execucao_acordos_subfase_opcoes_NG: ['AGUARDANDO PAGAMENTO', 'ACORDO HOMOLOGADO', 'PAGAMENTO PARCIAL'],
            valor_diligencias_expedicao_alvara_execucao_acordos_NG: _valorAlvaras,
            ...statsAtividades('execucao_acordos_NG', 0.6),
        },
        fechamento_acordo_por_subfase_NG: [
            { name: 'ACORDO EM NEGOCIAÇÃO', value: 61 },
            { name: 'AG. PROTOCOLO DA MINUTA DE ACORDO', value: 23 },
            { name: 'MINUTA DE ACORDO PROTOCOLADA', value: 17 },
            { name: 'ACORDO FECHADO', value: 9 },
            { name: 'ACORDO CANCELADO', value: 4 },
        ],
        valor_fechamento_acordo_por_subfase_NG: [
            { name: 'ACORDO EM NEGOCIAÇÃO', value: 412_300 },
            { name: 'AG. PROTOCOLO DA MINUTA DE ACORDO', value: 158_900 },
            { name: 'MINUTA DE ACORDO PROTOCOLADA', value: 121_450 },
            { name: 'ACORDO FECHADO', value: 70_200 },
            { name: 'ACORDO CANCELADO', value: 18_000 },
        ],
        execucao_acordos_por_subfase_NG: [
            { name: 'AGUARDANDO PAGAMENTO', value: 302 },
            { name: 'ACORDO HOMOLOGADO', value: 141 },
            { name: 'PAGAMENTO PARCIAL', value: 75 },
        ],
        valor_execucao_acordos_por_subfase_NG: [
            { name: 'AGUARDANDO PAGAMENTO', value: 2_301_900 },
            { name: 'ACORDO HOMOLOGADO', value: 1_098_500 },
            { name: 'PAGAMENTO PARCIAL', value: 504_372.1 },
        ],
        execucao_acordos_por_sentenca_NG: [
            { name: 'Pré-Sentença', value: 288 },
            { name: 'Pós-Sentença', value: 197 },
            { name: 'Sem classificação', value: 33 },
        ],
        execucao_acordos_por_tipo_acao_NG: [
            { name: 'Judicial', value: 431 },
            { name: 'Extrajudicial', value: 70 },
            { name: 'Sem classificação', value: 17 },
        ],
        execucao_acordos_por_materia_NG: pts(MATERIAS, 0.4),
        execucao_acordos_por_comarca_total_NG: comarcas(0.4),
        execucao_acordos_valor_por_comarca_total_NG: comarcas(3_100),
        execucao_acordos_por_comarca_entrada_NG: comarcas(0.02),
        execucao_acordos_valor_por_comarca_entrada_NG: comarcas(160),
        execucao_acordos_por_comarca_saida_NG: comarcas(0.015),
        execucao_acordos_valor_por_comarca_saida_NG: comarcas(120),
        quantidade_entrada_execucao_acordos_por_mes_NG: porMes(16, 6),
        quantidade_saida_execucao_acordos_por_mes_NG: porMes(12, 5),
        valor_entrada_execucao_acordos_por_mes_NG: porMes(98_000, 30_000),
        valor_saida_execucao_acordos_por_mes_NG: porMes(71_000, 22_000),
        execucao_acordos_lista_entrada_NG: entrada,
        execucao_acordos_lista_saida_NG: saida,
        execucao_acordos_lista_total_NG: [...entrada, ...saida],
        ...partes,
    } as V1GenericoResponse
}

// A unidade do mock -> o escritório da rota da v1 (NG, LA_AM -> LA, LA_RJ -> RJ). Outra unidade: sem dados.
const ESCRITORIO: Record<string, Unidade> = { NG: 'NG', LA: 'LA', LA_AM: 'LA', RJ: 'RJ', LA_RJ: 'RJ' }

// LA e RJ com os números da NG (fictícios) e os nomes da rota de cada escritório, pela regra da v1 (nomeNaUnidade).
// A Execução da LA não tem Diligências, como a rota /execucao_LA.
function naUnidade(base: V1GenericoResponse, u: Unidade, dashboard: string, unit: string): V1GenericoResponse {
    const renomeia = (o: Record<string, unknown>) =>
        Object.fromEntries(
            Object.entries(o)
                .filter(([k]) => !(dashboard === 'execucao_LA' && k.includes('diligencias')))
                .map(([k, v]) => [nomeNaUnidade(k, u), v]),
        )
    const { meta, dashboard: _rota, stats, ...resto } = base as V1GenericoResponse & Record<string, unknown>
    void _rota
    void meta
    return {
        ...renomeia(resto),
        meta: metaFor(unit, 'LexFlow'),
        dashboard,
        stats: renomeia((stats ?? {}) as Record<string, unknown>),
    } as V1GenericoResponse
}

// Execução Condenação: NG, LA e RJ com a página toda; outra unidade, só o `meta` ('—').
export function execucaoFor(unit: string): V1GenericoResponse {
    const u = ESCRITORIO[unit]
    if (!u) return { meta: metaFor(unit, 'LexFlow'), stats: {} }
    const base = u === 'NG' ? execucaoNG() : naUnidade(execucaoNG(), u, `execucao_${u}`, unit)
    // V2 (dashboards/execucao_campos.py): o mesmo nome nas três unidades, fora da regra _NG -> _LA/_RJ.
    return { ...base, campos_faltando: camposFaltando() } as V1GenericoResponse
}

// Processos em execução com campo em branco (fictícios): um item por (processo, campo).
function camposFaltando() {
    const campos: [string, number][] = [
        ['Data do trânsito em julgado', 14],
        ['Data da execução', 9],
        ['Valor da execução', 3],
        ['Matéria', 2],
        ['Comarca', 1],
    ]
    return campos.flatMap(([campo, n], c) =>
        Array.from({ length: n }, (_, i) => ({ numero_processo: processo(200 + c * 20 + i), campo })),
    )
}

export function acordosFor(unit: string): V1GenericoResponse {
    const u = ESCRITORIO[unit]
    if (!u) return { meta: metaFor(unit, 'LexFlow'), stats: {} }
    return u === 'NG' ? acordosNG() : naUnidade(acordosNG(), u, `execucao_acordos_${u}`, unit)
}
