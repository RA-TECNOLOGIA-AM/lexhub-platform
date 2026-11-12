import type { Unit } from '../types/index.ts'

// Módulo: a unidade escolhida no seletor da barra lateral, sem React (testado em activeUnit.test.ts).
// null = "Todas as unidades". Fica lembrada na sessão (por organização): voltar ao hub mantém a escolha.

const key = (org: string) => `lexhub.unit.${org}`

// O que ficou lembrado para a organização. Sem storage (ex.: aba privada bloqueada) = nada lembrado.
export function rememberedUnit(org: string, storage: Pick<Storage, 'getItem'> | null = safeSession()): string | null {
    try {
        return storage?.getItem(key(org)) || null
    } catch {
        return null
    }
}

export function rememberUnit(
    org: string,
    unit: string | null,
    storage: Pick<Storage, 'setItem' | 'removeItem'> | null = safeSession(),
): void {
    try {
        if (unit) storage?.setItem(key(org), unit)
        else storage?.removeItem(key(org))
    } catch {
        // sem storage: a escolha vale só enquanto a página estiver aberta (pela URL)
    }
}

function safeSession(): Storage | null {
    try {
        return window.sessionStorage
    } catch {
        return null
    }
}

// A unidade do hub: a da URL (?unidade=) manda; sem ela, a lembrada; só vale se a pessoa vê essa unidade.
// Quem vê uma unidade só fica sempre nela (não existe "Todas" para essa pessoa).
export function hubUnit(fromUrl: string | null, remembered: string | null, units: Unit[]): string | null {
    if (units.length === 1) return units[0].code
    const candidate = fromUrl ?? remembered
    return candidate && units.some((u) => u.code === candidate) ? candidate : null
}

// As unidades que entram no seletor: só as que têm algum dashboard liberado para a pessoa
// (ex.: "Escritório Master", sem dashboards, some). Sem o catálogo ainda (carregando): todas.
export function unitsWithDashboards(units: Unit[], dashboards: { units: string[] }[] | null): Unit[] {
    if (!dashboards) return units
    const used = new Set(dashboards.flatMap((d) => d.units))
    return units.filter((u) => used.has(u.code))
}

export type UnitChoice = { code: string | null; label: string } // code null = "Todas as unidades"

// As opções do seletor. Num dashboard: só as unidades em que ele está liberado, sem "Todas"
// (os dados são sempre de uma unidade). No resto do app: "Todas" (se vê mais de uma) + cada unidade.
export function unitChoices(units: Unit[], dashboardUnits: string[] | null): UnitChoice[] {
    if (dashboardUnits) {
        return units.filter((u) => dashboardUnits.includes(u.code)).map((u) => ({ code: u.code, label: u.name }))
    }
    const each = units.map((u) => ({ code: u.code, label: u.name }))
    return units.length > 1 ? [{ code: null, label: 'Todas as unidades' }, ...each] : each
}
