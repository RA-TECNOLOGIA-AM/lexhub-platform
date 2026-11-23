import type { DeleteImpact } from '../../../components/ui/ConfirmDeleteDialog.tsx'
import type { OrgClosureImpact } from '../../../types/index.ts'

const plural = (n: number, one: string, many: string) => `${n} ${n === 1 ? one : many}`

// Módulo: o impacto de encerrar uma organização (api.org_closure_impact) em texto para o modal de confirmação.
export function orgClosureView(i: OrgClosureImpact): DeleteImpact {
    if (i.locked) return { items: [], blocked: `${i.name} é a dona da plataforma e não pode ser encerrada.` }
    return {
        items: [
            `${plural(i.units, 'unidade some', 'unidades somem')} das telas`,
            `${plural(i.members, 'membro perde', 'membros perdem')} o acesso`,
            i.sources === 0
                ? 'Nenhuma fonte conectada'
                : `${plural(i.sources, 'fonte é desconectada', 'fontes são desconectadas')} e as senhas apagadas na hora`,
        ],
        blocked: null,
        note: 'A organização fica encerrada: o histórico da auditoria é guardado. Só o suporte reabre.',
    }
}
