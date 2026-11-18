import type { RecursalResponse } from '../../pages/dashboards/recursal/recursal.ts'
import { funcionarios, metaFor } from './helpers.ts'

// Recursal fictício (NG, LA e RJ), no formato da resposta da V2 (app/dashboards/recursal.py: as chamadas da página
// da v1 juntas, com os nomes da NG). Números, nomes e processos inventados e determinísticos (sem Math.random).
// O LA não tem "Cancelados" nem "Meta de provimento", como na v1. Outra unidade: só o `meta`.

const ESCRITORIO: Record<string, 'NG' | 'LA' | 'RJ'> = { NG: 'NG', LA: 'LA', LA_AM: 'LA', RJ: 'RJ', LA_RJ: 'RJ' }
const MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']

const SUBFASES: [string, number][] = [
    ['AG. CONTRARRAZÕES', 1338],
    ['AG. JULGAMENTO', 1102],
    ['AG. CONFECÇÃO RECURSO', 760],
    ['AG. ANÁLISE RECURSO', 512],
    ['AG. PROTOCOLO RECURSO', 301],
    ['AG. TRÂNSITO EM JULGADO', 188],
]
const MATERIAS: [string, number][] = [
    ['CESTA', 1420],
    ['RMC', 980],
    ['MORA', 760],
    ['ANP', 520],
    ['SEM MATERIA', 210],
]
const COMPETENCIAS: [string, number][] = [
    ['Turma Recursal', 2400],
    ['Câmara Cível', 1300],
    ['Câmaras Reunidas', 290],
]
const VARAS: [string, number][] = [
    ['1º vara', 900],
    ['2º vara', 760],
    ['3º vara', 520],
    ['Sem vara', 310],
]
const STATUS_1G: [number, string, number][] = [
    [19, 'IMPROCEDENTE', 115],
    [20, 'PROCEDENTE COM PROVEITO ECONÔMICO', 74],
    [18, 'EXTINTO SEM MÉRITO', 53],
    [21, 'PARCIALMENTE PROCEDENTE COM PROVEITO ECONÔMICO', 41],
]
const STATUS_2G: [number, string, number][] = [
    [19, 'IMPROCEDENTE', 61],
    [21, 'PROCEDENTE (COM PROVEITO ECONÔMICO)', 48],
    [20, 'PARCIALMENTE PROCEDENTE (COM PROVEITO ECONÔMICO)', 22],
    [18, 'EXTINTO SEM MÉRITO', 14],
]
const DECISOES: [string, number][] = [
    ['mantido_ganho', 15],
    ['ganho_ampliado', 7],
    ['revertido_ganho', 12],
    ['ganho_reduzido', 2],
    ['mantido_perda', 34],
    ['revertido_perda', 7],
    ['extincao_reajuizar', 21],
    ['instrucao_retomada', 4],
]
const JUIZES = [
    'Juiz Exemplo Um',
    'Juíza Exemplo Dois',
    'Juiz Exemplo Três',
    'Juíza Exemplo Quatro',
    'Juiz Exemplo Cinco',
]
const RELATORES = ['Desembargador Alfa', 'Desembargadora Beta', 'Desembargador Gama', 'Desembargadora Delta']
const ATIVIDADES: [string, number][] = [
    ['ANÁLISE SENTENÇA', 346],
    ['VERIFICAR CUMPRIMENTO - SENTENÇA', 290],
    ['CONFECÇÃO RECURSO INOMINADO', 181],
    ['CONTRARRAZÕES', 122],
    ['AVR - REVISÃO - SENTENÇA (1G)', 64],
]

const pontos = (xs: [string, number][], k = 1) => {
    const total = xs.reduce((t, [, v]) => t + Math.round(v * k), 0)
    return xs.map(([name, v], i) => ({
        name,
        value: Math.round(v * k),
        percent: Math.round(((v * k) / total) * 1000) / 10,
        valor_causa: Math.round(v * k * (310 + i * 45)),
    }))
}
const iniciais = (n: string) =>
    n
        .split(' ')
        .filter((p) => p.length > 2)
        .slice(0, 2)
        .map((p) => p[0])
        .join('')
        .toUpperCase()
const ranking = (nomes: string[], base: number) =>
    nomes.map((name, i) => {
        const total = base - i * 3
        const fav = Math.max(0, Math.round(total * (0.75 - i * 0.12)))
        const des = Math.max(0, Math.round(total * (0.2 + i * 0.08)))
        const outros = Math.max(0, total - fav - des)
        const p = (x: number) => Math.round((x / total) * 1000) / 10
        return {
            name,
            initials: iniciais(name),
            total_casos: total,
            taxa_sucesso: p(fav),
            fav,
            des,
            outros,
            percent_fav: p(fav),
            percent_des: p(des),
            percent_outros: p(outros),
        }
    })

function porDia(base: number) {
    const out: { name: string; value: number }[] = []
    for (let ano = 2026, m = 6; m <= 10; m++) {
        for (let d = 1; d <= (m === 10 ? 18 : 28); d++) {
            const wd = new Date(ano, m, d).getDay()
            if (wd === 0 || wd === 6) continue
            out.push({
                name: `${ano}-${String(m + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`,
                value: Math.max(0, Math.round(base + 6 * Math.sin(d * 1.3) + (d % 4))),
            })
        }
    }
    return out
}

export function recursalFor(unit: string): RecursalResponse {
    const meta = metaFor(unit, 'LexFlow')
    const u = ESCRITORIO[unit]
    if (!u) return { meta }
    const k = u === 'NG' ? 1 : u === 'LA' ? 0.8 : 0.15
    const equipe = funcionarios.slice(0, 6)
    const totalEstoque = Math.round(SUBFASES.reduce((t, [, v]) => t + v, 0) * k)
    const entrada = Math.round(431 * k)
    const lista = Array.from({ length: 34 }, (_, i) => {
        const [atividade] = ATIVIDADES[i % ATIVIDADES.length]
        const concluida = i % 3 === 0
        const vencida = !concluida && i % 5 === 1
        return {
            id: 102000 + i * 7,
            status: concluida
                ? i % 6 === 0
                    ? 'Encerrado Não Cumprido'
                    : 'Encerrado Cumprido'
                : vencida
                  ? 'Recebido'
                  : 'Visualizado',
            descricao: atividade.toLowerCase(),
            pessoa_setor: `RECURSOS - ${atividade}`,
            funcionario: equipe[i % equipe.length],
            funcionario_atribuido: equipe[i % equipe.length],
            funcionario_encerramento: concluida ? equipe[(i + (i % 9 === 0 ? 1 : 0)) % equipe.length] : undefined,
            encerrado_pelo_responsavel: concluida ? i % 9 !== 0 : undefined,
            atividade,
            prazo: `2026-11-${String(2 + (i % 26)).padStart(2, '0')}`,
            criado_em: `2026-11-${String(1 + (i % 17)).padStart(2, '0')}`,
            em_andamento: !concluida,
            vencida,
            vence_hoje: i % 11 === 4,
            concluida,
        }
    })
    const dias = Object.fromEntries(equipe.map((f, i) => [f, porDia(9 - i)]))
    const somaDias = porDia(0).map((p) => ({
        name: p.name,
        value: Object.values(dias).reduce((t, s) => t + (s.find((x) => x.name === p.name)?.value ?? 0), 0),
    }))
    const porMes = new Map<string, number>()
    for (const p of somaDias) {
        const nome = `${MESES[Number(p.name.slice(5, 7)) - 1]} ${p.name.slice(0, 4)}`
        porMes.set(nome, (porMes.get(nome) ?? 0) + p.value)
    }
    const decTotal = DECISOES.reduce((t, [, v]) => t + Math.round(v * k), 0)
    const extintos = {
        controle_processo_extintos_com_merito_2g_qtd_recursal_NG: Math.round(105 * k),
        controle_processo_extintos_com_merito_2g_valor_causa_acordao_recursal_NG: Math.round(252405 * k),
        controle_processo_taxa_provimento_2g_recursal_NG: 63.03,
        controle_processo_extintos_sem_merito_2g_qtd_recursal_NG: Math.round(14 * k),
        controle_processo_extintos_sem_merito_2g_valor_causa_acordao_recursal_NG: Math.round(31200 * k),
    }
    const porTipo = [
        { label: 'IMPROCEDENTE', quantidade: Math.round(41 * k), valor_causa: Math.round(98000 * k) },
        {
            label: 'PROCEDENTE (COM PROVEITO ECONÔMICO)',
            quantidade: Math.round(38 * k),
            valor_causa: Math.round(101000 * k),
        },
        {
            label: 'PARCIALMENTE PROCEDENTE (COM PROVEITO ECONÔMICO)',
            quantidade: Math.round(26 * k),
            valor_causa: Math.round(53405 * k),
        },
    ]
    const dist = (xs: [string, number][], chave: string) => ({
        estoque: { stats: { total_recursal_NG: totalEstoque }, [`recursal_por_${chave}_NG`]: pontos(xs, k) },
        entrada: {
            stats: { entrada_recursal_NG: entrada },
            [`recursal_por_${chave}_NG`]: pontos(xs, (k * entrada) / totalEstoque),
        },
    })
    const status = (xs: [number, string, number][], campo: 'id_1g' | 'id_2g') =>
        xs.map(([id, name, v], i) => ({
            name,
            value: Math.round(v * k),
            valor_causa: Math.round(v * k * (420 + i * 30)),
            [campo]: id,
        }))
    return {
        meta,
        unidade: u,
        periodo: {
            stats: {
                entrada_recursal_NG: entrada,
                valor_causa_acordo_recursal_NG: Math.round(2232443 * k),
                ...(u === 'LA'
                    ? {}
                    : {
                          avr_retorno_recurso_cancelado_NG: Math.round(3 * k),
                          retorno_cr_recurso_cancelado_NG: Math.round(2 * k),
                          provimento_mensal_qtd_NG: Math.round(62 * k),
                          provimento_mensal_meta_NG: 80,
                      }),
                total_por_prazo_atividades_recursos_NG: Math.round(597 * k),
                por_prazo_em_andamento_atividades_recursos_NG: Math.round(597 * k),
                por_prazo_vencidas_atividades_recursos_NG: Math.round(49 * k),
                por_prazo_vencem_hoje_atividades_recursos_NG: Math.round(12 * k),
                por_prazo_concluidas_atividades_recursos_NG: Math.round(410 * k),
                total_atividades_recursos_NG: Math.round(1615 * k),
                atividades_recursos_em_andamento_NG: Math.round(612 * k),
                atividades_recursos_vencidas_NG: Math.round(49 * k),
                atividades_recursos_vencem_hoje_NG: Math.round(12 * k),
                atividades_recursos_concluidas_NG: Math.round(1003 * k),
                ...(u === 'RJ' ? extintos : {}),
            },
            recursal_processos_por_atividade_NG: pontos(ATIVIDADES, k),
            recursal_demandas_por_funcionario_NG: equipe.map((name, i) => ({
                name,
                encerrado_cumprido: Math.round((184 - i * 25) * k),
                encerrado_nao_cumprido: Math.round((48 - i * 6) * k),
            })),
            recursal_media_resolvidos_por_funcionario_NG: equipe.map((name, i) => ({
                name,
                value: Math.round((14.45 - i * 1.9) * 100) / 100,
            })),
            recursal_atividades_lista_NG: lista,
            recursal_atividades_lista_filtros_opcoes_NG: {
                funcionarios: equipe,
                atividades: ATIVIDADES.map(([a]) => a),
                status: ['Recebido', 'Visualizado', 'Encerrado Cumprido', 'Encerrado Não Cumprido', 'Cancelado'],
                situacoes: [
                    { id: 'em_andamento', label: 'Em andamento' },
                    { id: 'vencidas', label: 'Vencidas' },
                    { id: 'vencem_hoje', label: 'Vencem hoje' },
                    { id: 'concluidas', label: 'Concluídas' },
                ],
            },
        },
        historico: { stats: { total_recursal_NG: totalEstoque } },
        producao: {
            recursal_resolvidos_por_mes_NG: [...porMes].map(([name, value]) => ({ name, value })),
            recursal_resolvidos_por_dia_NG: somaDias,
            recursal_resolvidos_por_dia_por_funcionario_NG: dias,
        },
        subfase: dist(SUBFASES, 'subfase'),
        materia: dist(MATERIAS, 'materia'),
        competencia: dist(COMPETENCIAS, 'competencia'),
        vara: dist(VARAS, 'vara'),
        decisoes: {
            stats: {
                total_decisoes_recursal_NG: decTotal,
                ...Object.fromEntries(
                    DECISOES.flatMap(([d, v]) => [
                        [`total_${d}_recurso_NG`, Math.round(v * k)],
                        [`percent_${d}_recursal_NG`, Math.round(((v * k) / decTotal) * 1000) / 10],
                    ]),
                ),
            },
        },
        status_1g: { recursal_por_status_1g_NG: status(STATUS_1G, 'id_1g') },
        status_2g: { recursal_por_status_2g_NG: status(STATUS_2G, 'id_2g') },
        juizes: { ranking_juizes_recursal_NG: ranking(JUIZES, 22) },
        relatores: { ranking_relatores_recursal_NG: ranking(RELATORES, 18) },
        controle: {
            stats: extintos,
            controle_processo_extintos_com_merito_2g_por_tipo_sentenca_valor_acordao_recursal_NG: porTipo,
        },
        // Comissão do setor Recursos: só NG (como a v1); números fictícios.
        comissao:
            u === 'NG'
                ? {
                      linhas: equipe.slice(0, 4).map((funcionario, i) => {
                          const qa = 120 - i * 25
                          const qc = 60 - i * 12
                          const erros = i === 1 ? 2 : 0
                          const total = qa * 0.5 + qc * 2 - erros * 1 + (erros === 0 ? 100 : 0)
                          return {
                              funcionario,
                              subsetores: i % 2 ? ['Análise'] : ['Análise', 'Confecção'],
                              qtd_analise: qa,
                              valor_qtd_analise: qa * 0.5,
                              qtd_confeccao: qc,
                              valor_qtd_confeccao: qc * 2,
                              erros_analise: erros,
                              desconto_analise: erros * 1,
                              erros_confeccao: 0,
                              desconto_confeccao: 0,
                              bonus_meta_qualidade: 0,
                              bonus_zero_retrabalho: erros === 0 ? 100 : 0,
                              valor_total: total,
                          }
                      }),
                      detalhes: [
                          {
                              funcionario: equipe[1],
                              subsetor: 'Análise',
                              numero_processo: '0001234-56.2025.8.04.0001',
                              atividade_origem: 'ANÁLISE SENTENÇA',
                              data: '2026-11-04',
                              tipo_desconto: 'Erro de análise',
                              valor_desconto: 1,
                              motivo_texto: 'Retorno para ajuste do cálculo.',
                          },
                          {
                              funcionario: equipe[1],
                              subsetor: 'Análise',
                              numero_processo: '0004321-65.2025.8.04.0001',
                              atividade_origem: 'ANÁLISE SENTENÇA',
                              data: '2026-11-10',
                              tipo_desconto: 'Erro de análise',
                              valor_desconto: 1,
                              motivo_texto: 'Documento faltando.',
                          },
                      ],
                      meta_atingida: false,
                      qtd_provimento: Math.round(62 * k),
                      meta: 80,
                  }
                : null,
        opcoes: {
            status_1g: STATUS_1G.map(([id, label]) => ({ id, label })),
            status_2g: STATUS_2G.map(([id, label]) => ({ id, label })),
            decisoes: DECISOES.map(([id]) => ({
                id: id === 'extincao_reajuizar' ? 'extincao_permite_reajuizar' : id,
                label: id.replace(/_/g, ' ').replace(/^./, (c) => c.toUpperCase()),
            })),
            juizes: JUIZES,
            relatores: RELATORES,
            materias: MATERIAS.map(([m]) => m),
            competencias: COMPETENCIAS.map(([c]) => c),
            varas: VARAS.map(([v]) => v),
            subfases: SUBFASES.map(([s]) => s),
            extintos_2g: [
                { id: 'com_merito', label: 'Extintos com mérito (2º grau)' },
                { id: 'sem_merito', label: 'Extintos sem mérito (2º grau)' },
            ],
        },
    }
}
