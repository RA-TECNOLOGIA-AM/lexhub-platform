import type { Me } from '../types.ts'

// Quem aparece logado no mock (qualquer usuário de teste vira este).
export const me: Me = {
    user: { name: 'Luís Tápia', initials: 'LT', roleLabel: 'Controller · NG', canExport: true, canSeeCommission: true },
    org: { slug: 'lexgroup', name: 'LexGroup', sub: 'Piloto V2 · 1 unidade' },
    units: [
        { code: 'NG', name: 'Nicolas Gomes' },
        { code: 'LA_AM', name: 'Luis Albert AM' },
        { code: 'LA_RJ', name: 'Luis Albert RJ' },
    ],
}

// Usuários de teste do mock (só existem aqui, no navegador).
// No Supabase, cada um vira um usuário de verdade em Authentication > Users.
export const testUsers = [{ email: 'controller@lexgroup.com.br', password: 'lexhub123' }]