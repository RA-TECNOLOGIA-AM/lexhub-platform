import type { EstrategicoResponse } from '../../pages/dashboards/execucao-estrategico/estrategico.ts'
import type { Point } from '../../types/index.ts'
import { acordosFor, execucaoFor } from './execucao.ts'
import { funcionarios, metaFor } from './helpers.ts'

// Execução Estratégico Geral (NG) fictícia: as 8 chamadas da página da v1 montadas com os números do mock da
// Execução Condenação e da Execução Acordos, mais os campos que só esta página lê (durações, taxa de atualização,
// fluxo da Confecção CS, ano de ajuizamento, tempo médio por mês, alvarás e a Confecção CS). Determinístico.

type Obj = Record<string, unknown>
const MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
const processo = (i: number) =>
    `0${String(700000 + ((i * 6151) % 299999)).padStart(6, '0')}${String(10 + (i % 89)).padStart(2, '0')}2023804${String(1 + (i % 9)).padStart(4, '0')}`
const ATIVIDADES_CS = [
    'Elaborar Cumprimento de Sentença (1G)',
    'Elaborar Cumprimento de Sentença (2G)',
    'Manifestação Cálculo 1',
    'Manifestação Cálculo 2',
]

function meses(fn: (ano: number, m: number) => Obj): Obj[] {
    const out: Obj[] = []
    for (let ano = 2024; ano <= 2026; ano++)
        for (let m = 0; m < 12 && !(ano === 2026 && m > 10); m++)
            out.push({ name: `${MESES[m]} ${ano}`, ...fn(ano, m) })
    return out
}
const duracoes = (n: number, base: number) => Array.from({ length: n }, (_, i) => base + ((i * 37) % 160) - 40)
const anos = (k: number) =>
    [2019, 2020, 2021, 2022, 2023, 2024].map((a, i) => ({
        name: String(a),
        value: Math.round([40, 95, 180, 260, 210, 70][i] * k),
        valor_causa: Math.round([40, 95, 180, 260, 210, 70][i] * k * 18_500),
    }))
const comValor = (v: unknown, porProcesso: number) =>
    (v as Obj[]).map((c) => ({ ...c, valor_execucao: Number(c.value) * porProcesso }))
const materiaValor = (v: unknown, k: number) => (v as Point[]).map((p) => ({ name: p.name, value: p.value * k }))

function alvarasPorDia(k: number): Obj[] {
    const out: Obj[] = []
    for (let ano = 2025; ano <= 2026; ano++)
        for (let m = 0; m < 12 && !(ano === 2026 && m > 10); m++)
            for (let d = 2; d <= 27; d += 3 + ((m + d) % 3)) {
                const q = Math.max(1, Math.round((2 + Math.sin(d + m)) * k))
                out.push({
                    data: `${ano}-${String(m + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`,
                    quantidade: q,
                    valor: q * (14_000 + ((d * 977) % 9_000)),
                })
            }
    return out
}

function alvarasLista(n: number, desloc: number, acordo: boolean): Obj[] {
    return Array.from({ length: n }, (_, i) => {
        const remanescente = !acordo && i % 4 === 1
        const dia = 3 + ((i * 2) % 14)
        return {
            numero_processo: processo(desloc + i),
            subfase: acordo
                ? 'ALVARÁ EXPEDIDO ACORDO'
                : remanescente
                  ? 'ALVARÁ DO INCONTROVERSO EXPEDIDO'
                  : 'ALVARÁ EXPEDIDO',
            materia: ['CESTA', 'RMC', 'MORA', 'ANP'][i % 4],
            tipo_alvara: acordo ? 'Acordo' : remanescente ? 'Remanescente' : 'Integral',
            data_expedicao_alvara: `2026-11-${String(dia).padStart(2, '0')}`,
            data_expedicao_alvara_incontroverso: remanescente ? `2026-08-${String(dia).padStart(2, '0')}` : null,
            valor_alvara: 6_000 + i * 2_315.4,
            valor_alvara_incontroverso: remanescente ? 4_200 + i * 310 : null,
        }
    })
}

function taxa(k: number): Obj {
    const linha = (fluxo: string, q: number, dec: number, exe: number) => ({
        fluxo,
        quantidade: q,
        sem_valor: 1,
        valor_decisao: dec,
        valor_execucao: exe,
        aumento: exe - dec,
        taxa: Math.round(((exe - dec) / dec) * 10000) / 100,
    })
    const l1 = linha('1G', Math.round(21 * k), 310_000 * k, 402_500 * k)
    const l2 = linha('2G', Math.round(14 * k), 255_000 * k, 349_000 * k)
    return {
        linhas: [l1, l2],
        total: { taxa: Math.round(((l1.aumento + l2.aumento) / (l1.valor_decisao + l2.valor_decisao)) * 10000) / 100 },
        ano: 2026,
        por_mes: Array.from({ length: 11 }, (_, i) => ({
            mes: i + 1,
            valor_sentenca: 240_000 + 40_000 * Math.sin(i),
            valor_acordao: 190_000 + 35_000 * Math.cos(i),
            Total: Math.round((26 + 6 * Math.sin(i * 0.8)) * 100) / 100,
            quantidade: 20 + (i % 5),
        })),
        sem_valor_processos: [0, 1].map((i) => ({
            numero_processo: processo(500 + i),
            fluxo: i ? '2G' : '1G',
            data_entrada: `2026-11-0${3 + i}`,
            faltando: i ? ['Valor do Acórdão'] : ['Valor da Sentença', 'Valor da Execução'],
        })),
    }
}

function tarefas(n: number, concluidas: boolean): Obj[] {
    return Array.from({ length: n }, (_, i) => ({
        id: (concluidas ? 70_000 : 80_000) + i,
        numero_processo: processo(300 + i),
        criado_em: `2026-10-${String(1 + (i % 28)).padStart(2, '0')}`,
        prazo: `2026-11-${String(1 + ((i * 3) % 28)).padStart(2, '0')}`,
        concluido_em: concluidas ? `2026-11-${String(1 + ((i * 5) % 16)).padStart(2, '0')}` : null,
        valor_sentenca: 9_000 + i * 1_120,
        valor_acordao: i % 3 ? 11_000 + i * 900 : null,
        concluida: concluidas,
        funcionario_atribuido: funcionarios[i % 5],
    }))
}

export function execucaoEstrategicoFor(unit: string): EstrategicoResponse {
    const meta = metaFor(unit, 'LexFlow')
    // NG, LA e RJ (a API devolve sempre os nomes da NG); LA e RJ com a atividade antiga, sem grau, como a v1.
    const escritorio = ({ NG: 'NG', LA: 'LA', LA_AM: 'LA', RJ: 'RJ', LA_RJ: 'RJ' } as Record<string, string>)[unit]
    if (!escritorio) return { meta }
    const semGrau = escritorio !== 'NG'
    const c = execucaoFor('NG') as unknown as Obj & { stats: Obj }
    const a = acordosFor('NG') as unknown as Obj & { stats: Obj }
    const cAtual = {
        ...c,
        stats: { ...c.stats, duracoes_tempo_execucao_NG: duracoes(39, 214), taxa_atualizacao_execucao_NG: taxa(1) },
        valor_execucao_por_materia: materiaValor(c.execucao_por_materia, 1_850),
        execucao_por_materia: (c.execucao_por_materia as Point[]).map((p) => ({
            ...p,
            value: Math.round(p.value * 0.04),
        })),
        valor_execucao_por_subfase: materiaValor(c.valor_execucao_por_subfase, 0.05),
        execucao_por_ano_ajuizamento_NG: anos(0.05),
        execucao_por_comarca_entrada: comValor(c.execucao_por_comarca_entrada, 27_000),
        execucao_por_comarca_saida: comValor(c.execucao_por_comarca_saida, 26_500),
    }
    const cHist = {
        ...c,
        stats: { ...c.stats, total_em_execucao: c.stats.total_em_execucao_historico },
        quantidade_saida_execucao_por_mes: meses((ano, m) => ({
            value: Math.round(33 + (ano - 2024) * 5 + 9 * Math.cos(m)),
        })),
        valor_saida_execucao_por_mes: c.valor_execucao_saida_periodo_por_mes,
        execucao_entrada_fluxo_cs_por_mes_NG: meses((ano, m) => ({
            '1G': Math.round(18 + (ano - 2024) * 3 + 5 * Math.sin(m)),
            '2G': Math.round(12 + 4 * Math.cos(m)),
            ...(semGrau ? { 'CS (sem grau)': ano === 2026 ? 0 : 3 + (m % 3) } : {}),
            Outros: 4 + (m % 4),
        })),
        execucao_por_ano_ajuizamento_NG: anos(1),
        execucao_media_tempo_por_mes: meses((ano, m) => ({
            value: Math.round((230 - (ano - 2024) * 15 + 20 * Math.sin(m)) * 10) / 10,
        })),
        execucao_por_comarca_total: comValor(c.execucao_por_comarca_total, 23_500),
        execucao_alvaras_expedidos_por_dia_NG: alvarasPorDia(1),
        execucao_alvara_expedido_lista_NG: alvarasLista(18, 0, false),
    }
    const cAnt = {
        stats: {
            ...cAtual.stats,
            total_em_execucao: 41,
            total_saida_execucao_periodo: 44,
            valor_em_execucao: 1_190_400,
            valor_execucao_saida_periodo: 1_102_000,
            duracoes_tempo_execucao_NG: duracoes(44, 230),
            taxa_atualizacao_execucao_NG: taxa(0.9),
        },
    }

    const aAtual = {
        ...a,
        stats: {
            ...a.stats,
            duracoes_tempo_execucao_acordos_NG: duracoes(9, 64),
            valor_ted_saida_execucao_acordos_periodo_NG: 51_300,
        },
        execucao_acordos_por_materia_NG: (a.execucao_acordos_por_materia_NG as Point[]).map((p) => ({
            ...p,
            value: Math.round(p.value * 0.05),
        })),
        valor_execucao_acordos_por_materia_NG: materiaValor(a.execucao_acordos_por_materia_NG, 380),
        valor_execucao_acordos_por_subfase_NG: materiaValor(a.valor_execucao_acordos_por_subfase_NG, 0.03),
        execucao_acordos_por_ano_ajuizamento_NG: anos(0.02),
        execucao_acordos_por_comarca_entrada_NG: comValor(a.execucao_acordos_por_comarca_entrada_NG, 7_500),
        execucao_acordos_por_comarca_saida_NG: comValor(a.execucao_acordos_por_comarca_saida_NG, 7_900),
    }
    const aHist = {
        ...a,
        execucao_acordos_por_ano_ajuizamento_NG: anos(0.35),
        execucao_acordos_media_tempo_por_mes_NG: meses((ano, m) => ({
            value: Math.round((70 - (ano - 2024) * 4 + 8 * Math.cos(m)) * 10) / 10,
        })),
        execucao_acordos_por_comarca_total_NG: comValor(a.execucao_acordos_por_comarca_total_NG, 7_600),
        execucao_acordos_alvaras_expedidos_por_dia_NG: alvarasPorDia(0.5),
        execucao_acordos_alvara_expedido_lista_NG: alvarasLista(7, 100, true),
    }
    const aAnt = {
        stats: {
            ...aAtual.stats,
            total_entrada_execucao_acordos_periodo_NG: 11,
            total_saida_execucao_acordos_periodo_NG: 10,
            duracoes_tempo_execucao_acordos_NG: duracoes(10, 70),
        },
    }

    const equipe = funcionarios.slice(0, 5)
    const concluidas = tarefas(23, true)
    return {
        meta,
        condenacao: { atual: cAtual, historico: cHist, anterior: cAnt },
        acordos: { atual: aAtual, historico: aHist, anterior: aAnt },
        confeccao: {
            stats: {
                total_atividades_criadas_execucao_NG: 64,
                atividades_execucao_abertas_NG: 31,
                atividades_execucao_concluidas_NG: concluidas.length,
            },
            execucao_atividades_lista_filtros_opcoes_NG: {
                funcionarios: equipe,
                situacoes: [
                    { id: 'em_andamento', label: 'Em andamento' },
                    { id: 'vencidas', label: 'Vencidas' },
                    { id: 'concluidas', label: 'Concluídas' },
                ],
            },
            execucao_nao_cumprido_por_motivo_NG: [
                { name: 'Falta de documento', value: 6 },
                { name: 'Cálculo divergente', value: 4 },
                { name: 'Processo suspenso', value: 2 },
            ],
            execucao_taxa_conclusao_por_funcionario_NG: equipe.map((name, i) => ({
                name,
                encerrado_cumprido: 9 - i,
                percent: 82 - i * 9.5,
            })),
            execucao_atividades_lista_NG: concluidas,
            execucao_atividades_abertas_NG: tarefas(31, false),
        },
        confeccao_por_atividade: {
            stats: {},
            execucao_atividades_criadas_por_atividade_NG: (semGrau
                ? ['Elaborar Cumprimento de Sentença', ...ATIVIDADES_CS]
                : ATIVIDADES_CS
            ).map((name, i) => ({
                name,
                concluidos: 9 - i * 2,
                abertas: 12 - i * 3,
            })),
        },
        periodo_anterior: { from: '2026-10-01', to: '2026-10-17' },
        atividades_confeccao: semGrau ? ['Elaborar Cumprimento de Sentença', ...ATIVIDADES_CS] : ATIVIDADES_CS,
    }
}
