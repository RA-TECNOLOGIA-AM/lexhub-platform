import { describe, expect, it } from 'vitest'
import { diaCurto, diaLongo, mesBarra, mesNome, periodo } from './datas.ts'

describe('datas', () => {
    it('dia curto e longo', () => {
        expect(diaCurto('2026-11-03')).toBe('03/11')
        expect(diaLongo('2026-11-03')).toBe('03/11/2026')
        expect(diaLongo(undefined)).toBe('')
    })

    it('período: ano só no fim quando é o mesmo', () => {
        expect(periodo('2026-11-04', '2026-11-13')).toBe('04/11 a 13/11/2026')
        expect(periodo('2025-12-20', '2026-01-10')).toBe('20/12/2025 a 10/01/2026')
        expect(periodo('', '')).toBe('Período selecionado')
    })

    it('mês da barra e nome do mês', () => {
        expect(mesBarra('nov 2026')).toBe('Nov / 2026')
        expect(mesBarra('2026-09')).toBe('Set / 2026')
        expect(mesNome(3)).toBe('Abril')
    })
})
