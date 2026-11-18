import { describe, expect, it } from 'vitest'
import {
    abasDoFeed,
    atividades,
    duracaoHoras,
    filtrarFeed,
    lerTickets,
    porAno,
    variacao,
    type TicketsResponse,
} from './tickets.ts'
import { ticketsFilters } from './filters.ts'
import { ticketsFor } from '../../../services/mock/tickets.ts'

const meta = { unit: 'NG' } as unknown as TicketsResponse['meta']

describe('as contas da página da v1', () => {
    it('duração como o formatDuration da v1', () => {
        expect(duracaoHoras(0)).toBe('0h')
        expect(duracaoHoras(0.5)).toBe('30min')
        expect(duracaoHoras(5.25)).toBe('5h 15min')
        expect(duracaoHoras(5)).toBe('5h')
        expect(duracaoHoras(49)).toBe('2d 1h')
        expect(duracaoHoras(48)).toBe('2d')
    })
    it('variação só com o mês anterior > 0', () => {
        expect(variacao(133, 126)).toBe(5.56)
        expect(variacao(10, 0)).toBeNull()
        expect(variacao(10, null)).toBeNull()
    })
    it('série histórica por ano e o pico', () => {
        const { anos, pico } = porAno([
            { name: 'dez 2025', value: 9 },
            { name: 'jan 2026', value: 12 },
            { name: 'fev 2026', value: 4 },
        ])
        expect([...anos.keys()]).toEqual(['2025', '2026'])
        expect(anos.get('2026')?.slice(0, 3)).toEqual([12, 4, null])
        expect(pico).toEqual({ ano: '2026', mes: 0, valor: 12 })
    })
    it('lê a resposta: % sem subcategoria, média da equipe e o comparativo', () => {
        const t = lerTickets({
            meta,
            stats: {
                total_tickets: 20,
                total_tickets_periodo_anterior: 10,
                total_encerrados: 15,
                duracao_atendimento: 30,
            },
            tickets_por_subcategoria: [
                { name: 'Sem subcategoria', value: 6 },
                { name: 'Outros', value: 4 },
            ],
            tickets_media_encerrados_por_colaborador: [
                { name: 'A', value: 3 },
                { name: 'B', value: 1 },
            ],
        })
        expect(t.variacao).toBe(100)
        expect(t.pctSemSubcategoria).toBe(60)
        expect(t.mediaEquipe).toBe(2)
        expect(t.dentroSla).toBe(false)
    })
})

describe('feed de movimentações', () => {
    const lista = atividades([
        {
            id: '1',
            type: 'success',
            categoria: 'bug',
            description: 'Erro no login',
            user: 'Ana',
            ticket_numero: '1195',
            servidor: 'NG',
        },
        { id: '2', type: 'pending', title: 'Acesso', description: 'Pasta', user: 'Bia', servidor: 'LA-AM' },
        { id: '3', type: 'x', categoria: 'bug', description: 'Outro erro', user: 'Caio' },
    ])
    it('categoria em minúsculas (ou o título) e tipo desconhecido vira warning', () => {
        expect(lista.map((a) => a.categoria)).toEqual(['bug', 'acesso', 'bug'])
        expect(lista[2].tipo).toBe('warning')
    })
    it('abas pela frequência e busca por #ID, autor e servidor', () => {
        expect(abasDoFeed(lista).map((a) => `${a.value}:${a.total}`)).toEqual(['todos:3', 'bug:2', 'acesso:1'])
        expect(filtrarFeed(lista, 'todos', '#1195').map((a) => a.id)).toEqual(['1'])
        expect(filtrarFeed(lista, 'bug', 'caio').map((a) => a.id)).toEqual(['3'])
        expect(filtrarFeed(lista, 'todos', 'la-am').map((a) => a.id)).toEqual(['2'])
    })
})

describe('filtros e mock', () => {
    it('sem dados: nenhum filtro; com o mock: servidor, categoria, subcategoria e status (um valor cada)', () => {
        expect(ticketsFilters({ meta })).toEqual([])
        const f = ticketsFilters(ticketsFor('NG'))
        expect(f.map((x) => x.key)).toEqual([
            'ticket_servidor',
            'ticket_categoria',
            'ticket_subcategoria',
            'ticket_status',
        ])
        expect(f.every((x) => x.single)).toBe(true)
        expect(f[0].options.map((o) => o.value)).toEqual(['NG', 'LA-AM', 'LA-RJ'])
        expect(ticketsFor('LA_AM').stats).toBeUndefined()
    })
})
