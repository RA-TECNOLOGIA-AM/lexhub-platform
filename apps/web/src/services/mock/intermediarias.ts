import type { PendenciasIntermediariasResponse } from '../../pages/dashboards/pendencias-intermediarias/intermediarias.ts'
import { metaFor } from './helpers.ts'

// Pendências Intermediárias fictícias (NG, LA e RJ), no formato da resposta da V2 (app/dashboards/
// pendencias_intermediarias.py: a chamada do período e a do histórico com os nomes da NG). Números e nomes
// inventados, determinísticos.

// O RJ usa o cálculo do NG (mesmo setor PENDÊNCIA).
const ESCRITORIO: Record<string, 'NG' | 'LA' | 'RJ'> = { NG: 'NG', LA: 'LA', LA_AM: 'LA', RJ: 'RJ', LA_RJ: 'RJ' }
const PESSOAS = ['Ana Ribeiro', 'Bruno Lima', 'Carla Souza', 'Diego Prado']
const ATIVIDADES_NG = ['SANAR PENDÊNCIA 1G', 'SOLICITAR DOCS COM CLIENTE', 'OBTER DOCUMENTOS PARA EXECUÇÃO']
const ATIVIDADES_LA = [
    'SOLICITAR DOCS DO CLIENTE',
    'SOLICITAR DOCS DE HIPOSSUFICIÊNCIA DO CLIENTE PARA RECURSO',
    'VERIFICAR NÃO CUMPRIMENTO',
    'PROVIDENCIAR PROCURAÇÃO',
]
const STATUS = ['Recebido', 'Visualizado', 'Iniciado', 'Encerrado Cumprido', 'Encerrado Não Cumprido']

const iso = (d: Date) => d.toISOString().slice(0, 10)
const MESES_PT = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']

export function intermediariasFor(unit: string): PendenciasIntermediariasResponse {
    const meta = metaFor(unit, 'LexFlow')
    const u = ESCRITORIO[unit]
    if (!u) return { meta }
    let semente = u === 'NG' ? 11 : u === 'RJ' ? 47 : 29
    const rnd = () => {
        semente = (semente * 1103515245 + 12345) % 2147483648
        return semente / 2147483648
    }
    const int = (a: number, b: number) => Math.round(a + (b - a) * rnd())
    const comoNG = u !== 'LA'
    const atividades = comoNG ? ATIVIDADES_NG : ATIVIDADES_LA
    const setor = comoNG ? 'PENDÊNCIA' : 'PENDÊNCIAS'

    // Histórico: concluídas por dia (dias úteis desde jan/2025), por funcionário.
    const porDiaPorFuncionario: Record<string, { name: string; value: number }[]> = {}
    const porDia = new Map<string, number>()
    for (
        let d = new Date('2025-01-02T12:00:00Z');
        d <= new Date('2026-11-18T12:00:00Z');
        d.setUTCDate(d.getUTCDate() + 1)
    ) {
        if (d.getUTCDay() === 0 || d.getUTCDay() === 6) continue
        for (const p of PESSOAS) {
            const v = int(0, 9)
            ;(porDiaPorFuncionario[p] ??= []).push({ name: iso(d), value: v })
            porDia.set(iso(d), (porDia.get(iso(d)) ?? 0) + v)
        }
    }
    const dias = [...porDia.entries()].map(([name, value]) => ({ name, value }))
    const porMes = new Map<string, number>()
    for (const p of dias) {
        const k = `${MESES_PT[Number(p.name.slice(5, 7)) - 1]} ${p.name.slice(0, 4)}`
        porMes.set(k, (porMes.get(k) ?? 0) + p.value)
    }
    const media = PESSOAS.map((name) => ({ name, value: int(30, 95) / 10 })).sort((a, b) => b.value - a.value)

    const lista = Array.from({ length: 24 }, (_, i) => {
        const status = STATUS[i % STATUS.length]
        const encerrada = status.startsWith('Encerrado')
        const prazo = new Date(Date.UTC(2026, 10, 1 + (i % 20)))
        const atividade = atividades[i % atividades.length]
        return {
            id: 90000 + i * 37,
            status,
            descricao: `PROVIDENCIAR OS DOCUMENTOS DO CLIENTE PARA O PROCESSO (ITEM ${i + 1})`,
            pessoa_setor: `${setor} - ${atividade}`,
            funcionario: PESSOAS[i % PESSOAS.length],
            funcionario_atribuido: PESSOAS[i % PESSOAS.length],
            atividade,
            prazo: iso(prazo),
            criado_em: iso(new Date(prazo.getTime() - 5 * 86400000)),
            operacao: u === 'NG' ? 'NGAM' : u === 'RJ' ? 'NGRJ' : 'CONSUMIDOR',
            ...(encerrada ? { encerrado_pelo_responsavel: i % 4 !== 0 } : {}),
            ...(encerrada && i % 4 === 0 ? { funcionario_encerramento: PESSOAS[(i + 1) % PESSOAS.length] } : {}),
            em_andamento: status === 'Iniciado',
            vencida: !encerrada && prazo.getTime() < Date.UTC(2026, 10, 18),
            vence_hoje: !encerrada && iso(prazo) === '2026-11-18',
            concluida: encerrada,
        }
    })
    const porAtividade = atividades.map((name) => ({ name, value: int(4, 40) })).sort((a, b) => b.value - a.value)
    const demandas = PESSOAS.map((name) => {
        const c = int(10, 60)
        const n = int(0, 12)
        return { name, encerrado_cumprido: c, encerrado_nao_cumprido: n, total: c + n }
    }).sort((a, b) => b.total - a.total)
    const dilacoes = PESSOAS.map((funcionario, i) => {
        const total = demandas[i].total
        const qtd = [1, 4, 7, 12][i]
        return {
            funcionario,
            qtd_dilacoes: qtd,
            total_encerrados: total,
            qtd_resolvidos: demandas[i].encerrado_cumprido,
            taxa_dilacao: Math.round((1000 * qtd) / total) / 10,
        }
    })
    const encerrados = dilacoes.reduce((s, d) => s + d.total_encerrados, 0)
    const count = dilacoes.reduce((s, d) => s + d.qtd_dilacoes, 0)
    const opcoes = {
        funcionarios: PESSOAS,
        atividades,
        status: STATUS,
        situacoes: [
            { id: 'em_andamento', label: 'Em andamento' },
            { id: 'vencidas', label: 'Vencidas' },
            { id: 'vencem_hoje', label: 'Vencem hoje' },
            { id: 'concluidas', label: 'Concluídas' },
        ],
    }
    const cards = (pre: string, suf: string) => ({
        [`${pre}total${suf}`]: lista.filter((t) => !t.concluida).length,
        [`${pre}em_andamento${suf}`]: lista.filter((t) => t.em_andamento).length,
        [`${pre}vencidas${suf}`]: lista.filter((t) => t.vencida).length,
        [`${pre}vencem_hoje${suf}`]: lista.filter((t) => t.vence_hoje).length,
        [`${pre}concluidas${suf}`]: lista.filter((t) => t.concluida).length,
    })
    const taxa = Math.round((1000 * count) / encerrados) / 10
    return {
        meta,
        unidade: u,
        stats: {
            total_atividades_intermediarias_NG: lista.filter((t) => !t.concluida).length,
            atividades_intermediarias_em_andamento_NG: lista.filter((t) => t.em_andamento).length,
            atividades_intermediarias_vencidas_NG: lista.filter((t) => t.vencida).length,
            atividades_intermediarias_vencem_hoje_NG: lista.filter((t) => t.vence_hoje).length,
            atividades_intermediarias_concluidas_NG: encerrados,
            ...Object.fromEntries(
                Object.entries(cards('por_prazo_', '_intermediarias_NG')).map(([k, v]) => [
                    k.replace('por_prazo_total', 'total_por_prazo'),
                    v,
                ]),
            ),
            dilacoes_intermediarias_total_encerrados_NG: encerrados,
            dilacoes_intermediarias_count_NG: count,
            dilacoes_intermediarias_taxa_NG: taxa,
            dilacoes_intermediarias_faixa_NG: taxa <= 5 ? 'ouro' : taxa <= 10 ? 'prata' : taxa <= 15 ? 'bronze' : null,
        },
        intermediarias_processos_por_atividade_NG: porAtividade,
        intermediarias_processos_por_atividade_por_prazo_NG: porAtividade.map((p) => ({ ...p, value: p.value + 3 })),
        intermediarias_demandas_por_funcionario_NG: demandas,
        intermediarias_demandas_por_funcionario_por_prazo_NG: demandas,
        intermediarias_atividades_lista_NG: lista,
        intermediarias_por_prazo_lista_NG: lista.slice(0, 18),
        intermediarias_atividades_lista_filtros_opcoes_NG: opcoes,
        intermediarias_por_prazo_lista_filtros_opcoes_NG: opcoes,
        dilacoes_intermediarias_por_funcionario_NG: dilacoes,
        intermediarias_concluidas_por_mes_NG: [...porMes.entries()].map(([name, value]) => ({ name, value })),
        intermediarias_concluidas_por_dia_NG: dias,
        intermediarias_concluidas_por_dia_por_funcionario_NG: porDiaPorFuncionario,
        intermediarias_concluidas_por_prazo_por_mes_NG: [...porMes.entries()].map(([name, value]) => ({ name, value })),
        intermediarias_concluidas_por_prazo_por_dia_NG: dias,
        intermediarias_concluidas_por_prazo_por_dia_por_funcionario_NG: porDiaPorFuncionario,
        media_intermediarias_concluidas_por_funcionario_NG: media,
        media_intermediarias_concluidas_por_prazo_por_funcionario_NG: media,
    }
}
