import type { SourcesResponse, UnitDeletionImpact, UnitInput, UnitSources } from '../../types/index.ts'
import { DataError } from '../errors.ts'
import { validateUnit } from '../../pages/admin/sources/unitForm.ts'

// Criar e editar unidade no mock, com as mesmas regras de api.create_unit / api.update_unit
// (migration 20261113220000_nova_unidade.sql). Grava em `data` (a memória do mock, até o F5).

export function createUnitIn(data: SourcesResponse, input: UnitInput): UnitSources {
    const problem = validateUnit(
        input,
        'create',
        data.units.map((u) => u.unit.code),
    )
    if (problem) throw new DataError(409, problem)
    const unit: UnitSources = {
        unit: { code: input.code, name: input.name.trim() },
        timezone: input.timezone,
        dashboards: 0,
        lastFailure: null,
        sources: [],
    }
    data.units.push(unit)
    if (data.unitLimit) data.unitLimit = { ...data.unitLimit, used: data.unitLimit.used + 1 }
    data.units.sort((a, b) => a.unit.name.localeCompare(b.unit.name, 'pt-BR'))
    return unit
}

export function updateUnitIn(data: SourcesResponse, input: UnitInput): UnitSources {
    const unit = data.units.find((u) => u.unit.code === input.code)
    if (!unit) throw new DataError(409, 'Unidade não encontrada.')
    const problem = validateUnit(input, 'edit', [])
    if (problem) throw new DataError(409, problem)
    unit.unit = { ...unit.unit, name: input.name.trim() }
    unit.timezone = input.timezone
    return unit
}

// Excluir unidade no mock, com as travas de api.delete_unit (migration 20261123140000_excluir_unidade_organizacao.sql).
// locked: as unidades travadas da organização (na LexGroup: NG, LA e RJ).
export function unitImpactIn(data: SourcesResponse, code: string, locked: string[]): UnitDeletionImpact {
    const unit = data.units.find((u) => u.unit.code === code)
    if (!unit) throw new DataError(409, 'Unidade não encontrada.')
    return {
        code: unit.unit.code,
        name: unit.unit.name,
        sources: unit.sources.length,
        dashboards: unit.dashboards,
        members: 0, // o mock não liga membros a unidades
        locked: locked.includes(code),
        lastUnit: data.units.length === 1,
    }
}

export function deleteUnitIn(data: SourcesResponse, code: string, confirmName: string, locked: string[]): void {
    const impact = unitImpactIn(data, code, locked)
    if (impact.locked) throw new DataError(409, `A unidade ${impact.name} não pode ser excluída (trava da plataforma).`)
    if (impact.lastUnit) throw new DataError(409, 'A organização precisa de pelo menos uma unidade.')
    if (confirmName.trim().toLowerCase() !== impact.name.trim().toLowerCase()) {
        throw new DataError(409, 'Digite o nome da unidade para confirmar.')
    }
    const removed = data.units.find((u) => u.unit.code === code)!
    data.units = data.units.filter((u) => u.unit.code !== code)
    if (data.unitLimit) data.unitLimit = { ...data.unitLimit, used: data.unitLimit.used - 1 }
    const now = new Date()
    data.deletedUnits.unshift({
        code,
        name: impact.name,
        deletedAt: now.toISOString(),
        purgeAt: new Date(now.getTime() + 30 * DAY_MS).toISOString(),
        deletedBy: 'Você',
    })
    trash.set(code, { ...removed, sources: [], lastFailure: null }) // volta sem as fontes próprias
}

// O que a exclusão guardou para restaurar (no banco: a própria linha arquivada).
const trash = new Map<string, UnitSources>()
const DAY_MS = 24 * 60 * 60 * 1000

export function restoreUnitIn(data: SourcesResponse, code: string): UnitSources {
    const deleted = data.deletedUnits.find((u) => u.code === code)
    const unit = trash.get(code)
    if (!deleted || !unit) throw new DataError(409, 'Unidade excluída não encontrada.')
    data.deletedUnits = data.deletedUnits.filter((u) => u.code !== code)
    trash.delete(code)
    data.units.push(unit)
    data.units.sort((a, b) => a.unit.name.localeCompare(b.unit.name, 'pt-BR'))
    if (data.unitLimit) data.unitLimit = { ...data.unitLimit, used: data.unitLimit.used + 1 }
    return unit
}
