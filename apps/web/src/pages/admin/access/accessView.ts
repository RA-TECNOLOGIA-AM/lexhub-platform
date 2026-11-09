import type { Member, Permission, RoleKey, TeamRule, Unit } from '../../../types/index.ts'
import { ROLE_LABEL } from '../members/memberView.ts'

export const ROLE_ORDER: RoleKey[] = ['owner', 'admin', 'gestor', 'colaborador', 'leitor']

export type Simulation = {
    profile: string // "Colaborador · equipe Protocolo · Luis Albert RJ"
    summary: string // "Vê 4 dashboards em Luis Albert RJ e não pode exportar."
    dashboards: string[] // as tags que a pessoa vê
}

// O papel tem a permissão? ('yes' = sim; 'no' e 'partial' contam como não para a frase do simulador)
function allows(matrix: Permission[], key: string, role: RoleKey): boolean {
    return matrix.find((p) => p.key === key)?.cells[role].kind === 'yes'
}

// ['NG'] -> 'Nicolas Gomes' · ['*'] -> 'todas as unidades' · ['NG', 'LA_AM'] -> 'Nicolas Gomes e Luis Albert AM'
function unitNames(codes: string[], units: Unit[]): string {
    if (codes.includes('*')) return 'todas as unidades'
    return codes.map((c) => units.find((u) => u.code === c)?.name ?? c).join(' e ')
}

// "em Luis Albert RJ" · "em 2 unidades" · "em todas as unidades"
function where(codes: string[], units: Unit[]): string {
    if (codes.includes('*') || codes.length === 1) return `em ${unitNames(codes, units)}`
    return `em ${codes.length} unidades`
}

// Módulo: a regra de negócio do Acesso em uma função pura.
// Papel diz o que a pessoa pode fazer; equipe + unidades dizem o que ela vê. Sem equipe ou unidade, não vê nada.
export function simulateAccess(member: Member, rules: TeamRule[], matrix: Permission[], units: Unit[]): Simulation {
    const { role, team } = member
    const hasUnits = member.units.length > 0

    if (!role) {
        return {
            profile: 'Sem papel, equipe ou unidade',
            summary: 'Não vê nenhum dashboard até um admin aprovar o pedido e definir equipe e unidade.',
            dashboards: [],
        }
    }

    const profile = [
        ROLE_LABEL[role],
        team ? `equipe ${team}` : 'sem equipe',
        hasUnits ? unitNames(member.units, units) : 'sem unidade',
    ].join(' · ')
    if (!team || !hasUnits) {
        return { profile, summary: 'Não vê nenhum dashboard: precisa de equipe e unidade.', dashboards: [] }
    }

    const rule = rules.find((r) => r.team === team)
    if (!rule) {
        return { profile, summary: `Não vê nenhum dashboard: a equipe ${team} ainda não tem regra.`, dashboards: [] }
    }

    const count = rule.dashboards.length
    const what = rule.all ? 'Vê todos os dashboards' : `Vê ${count} ${count === 1 ? 'dashboard' : 'dashboards'}`
    const teamData = allows(matrix, 'team_data', role) ? ', com os dados de toda a equipe,' : ''
    const exports = allows(matrix, 'export', role) ? 'pode exportar' : 'não pode exportar'
    return {
        profile,
        summary: `${what} ${where(member.units, units)}${teamData} e ${exports}.`,
        dashboards: rule.all ? ['Todos os dashboards das suas unidades'] : rule.dashboards,
    }
}
