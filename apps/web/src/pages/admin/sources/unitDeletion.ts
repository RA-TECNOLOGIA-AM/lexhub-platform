import type { DeleteImpact } from '../../../components/ui/ConfirmDeleteDialog.tsx'
import type { UnitDeletionImpact } from '../../../types/index.ts'

const plural = (n: number, one: string, many: string) => `${n} ${n === 1 ? one : many}`

// Módulo: o impacto de excluir uma unidade (api.unit_deletion_impact) em texto para o modal de confirmação.
export function unitDeletionView(i: UnitDeletionImpact): DeleteImpact {
    if (i.locked) {
        return {
            items: [],
            blocked: `${i.name} não pode ser excluída: é uma unidade travada da plataforma. Só o Desenvolvedor libera, por migration.`,
        }
    }
    if (i.lastUnit) {
        return { items: [], blocked: `${i.name} é a única unidade da organização: crie outra antes de excluir esta.` }
    }
    return {
        items: [
            i.sources === 0
                ? 'Nenhuma fonte ligada'
                : `${plural(i.sources, 'fonte deixa', 'fontes deixam')} de alimentar a unidade (as próprias dela são desconectadas e as senhas apagadas na hora)`,
            `${plural(i.dashboards, 'dashboard deixa', 'dashboards deixam')} de aparecer`,
            i.members === 0
                ? 'Nenhum membro ligado'
                : `${plural(i.members, 'membro perde', 'membros perdem')} o vínculo com a unidade (continuam na organização)`,
        ],
        blocked: null,
        note: 'A unidade fica arquivada por 30 dias e depois é apagada de vez. Nesse prazo, só o suporte traz de volta, sem as fontes.',
    }
}
