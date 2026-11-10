// Módulo: as regras de ordem do hub, sem React (testadas em hubOrder.test.ts).
// A ordem salva é UMA lista de keys para o hub inteiro; cada seção ordena os seus cards por ela.

// Áreas que sobem para logo abaixo de Favoritos, nesta ordem. As outras seguem a ordem do catálogo.
export const AREA_PRIORITY = ['Gestão']

// ['Comercial', 'Gestão', 'Operação jurídica'] -> ['Gestão', 'Comercial', 'Operação jurídica']
export function sortAreas(areas: string[], priority: string[] = AREA_PRIORITY): string[] {
    const rank = (area: string) => {
        const i = priority.indexOf(area)
        return i === -1 ? priority.length : i
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
