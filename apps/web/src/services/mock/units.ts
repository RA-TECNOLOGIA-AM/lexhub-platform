import type { SourcesResponse, UnitInput, UnitSources } from '../../types/index.ts'
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
