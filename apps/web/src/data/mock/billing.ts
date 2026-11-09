import type { BillingResponse, Plan } from '../types.ts'

// Os planos do protótipo. Preços em descoberta com escritórios: null até serem definidos.
export const plans: Plan[] = [
    {
        key: 'starter',
        name: 'Starter',
        monthlyPrice: null,
        custom: false,
        tagline: 'Um escritório começando a medir a operação',
        features: [
            '1 unidade e 10 assentos',
            '3 fontes de dados',
            'Catálogo essencial de dashboards',
            '12 meses de histórico',
        ],
    },
    {
        key: 'pro',
        name: 'Pro',
        monthlyPrice: null,
        custom: false,
        tagline: 'Grupos com várias unidades e equipes',
        features: [
            'Até 5 unidades e 60 assentos',
            '15 fontes de dados',
            'Catálogo completo e consolidados',
            '24 meses de histórico',
        ],
    },
    {
        key: 'enterprise',
        name: 'Enterprise',
        monthlyPrice: null,
        custom: true,
        tagline: 'Redes de escritórios e departamentos jurídicos',
        features: [
            'Unidades e assentos sob medida',
            'Login corporativo (SSO)',
            'Papéis personalizados',
            'SLA e implantação dedicada',
        ],
    },
]

// Módulo: a cobrança da organização no mock.
// Parâmetro: os assentos (vêm de Membros, para as duas telas mostrarem o mesmo número).
export function billingFor(seats: { used: number; total: number }): BillingResponse {
    return {
        current: {
            plan: 'pro',
            status: 'active',
            renewsOn: '2026-12-01',
            paymentMethods: ['boleto', 'PIX'],
            gateway: null,
        },
        usage: [
            { key: 'seats', label: 'Assentos', ...seats },
            { key: 'units', label: 'Unidades', used: 3, total: 5 },
            { key: 'sources', label: 'Fontes de dados', used: 12, total: 15 },
            { key: 'history', label: 'Histórico', used: 24, total: 24, unit: 'meses' },
        ],
        plans: structuredClone(plans),
        invoices: [
            { id: 'inv-2026-10', month: '2026-10', amount: null, status: 'paid', nfse: 'issued' },
            { id: 'inv-2026-09', month: '2026-09', amount: null, status: 'paid', nfse: 'issued' },
            { id: 'inv-2026-08', month: '2026-08', amount: null, status: 'paid', nfse: 'issued' },
        ],
    }
}
