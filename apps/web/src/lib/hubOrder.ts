// Módulo: as regras de ordem do hub, sem React (testadas em hubOrder.test.ts).
// A ordem salva é UMA lista de keys para o hub inteiro; cada seção ordena os seus cards por ela.

// As abas (seções) do hub, nesta ordem, logo abaixo de Favoritos. Aparecem mesmo sem dashboard
// (as análises ainda vão ser migradas). Área fora da lista vai para o fim, na ordem do catálogo.
export const HUB_AREAS = ['Comercial', 'Pré-protocolo', 'Tecnologia', 'Jurídico', 'Financeiro', 'Estratégico']

// ['Estratégico', 'Outros', 'Comercial'] -> ['Comercial', 'Estratégico', 'Outros']
export function sortAreas(areas: string[], order: string[] = HUB_AREAS): string[] {
    const rank = (area: string) => {
        const i = order.indexOf(area)
        return i === -1 ? order.length : i
    }
    return [...areas].sort((a, b) => rank(a) - rank(b)) // o sort é estável: empate mantém a ordem do catálogo
}

// Ordena pela lista salva. Quem não está nela (dashboard novo) vai para o fim, na ordem em que veio.
export function sortByOrder<T extends { key: string }>(items: T[], order: string[]): T[] {
    const saved = new Map(order.map((key, i) => [key, i]))
    return items
        .map((item, i) => ({ item, rank: saved.get(item.key) ?? order.length + i }))
        .sort((a, b) => a.rank - b.rank)
        .map((x) => x.item)
}

// Tira `active` do lugar e põe na posição de `over` (como no arraste). Key desconhecida: lista igual.
export function moveKey(keys: string[], active: string, over: string): string[] {
    const from = keys.indexOf(active)
    const to = keys.indexOf(over)
    if (from === -1 || to === -1 || from === to) return keys
    const next = [...keys]
    next.splice(from, 1)
    next.splice(to, 0, active)
    return next
}
