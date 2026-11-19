import type { HubGroup } from '../../types/index.ts'

// As colunas do hub como em app.hub_groups (slug fixo; name é o rótulo, igual a dashboard_catalog.area).
export const HUB_GROUPS: HubGroup[] = [
    { slug: 'comercial', name: 'Comercial' },
    { slug: 'pre_protocolo', name: 'Pré-protocolo' },
    { slug: 'tecnologia', name: 'Tecnologia' },
    { slug: 'juridico', name: 'Jurídico' },
    { slug: 'financeiro', name: 'Financeiro' },
    { slug: 'estrategico', name: 'Estratégico' },
]

// Como o gatilho do banco: o grupo de um card sai da área dele.
export function groupOfArea(area: string): string {
    return HUB_GROUPS.find((g) => g.name === area)?.slug ?? ''
}
