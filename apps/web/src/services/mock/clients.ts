import type { ClientsResponse } from '../../types/index.ts'

// Os clientes do protótipo (canvas "LexHub v2 — protótipo", tela Clientes).
export const clients: ClientsResponse = {
    monthlyRevenue: null,
    clients: [
        {
            slug: 'lexgroup',
            name: 'LexGroup',
            sub: '3 unidades · cliente desde a v1',
            plan: 'pro',
            seats: { used: 42, total: 60 },
            failingSources: 1,
            billing: 'ok',
        },
        {
            slug: 'cliente-parceiro',
            name: 'Cliente parceiro',
            sub: '1 unidade · implantação acompanhada',
            plan: 'onboarding',
            seats: { used: 6, total: 10 },
            failingSources: 0,
            billing: 'onboarding_paid',
        },
        {
            slug: 'escritorio',
            name: '[ESCRITÓRIO]',
            sub: '2 unidades · entrou em setembro',
            plan: 'starter',
            seats: { used: 9, total: 10 },
            failingSources: 0,
            billing: 'overdue',
        },
    ],
}
