import type { ApprovalTarget, UnitRoleKey } from '../../../types/index.ts'

// Módulo: as regras do painel "Aprovar pedido", sem React (testadas em approveView.test.ts).
// Mesmos limites do banco (app.organizations.slug, app.units.code).

export type ApproveForm = {
    mode: 'existing' | 'new'
    // organização existente
    orgId: string
    orgRole: 'admin' | 'member'
    unitRoles: Record<string, UnitRoleKey | ''> // unidade -> cargo ('' = fora dessa unidade)
    // organização nova
    newName: string
    newSlug: string
    newRole: 'owner' | 'admin'
    unitCode: string
    unitName: string
    timezone: string
}

export const UNIT_ROLES: { key: UnitRoleKey; label: string }[] = [
    { key: 'gestor', label: 'Gestor' },
    { key: 'controller', label: 'Controller' },
    { key: 'colaborador', label: 'Colaborador' },
    { key: 'leitor', label: 'Leitor' },
]

export const ORG_ROLE_LABEL = {
    owner: 'Proprietário',
    admin: 'Desenvolvedor (todas as unidades)',
    member: 'Membro (cargo por unidade)',
} as const

export const emptyForm = (orgId = ''): ApproveForm => ({
    mode: 'existing',
    orgId,
    orgRole: 'member',
    unitRoles: {},
    newName: '',
    newSlug: '',
    newRole: 'owner',
    unitCode: '',
    unitName: '',
    timezone: 'America/Manaus',
})

// "Escritório São João & Filhos" -> "escritorio-sao-joao-filhos" (sugestão de slug a partir do nome).
export function slugify(name: string): string {
    return name
        .normalize('NFD')
        .replace(/[̀-ͯ]/g, '')
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-+|-+$/g, '')
        .slice(0, 63)
        .replace(/-+$/g, '')
}

const SLUG = /^[a-z0-9][a-z0-9-]{1,62}$/
const UNIT_CODE = /^[A-Z0-9_]{2,16}$/

// Valida o formulário e monta o destino da aprovação. Devolve { error } ou { target }.
export function buildTarget(form: ApproveForm): { error: string } | { target: ApprovalTarget } {
    if (form.mode === 'existing') {
        if (!form.orgId) return { error: 'Escolha a organização.' }
        const units = Object.entries(form.unitRoles)
            .filter(([, role]) => role !== '')
            .map(([unit_id, role]) => ({ unit_id, role_key: role as UnitRoleKey }))
        if (form.orgRole === 'member' && units.length === 0) {
            return { error: 'Escolha pelo menos uma unidade e o cargo nela.' }
        }
        return {
            target: {
                kind: 'existing',
                org_id: form.orgId,
                org_role: form.orgRole,
                units: form.orgRole === 'admin' ? [] : units,
            },
        }
    }

    const name = form.newName.trim()
    const slug = form.newSlug.trim().toLowerCase()
    const code = form.unitCode.trim().toUpperCase()
    const unitName = form.unitName.trim()
    if (!name) return { error: 'Informe o nome da organização.' }
    if (!SLUG.test(slug)) return { error: 'Endereço inválido: letras minúsculas, números e hífen (2 a 63).' }
    if (!UNIT_CODE.test(code)) return { error: 'Código da unidade: letras maiúsculas, números ou _ (2 a 16).' }
    if (!unitName) return { error: 'Informe o nome da primeira unidade.' }
    return {
        target: {
            kind: 'new',
            name,
            slug,
            org_role: form.newRole,
            unit: { code, name: unitName, timezone: form.timezone.trim() || 'America/Manaus' },
        },
    }
}
