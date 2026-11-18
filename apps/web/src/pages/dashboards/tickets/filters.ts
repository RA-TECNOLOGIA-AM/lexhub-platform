import type { FilterField } from '../../../lib/filters.ts'
import { SERVIDORES, lerTickets, type TicketsResponse } from './tickets.ts'

const lista = (xs: string[]) => [...new Set(xs.filter(Boolean))].map((v) => ({ value: v, label: v }))

// Os filtros da página da v1 (clicando nos gráficos): servidor, categoria, subcategoria e status, um valor de
// cada (a v1 mandava um par selection_dim/selection_value por dimensão). `current` mantém o escolhido na lista.
export function ticketsFilters(data: TicketsResponse): FilterField[] {
    const t = lerTickets(data)
    if (!t.temDados) return []
    return [
        {
            key: 'ticket_servidor',
            label: 'Servidor',
            options: lista([
                ...SERVIDORES,
                ...t.abertosPorServidor.map((p) => p.name),
                ...t.encerradosPorServidor.map((p) => p.name),
            ]),
            single: true,
        },
        {
            key: 'ticket_categoria',
            label: 'Categoria',
            options: lista(t.porCategoria.map((p) => p.name)),
            single: true,
        },
        {
            key: 'ticket_subcategoria',
            label: 'Subcategoria',
            options: lista(t.subcategorias.map((p) => p.name)),
            single: true,
        },
        { key: 'ticket_status', label: 'Status', options: lista(t.porStatus.map((p) => p.name)), single: true },
    ]
}
