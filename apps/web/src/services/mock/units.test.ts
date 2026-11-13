import { describe, expect, it } from 'vitest'
import type { SourcesResponse } from '../../types/index.ts'
import { DataError } from '../errors.ts'
import { createUnitIn, updateUnitIn } from './units.ts'

const fresh = (): SourcesResponse => ({
    syncEveryMin: 10,
    unitLimit: { used: 1, total: 5 },
    canManageUnits: true,
    units: [
        {
            unit: { code: 'NG', name: 'Nicolas Gomes' },
            timezone: 'America/Manaus',
            dashboards: 3,
            lastFailure: null,
            sources: [],
        },
    ],
})

describe('unidades no mock', () => {
    it('cria sem fontes, em ordem de nome, e conta no limite do plano', () => {
        const data = fresh()
        const u = createUnitIn(data, { code: 'LASP', name: ' Luis Albert SP ', timezone: 'America/Sao_Paulo' })
        expect(u).toMatchObject({ unit: { code: 'LASP', name: 'Luis Albert SP' }, sources: [], dashboards: 0 })
        expect(data.units.map((x) => x.unit.code)).toEqual(['LASP', 'NG'])
        expect(data.unitLimit).toEqual({ used: 2, total: 5 })
    })

    it('código repetido vira 409 com a mensagem do banco', () => {
        const error = (() => {
            try {
                createUnitIn(fresh(), { code: 'NG', name: 'Outra', timezone: 'America/Manaus' })
            } catch (e) {
                return e
            }
        })()
        expect(error).toBeInstanceOf(DataError)
        expect((error as DataError).status).toBe(409)
        expect((error as DataError).message).toBe('Já existe uma unidade com o código NG.')
    })

    it('edita nome e fuso, nunca o código', () => {
        const data = fresh()
        const u = updateUnitIn(data, { code: 'NG', name: 'NG Manaus', timezone: 'America/Sao_Paulo' })
        expect(u).toMatchObject({ unit: { code: 'NG', name: 'NG Manaus' }, timezone: 'America/Sao_Paulo' })
        expect(() => updateUnitIn(data, { code: 'XX', name: 'X', timezone: 'America/Manaus' })).toThrow(
            'Unidade não encontrada.',
        )
    })
})
