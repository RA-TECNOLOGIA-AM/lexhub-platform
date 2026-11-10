import type { Me, Org, Unit, User } from '../../types/index.ts'

// Quem aparece logado no mock (qualquer usuário de teste vira este).
const user: User = {
    name: 'Luís Tápia',
    initials: 'LT',
    role_label: 'Dev · RA',
    can_export: true,
    can_see_commission: true,
    platform_staff: true,
}

// As organizações de que essa pessoa faz parte (as mesmas do protótipo).
export const orgs: Org[] = [
    { slug: 'lexgroup', name: 'LexGroup', sub: 'Plano Pro · 3 unidades' },
    { slug: 'cliente-parceiro', name: 'Cliente parceiro', sub: 'Implantação · 1 unidade' },
]

// Unidades que a pessoa enxerga em cada organização.
const UNITS: Record<string, Unit[]> = {
    lexgroup: [
        { code: 'NG', name: 'Nicolas Gomes' },
        { code: 'LA_AM', name: 'Luis Albert AM' },
        { code: 'LA_RJ', name: 'Luis Albert RJ' },
    ],
    'cliente-parceiro': [{ code: 'CP', name: 'Parceiro · sede' }],
}

// O "me" de uma organização; null = a pessoa não faz parte dela (a API responde 403).
export function meFor(slug: string): Me | null {
    const org = orgs.find((o) => o.slug === slug)
    return org ? { user, org, units: UNITS[slug] ?? [], orgs } : null
}

// A organização padrão (a primeira): para onde o login leva e quem tem os dados completos do mock.
export const me: Me = meFor(orgs[0].slug)!

// Usuários de teste do mock (só existem aqui, no navegador).
// No Supabase, cada um vira um usuário de verdade em Authentication > Users.
export const testUsers = [{ email: 'controller@lexgroup.com.br', password: 'lexhub123' }]
