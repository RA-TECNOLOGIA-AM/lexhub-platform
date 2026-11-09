import type { AccessCell, AccessResponse, Permission, RoleKey } from '../../types/index.ts'

// Atalhos para escrever a matriz como no protótipo: Y = sim, N = não, T('...') = em parte.
const Y: AccessCell = { kind: 'yes' }
const N: AccessCell = { kind: 'no' }
const T = (note: string): AccessCell => ({ kind: 'partial', note })

// Uma linha da matriz: as células na ordem owner, admin, gestor, colaborador, leitor.
function row(
    key: string,
    label: string,
    cells: [AccessCell, AccessCell, AccessCell, AccessCell, AccessCell],
): Permission {
    const roles: RoleKey[] = ['owner', 'admin', 'gestor', 'colaborador', 'leitor']
    return { key, label, cells: Object.fromEntries(roles.map((r, i) => [r, cells[i]])) as Record<RoleKey, AccessCell> }
}

// Os papéis e as regras do protótipo (canvas "LexHub v2 — protótipo", tela Acesso).
export const access: AccessResponse = {
    matrix: [
        row('view', 'Ver dashboards liberados', [Y, Y, Y, Y, Y]),
        row('export', 'Exportar e gerar PDF', [Y, Y, Y, N, N]),
        row('team_data', 'Ver dados de toda a equipe', [Y, Y, Y, T('Só os seus'), T('Só resumos')]),
        row('members', 'Convidar e gerir membros', [Y, Y, T('Da unidade'), N, N]),
        row('sources', 'Gerir fontes de dados', [Y, Y, N, N, N]),
        row('finance', 'Financeiro e despesas', [Y, Y, T('Se liberado'), N, N]),
        row('billing', 'Plano e cobrança', [Y, T('Só ver'), N, N, N]),
    ],
    rules: [
        {
            team: 'Protocolo',
            people: 12,
            dashboards: ['Protocolo', 'Pendências', 'Peticionamento', 'Pré-protocolo'],
            all: false,
            scope: null,
        },
        {
            team: 'Comercial',
            people: 9,
            dashboards: ['Funil comercial', 'Comissão', 'NPS', 'Marketing'],
            all: false,
            scope: 'Colaborador vê só os próprios atendimentos, pelo vínculo exato com o atendente.',
        },
        { team: 'Execução', people: 7, dashboards: ['Execução', 'Acordos', 'Recursal'], all: false, scope: null },
        { team: 'Diretoria', people: 4, dashboards: [], all: true, scope: null },
    ],
}
