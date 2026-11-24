import type { Unit } from '../types/index.ts'

// Módulo: o nome de uma unidade para mostrar na tela.
// 'NG' -> 'Nicolas Gomes' (das unidades da pessoa). Unidade que não é física ('Consolidado') ou
// desconhecida mostra o próprio código, para nunca sumir da tela.
export const unitName = (code: string, units: Unit[]): string => units.find((u) => u.code === code)?.name ?? code

// Módulo: a logo de uma unidade (64x64 em /public, ~1-4 kB). Unidade sem logo -> null (a tela mostra
// só o nome). Os códigos variam entre fontes e o mock ('LA'/'LAAM'/'LA_AM', 'RJ'/'LARJ'/'LA_RJ').
const UNIT_LOGOS: Record<string, string> = {
    NG: '/logo_ng.webp',
    LA: '/logo_laam.webp',
    LAAM: '/logo_laam.webp',
    LA_AM: '/logo_laam.webp',
    RJ: '/logo_larj.webp',
    LARJ: '/logo_larj.webp',
    LA_RJ: '/logo_larj.webp',
}
export const unitLogo = (code: string | null): string | null => (code ? (UNIT_LOGOS[code] ?? null) : null)
