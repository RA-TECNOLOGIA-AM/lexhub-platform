import type { DataClient } from '../../../services/client.ts'
import { DataError } from '../../../services/errors.ts'
import type { AccessMember, Member, RoleKey, UnitRoleKey } from '../../../types/index.ts'

// Do maior para o menor. Controller vira Gestor: a matriz do Acesso ainda não tem a coluna Controller.
const UNIT_ROLE_ORDER: UnitRoleKey[] = ['gestor', 'controller', 'colaborador', 'leitor']
const AS_ACCESS_ROLE: Record<UnitRoleKey, RoleKey> = {
    gestor: 'gestor',
    controller: 'gestor',
    colaborador: 'colaborador',
    leitor: 'leitor',
}

// Módulo: o membro da lista (cargo por unidade) no formato do simulador do Acesso (um papel só).
// Fica até a aba Acesso ganhar a edição de cargo por unidade.
export function accessMemberOf(m: Member): AccessMember {
    const base = { id: m.id, name: m.name, email: m.email, team: m.teams[0] ?? null }
    if (m.org_role === 'owner' || m.org_role === 'admin') return { ...base, role: m.org_role, units: ['*'] }
    const top = UNIT_ROLE_ORDER.find((r) => m.units.some((u) => u.role === r)) ?? 'leitor'
    return { ...base, role: AS_ACCESS_ROLE[top], units: m.units.map((u) => u.code) }
}

// Os membros do simulador. Quem não gere membros (403 de api.list_members) ainda abre o Acesso:
// o simulador só fica vazio. Outros erros sobem para a tela de erro.
export async function loadAccessMembers(client: Pick<DataClient, 'listMembers'>, org: string): Promise<AccessMember[]> {
    try {
        return (await client.listMembers(org)).members.map(accessMemberOf)
    } catch (err) {
        if (err instanceof DataError && err.status === 403) return []
        throw err
    }
}
