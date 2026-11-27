import { describe, expect, it } from 'vitest'
import { hubUnit, rememberUnit, rememberedUnit, sourcesUnit, unitChoices, unitsWithDashboards } from './activeUnit.ts'

const units = [
    { code: 'NG', name: 'Nicolas Gomes' },
    { code: 'LA', name: 'LAAM' },
]

// sessionStorage falso
function fakeStorage() {
    const data = new Map<string, string>()
    return {
        getItem: (k: string) => data.get(k) ?? null,
        setItem: (k: string, v: string) => void data.set(k, v),
        removeItem: (k: string) => void data.delete(k),
    }
}

describe('rememberUnit / rememberedUnit', () => {
    it('lembra por organização e "Todas" apaga', () => {
        const s = fakeStorage()
        rememberUnit('lexgroup', 'LA', s)
        expect(rememberedUnit('lexgroup', s)).toBe('LA')
        expect(rememberedUnit('outra', s)).toBeNull()
        rememberUnit('lexgroup', null, s)
        expect(rememberedUnit('lexgroup', s)).toBeNull()
    })

    it('storage que dá erro não quebra a tela', () => {
        const broken = {
            getItem: () => {
                throw new Error('bloqueado')
            },
        }
        expect(rememberedUnit('lexgroup', broken)).toBeNull()
    })
})

describe('hubUnit', () => {
    it('URL manda; sem URL, a lembrada; unidade que a pessoa não vê é ignorada', () => {
        expect(hubUnit('NG', 'LA', units)).toBe('NG')
        expect(hubUnit(null, 'LA', units)).toBe('LA')
        expect(hubUnit(null, null, units)).toBeNull()
        expect(hubUnit('RJ', null, units)).toBeNull()
    })

    it('uma unidade só: sempre ela', () => {
        expect(hubUnit(null, null, [units[1]])).toBe('LA')
    })
})

describe('unitsWithDashboards', () => {
    it('unidade sem dashboard some do seletor; sem catálogo, mostra todas', () => {
        const withMaster = [...units, { code: 'MT', name: 'ESCRITÓRIO MASTER' }]
        expect(
            unitsWithDashboards(withMaster, [{ units: ['NG'] }, { units: ['LA', 'NG'] }]).map((u) => u.code),
        ).toEqual(['NG', 'LA'])
        expect(unitsWithDashboards(withMaster, null)).toHaveLength(3)
    })
})

describe('unitChoices', () => {
    it('fora do dashboard: "Todas" + cada unidade', () => {
        expect(unitChoices(units, null).map((c) => c.code)).toEqual([null, 'NG', 'LA'])
    })

    it('uma unidade só: sem "Todas"', () => {
        expect(unitChoices([units[0]], null)).toEqual([{ code: 'NG', label: 'Nicolas Gomes' }])
    })

    it('no dashboard: só as unidades liberadas nele, sem "Todas"', () => {
        expect(unitChoices(units, ['LA', 'RJ'])).toEqual([{ code: 'LA', label: 'LAAM' }])
    })
})

describe('sourcesUnit', () => {
    const codes = ['NG', 'LA', 'EDT']

    it('a da URL manda', () => {
        expect(sourcesUnit('LA', 'NG', codes)).toBe('LA')
    })

    it('sem URL, a lembrada no seletor', () => {
        expect(sourcesUnit(null, 'EDT', codes)).toBe('EDT')
    })

    it('"Todas" lembrada ou código que a pessoa não vê: a primeira', () => {
        expect(sourcesUnit(null, null, codes)).toBe('NG')
        expect(sourcesUnit('XX', 'YY', codes)).toBe('NG')
    })

    it('sem unidades: nenhuma', () => {
        expect(sourcesUnit(null, null, [])).toBeNull()
    })
})
