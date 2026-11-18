import type { PublicacoesResponse } from '../../pages/dashboards/publicacoes/publicacoes.ts'
import type { DashboardQuery } from '../../types/index.ts'
import { funcionarios, metaFor } from './helpers.ts'

// Publicações fictícias (NG, LA e RJ), no formato da resposta da V2 (app/dashboards/publicacoes.py: a chamada do
// período da rota da v1 com os nomes da NG, os leitores e a comissão). Números e nomes inventados, determinísticos.
// O LA não tem a série "Visualizadas" e a lista dele mostra TRIBUNAL - ÓRGÃO, como na v1.

const ESCRITORIO: Record<string, 'NG' | 'LA' | 'RJ'> = { NG: 'NG', LA: 'LA', LA_AM: 'LA', RJ: 'RJ', LA_RJ: 'RJ' }
const MATERIAS: [string, number][] = [
    ['ANP', 980],
    ['CESTA', 760],
    ['RMC', 540],
    ['MORA', 410],
    ['SEM MATERIA', 120],
]
const DOCUMENTOS: [string, number][] = [
    ['INTIMAÇÃO', 1320],
    ['DESPACHO', 820],
    ['SENTENÇA', 410],
    ['DISTRIBUICAO DE PROCESSO', 260],
]
const ORGAOS: [string, number][] = [
    ['1º JUIZADO ESPECIAL CÍVEL', 640],
    ['2º JUIZADO ESPECIAL CÍVEL', 520],
    ['3ª VARA CÍVEL', 410],
    ['TURMA RECURSAL', 300],
]
const ATIVIDADES: [string, number][] = [
    ['ANÁLISE SENTENÇA', 610],
    ['ELABORAR RECURSO', 320],
    ['VERIFICAR CUMPRIMENTO', 210],
]
const SETORES: [string, number][] = [
    ['RECURSOS', 919],
    ['EXECUÇÃO', 420],
    ['SEM SETOR', 181],
]

const pts = (xs: [string, number][], k: number) => xs.map(([name, v]) => ({ name, value: Math.round(v * k) }))
const iso = (d: Date) =>
    `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`

export function publicacoesFor(unit: string, query?: DashboardQuery): PublicacoesResponse {
    const meta = metaFor(unit, 'LexFlow')
    const u = ESCRITORIO[unit]
    if (!u) return { meta }
    const k = u === 'NG' ? 1 : u === 'LA' ? 1.1 : 0.08
    const de = query?.from ?? meta.from
    const ate = query?.to ?? meta.to
    const dias: string[] = []
    for (let d = new Date(`${de}T00:00:00`); d <= new Date(`${ate}T00:00:00`); d.setDate(d.getDate() + 1)) {
        if (d.getDay() !== 0 && d.getDay() !== 6) dias.push(iso(d))
    }
    const porDia = (base: number) =>
        dias.map((name, i) => ({ name, value: Math.max(0, Math.round((base + 60 * Math.sin(i * 0.9)) * k)) }))
    const recebidas = porDia(180)
    const tratadas = porDia(170)
    const leitores = funcionarios.slice(0, 5).map((n) => n.toUpperCase())
    const totalRec = recebidas.reduce((t, p) => t + p.value, 0)
    const totalTrat = tratadas.reduce((t, p) => t + p.value, 0)
    return {
        meta,
        unidade: u,
        stats: {
            publicacoes_recebidas_periodo_NG: totalRec,
            publicacoes_recebidas_hoje_NG: Math.round(340 * k),
            publicacoes_tratadas_periodo_NG: totalTrat,
            publicacoes_pendentes_NG: Math.round(140 * k),
            media_tempo_tratamento_publicacoes_NG: 0.22,
            publicacoes_pendentes_zeradas_no_periodo_NG: 2,
            dia_referencia_publicacoes_NG: ate,
            publicacoes_tratadas_ultimo_dia_NG: Math.round(203 * k),
            publicacoes_recebidas_dia_referencia_NG: Math.round(340 * k),
            publicacoes_cumpridas_mesmo_dia_dia_referencia_NG: Math.round(203 * k),
            pct_tratadas_mesmo_dia_publicacoes_NG: 59.71,
            publicacoes_com_agendamento_apos_finalizacao_NG: Math.round(totalTrat * 0.67),
            publicacoes_sem_agendamento_apos_finalizacao_NG: totalTrat - Math.round(totalTrat * 0.67),
            publicacoes_com_data_disponibilizacao_NG: Math.round(36665 * k),
            publicacoes_cumpridas_mesmo_dia_chegada_NG: Math.round(24598 * k),
        },
        publicacoes_por_materia_NG: pts(MATERIAS, k),
        publicacoes_por_tipo_documento_NG: pts(DOCUMENTOS, k),
        publicacoes_por_tribunal_NG:
            u === 'LA'
                ? [
                      { name: 'TJAM', value: Math.round(2700 * k) },
                      { name: 'TRF1', value: 7 },
                      { name: 'TRF2', value: 1 },
                  ]
                : [
                      { name: u === 'RJ' ? 'TJRJ' : 'TJAM', value: Math.round(2700 * k) },
                      { name: 'TJPB', value: Math.round(126 * k) },
                      { name: 'TRF5', value: 5 },
                      { name: 'TJPA', value: 4 },
                      { name: 'TRF1', value: 3 },
                      { name: 'STJ', value: 1 },
                  ],
        publicacoes_por_orgao_NG: pts(ORGAOS, k),
        publicacoes_agendamento_apos_finalizacao_por_atividade_NG: pts(ATIVIDADES, k),
        publicacoes_agendamento_apos_finalizacao_por_setor_NG: pts(SETORES, k),
        publicacoes_cumprido_por_leitor_NG: leitores.map((name, i) => ({
            name,
            value: Math.round((1645 - i * 300) * k),
        })),
        publicacoes_pendentes_por_leitor_NG: leitores
            .slice(0, 3)
            .map((name, i) => ({ name, value: Math.round((40 - i * 10) * k) })),
        publicacoes_recebidas_por_dia_NG: recebidas,
        publicacoes_tratadas_por_dia_NG: tratadas,
        ...(u === 'LA' ? {} : { publicacoes_visualizadas_por_dia_NG: porDia(25) }),
        publicacoes_pendentes_por_dias_atraso_NG: [
            { name: '0', value: Math.round(134 * k) },
            { name: '2', value: 1 },
            { name: '5', value: 2 },
        ],
        publicacoes_lista_NG: Array.from({ length: 42 }, (_, i) => ({
            id: 464700 + i,
            status: ['Cumprido', 'Visualizado', 'Não visualizado', 'Cumprido'][i % 4],
            descricao: DOCUMENTOS[i % DOCUMENTOS.length][0],
            atividade: MATERIAS[i % MATERIAS.length][0],
            funcionario: leitores[i % leitores.length],
            pessoa_setor:
                u === 'LA'
                    ? `TJAM - ${ORGAOS[i % ORGAOS.length][0]}`
                    : i % 3 === 0
                      ? 'SEM AGENDAMENTO'
                      : `RECURSOS - ${ATIVIDADES[i % ATIVIDADES.length][0]} (${i % 2 ? 'cumprido' : 'em andamento'})`,
            criado_em: dias[i % Math.max(dias.length, 1)] ?? de,
            concluida: i % 4 === 0 || i % 4 === 3,
        })),
        leitores: ['SEM LEITOR', ...leitores],
        comissao: leitores.slice(0, 3).map((funcionario, i) => {
            const certas = Math.round((1154 - i * 250) * k)
            const erradas = Math.round((491 - i * 100) * k)
            return {
                funcionario,
                qtd_lidas: certas + erradas,
                qtd_certas: certas,
                qtd_erradas: erradas,
                valor_certa: 0.2,
                valor_errada: 0.5,
                comissao: Math.round((certas * 0.2 - erradas * 0.5) * 100) / 100,
            }
        }),
    }
}
