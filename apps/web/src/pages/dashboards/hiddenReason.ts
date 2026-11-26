import type { HiddenReason } from '../../types/index.ts'

// O motivo em português (vem de app_private.dashboard_access_explain, a mesma regra do acesso de verdade).
export const HIDDEN_REASON: Record<HiddenReason, string> = {
    no_unit_role: 'Sem cargo nesta unidade',
    no_sector_rule: 'Os setores dele não têm este dashboard e não há exceção',
    dashboard_off: 'Desligado nesta unidade',
    not_member: 'Não é membro ativo',
    org_inactive: 'Unidade ou organização inativa',
    owner_dev_only: 'Só Owner e Desenvolvedor veem este dashboard',
}
