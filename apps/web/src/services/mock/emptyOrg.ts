import type {
    AccessResponse,
    AuditResponse,
    BillingResponse,
    DashboardCatalog,
    Member,
    MembersResponse,
    SourcesResponse,
} from '../../types/index.ts'
import { access } from './access.ts'
import { plans } from './billing.ts'

// Organização em implantação (Cliente parceiro): ainda sem dashboards, regras ou eventos.
// Serve para as telas mostrarem os estados vazios, e não os dados da LexGroup por engano.

export const emptyCatalog: DashboardCatalog = { available: [], upcoming: [] }

// Só quem está logado faz parte, como admin.
export function onboardingMembers(email: string, name: string): MembersResponse {
    const self: Member = {
        id: 'self',
        name,
        email,
        role: 'admin',
        units: ['*'],
        team: null,
        status: 'active',
        note: null,
        security: 'MFA ativo',
    }
    return { seats: { used: 1, total: 10 }, teams: [], members: [self] }
}

// O papel diz o que cada um pode fazer (igual em toda organização); as regras por equipe ainda não existem.
export const onboardingAccess: AccessResponse = { matrix: access.matrix, rules: [] }

export const onboardingAudit: AuditResponse = { events: [] }

// Ainda sem fontes conectadas: só a unidade-sede, vazia.
export const onboardingSources: SourcesResponse = {
    syncEveryMin: 5,
    unitLimit: { used: 1, total: 1 },
    units: [
        {
            unit: { code: 'CP', name: 'Parceiro · sede' },
            timezone: 'America/Manaus',
            dashboards: 0,
            lastFailure: null,
            sources: [],
        },
    ],
}

export const onboardingBilling: BillingResponse = {
    current: {
        plan: 'onboarding',
        status: 'active',
        renewsOn: '2026-12-01',
        paymentMethods: ['boleto', 'PIX'],
        gateway: null,
    },
    usage: [
        { key: 'seats', label: 'Assentos', used: 1, total: 10 },
        { key: 'units', label: 'Unidades', used: 1, total: 1 },
        { key: 'sources', label: 'Fontes de dados', used: 0, total: 3 },
        { key: 'history', label: 'Histórico', used: 0, total: 12, unit: 'meses' },
    ],
    plans: structuredClone(plans),
    invoices: [],
}
