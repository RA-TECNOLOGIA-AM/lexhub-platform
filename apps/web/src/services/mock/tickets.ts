import type { TicketsResponse } from '../../pages/dashboards/tickets/tickets.ts'
import type { DashboardQuery } from '../../types/index.ts'
import { funcionarios, metaFor } from './helpers.ts'

// Tickets (banco NG) fictícios, no formato da rota /tickets da v1: números, nomes e descrições inventados e
// determinísticos (sem Math.random). Só a NG, como a v1; outra unidade, só o `meta`.

const MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
const CATEGORIAS: [string, number][] = [
    ['bug', 58],
    ['acesso', 27],
    ['suporte', 22],
    ['Sem categoria', 8],
    ['sugestao-ideia', 4],
    ['duvida', 3],
    ['dashboard', 2],
]
const SUBCATEGORIAS: [string, number][] = [
    ['Sem subcategoria', 41],
    ['Outros', 23],
    ['Chat interno', 18],
    ['Banco de documentos', 14],
    ['E-mail corporativo', 9],
    ['Computador ou notebook', 7],
    ['Formulários', 6],
    ['Acesso ao servidor', 6],
]
const DESCRICOES = [
    'Erro ao salvar o andamento do processo no sistema',
    'Solicito acesso à pasta compartilhada do setor',
    'O computador não liga depois da atualização',
    'Não consigo entrar no chat interno com o meu usuário',
    'Relatório do mês não abre no navegador',
    'Criar e-mail corporativo para a nova colaboradora',
]
const ESCRITORIOS: Record<string, string> = { NG: 'NG' }

function filtrado(query: DashboardQuery | undefined): number {
    // Com um filtro de página, uma fração dos números (o mock não recalcula nada de verdade).
    const f = query?.filters ?? {}
    const n = [f.ticket_servidor, f.ticket_categoria, f.ticket_subcategoria, f.ticket_status].filter(
        (v) => v?.length,
    ).length
    return n === 0 ? 1 : 0.45 ** n
}

export function ticketsFor(unit: string, query?: DashboardQuery): TicketsResponse {
    const meta = metaFor(unit, 'NG')
    if (!ESCRITORIOS[unit]) return { meta }
    const k = filtrado(query)
    const r = (v: number) => Math.round(v * k)
    const total = r(124)
    const encerrados = r(97)
    const equipe = funcionarios.slice(0, 6)
    const porMes = []
    for (let ano = 2025; ano <= 2026; ano++)
        for (let m = 0; m < 12 && !(ano === 2026 && m > 10); m++)
            porMes.push({ name: `${MESES[m]} ${ano}`, value: r(150 + (ano - 2025) * 30 + 45 * Math.sin(m * 0.8)) })
    return {
        meta,
        dashboard: 'tickets',
        stats: {
            total_tickets: total,
            tickets_ag_atendimento: r(6),
            tickets_atendimento: r(9),
            total_encerrados: encerrados,
            tickets_cancelados: r(4),
            tickets_reprovados: r(5),
            duracao_atendimento: 18.6,
            taxa_resolucao: total > 0 ? (encerrados / total) * 100 : 0,
            total_tickets_periodo_anterior: r(112),
        },
        tickets_por_categoria: CATEGORIAS.map(([name, v]) => ({ name, value: r(v) })),
        tickets_por_subcategoria: SUBCATEGORIAS.map(([name, v]) => ({ name, value: r(v) })),
        tickets_por_abertura: equipe.slice(0, 5).map((name, i) => ({ name, value: r(19 - i * 3) })),
        tickets_por_fechamento: ['Equipe Suporte 1', 'Equipe Suporte 2', 'Equipe Suporte 3'].map((name, i) => ({
            name,
            value: r(46 - i * 13),
        })),
        tickets_por_mes: porMes,
        tickets_por_status: [
            { name: 'Resolvido', value: encerrados },
            { name: 'Em Atendimento', value: r(9) },
            { name: 'Em Análise', value: r(6) },
            { name: 'Cancelado', value: r(4) },
        ],
        tickets_abertos_por_servidor: [
            { name: 'LA-AM', value: r(4) },
            { name: 'NG', value: r(3) },
            { name: 'LA-RJ', value: r(2) },
        ],
        tickets_encerrados_por_servidor: [
            { name: 'LA-AM', value: r(44) },
            { name: 'NG', value: r(38) },
            { name: 'LA-RJ', value: r(15) },
        ],
        tickets_media_encerrados_por_colaborador: [
            { name: 'Equipe Suporte 1', value: 3.83 },
            { name: 'Equipe Suporte 2', value: 2.75 },
            { name: 'Equipe Suporte 3', value: 1.9 },
        ],
        recent_activities: Array.from({ length: 12 }, (_, i) => {
            const [categoria] = CATEGORIAS[i % 4 === 3 ? 4 : i % 3]
            const status = ['Em Atendimento', 'Resolvido', 'Em Análise', 'Resolvido'][i % 4]
            return {
                id: `t-${1200 + i}`,
                type: status === 'Resolvido' ? 'success' : 'pending',
                title: categoria,
                categoria,
                status,
                description: `${DESCRICOES[i % DESCRICOES.length]}.`,
                time: i === 0 ? 'há 12 min' : i < 5 ? `há ${i} h` : `há ${i - 3} dia${i > 4 ? 's' : ''}`,
                user: equipe[i % equipe.length],
                servidor: ['NG', 'LA-AM', 'LA-RJ'][i % 3],
                ticket_numero: String(1200 + i),
                anydesk: i % 3 === 0 ? String(100200300 + i * 7) : null,
                url: i % 4 === 1 ? 'https://example.com/chat' : null,
                minutos_atras: i * 90,
            }
        }),
    }
}
