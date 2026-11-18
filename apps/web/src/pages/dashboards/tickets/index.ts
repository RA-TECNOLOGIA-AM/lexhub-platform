import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import { TicketsContent } from './TicketsContent.tsx'
import { ticketsFilters } from './filters.ts'
import type { TicketsResponse } from './tickets.ts'

// Tickets (banco NG, área Tecnologia): os tickets do Discord dos três servidores, como a página da v1.
export const tickets: DashboardModule<TicketsResponse> = {
    key: 'tickets',
    fetch: (query) => dataClient.getDashboardData<TicketsResponse>('tickets', query),
    Content: TicketsContent,
    filters: ticketsFilters,
}
