import type { AccessCell, Permission, PermissionRole } from '../../../types/index.ts'

// A matriz "Papéis": o que cada papel pode fazer além de ver dashboards. É igual em toda organização,
// então fica no front (era o mock da API). Controller = Gestor (mesmas permissões no banco).
export const PERMISSION_ROLES: PermissionRole[] = ['owner', 'admin', 'gestor', 'controller', 'colaborador', 'leitor']

const Y: AccessCell = { kind: 'yes' }
const N: AccessCell = { kind: 'no' }
const T = (note: string): AccessCell => ({ kind: 'partial', note })

// Uma linha: as células na ordem de PERMISSION_ROLES.
function row(key: string, label: string, cells: AccessCell[]): Permission {
    return {
        key,
        label,
        cells: Object.fromEntries(PERMISSION_ROLES.map((r, i) => [r, cells[i]])) as Record<PermissionRole, AccessCell>,
    }
}

export const PERMISSIONS: Permission[] = [
    row('view', 'Ver dashboards liberados', [Y, Y, Y, Y, Y, Y]),
    // Regra de 09/11: colaborador exporta só o próprio setor; Leitor não exporta.
    row('export', 'Exportar e gerar PDF', [Y, Y, Y, Y, T('Do próprio setor'), N]),
    row('team_data', 'Ver dados de toda a equipe', [Y, Y, Y, Y, T('Só os seus'), T('Só resumos')]),
    row('members', 'Convidar e gerir membros', [Y, Y, T('Da unidade'), T('Da unidade'), N, N]),
    row('access', 'Mudar cargos e equipes', [Y, Y, T('Da unidade'), T('Da unidade'), N, N]),
    row('sources', 'Gerir fontes de dados', [Y, Y, N, N, N, N]),
    row('finance', 'Financeiro e despesas', [Y, Y, T('Se liberado'), T('Se liberado'), N, N]),
    row('billing', 'Plano e cobrança', [Y, T('Só ver'), N, N, N, N]),
]
