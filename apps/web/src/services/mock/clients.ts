import type { ClientsResponse } from '../../types/index.ts'

// Os clientes do protótipo (canvas "LexHub v2 — protótipo", tela Clientes).
export const clients: ClientsResponse = {
    monthlyRevenue: null,
    closed: [],
    clients: [
        {
            slug: 'lexgroup',
            name: 'LexGroup',
            sub: '3 unidades · cliente desde a v1',
            plan: 'pro',
            seats: { used: 42, total: null }, // Pro sem teto (a LexGroup é a dona da plataforma)
            failingSources: 1,
            billing: 'ok',
            units: [
                { code: 'LA_AM', name: 'Luis Albert AM' },
                { code: 'LA_RJ', name: 'Luis Albert RJ' },
                { code: 'NG', name: 'Nicolas Gomes' },
            ],
            canClose: false, // a dona da plataforma
        },
        {
            slug: 'cliente-parceiro',
            name: 'Cliente parceiro',
            sub: '1 unidade · implantação acompanhada',
            plan: 'onboarding',
            seats: { used: 6, total: 10 },
            failingSources: 0,
            billing: 'onboarding_paid',
            units: [{ code: 'CP', name: 'Parceiro · sede' }],
            canClose: true,
        },
        {
            slug: 'escritorio',
            name: '[ESCRITÓRIO]',
            sub: '2 unidades · entrou em setembro',
            plan: 'starter',
            seats: { used: 9, total: 10 },
            failingSources: 0,
            billing: 'overdue',
            units: [
                { code: 'E1', name: 'Matriz' },
                { code: 'E2', name: 'Filial' },
            ],
            canClose: true,
        },
    ],
}
