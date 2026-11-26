import { describe, expect, it } from 'vitest'
import { addDays, addMonths, formatBr, monthGrid, rangeRole } from './calendar.ts'

describe('calendar', () => {
    it('formata no padrão brasileiro', () => {
        expect(formatBr('2026-11-26')).toBe('26/11/2026')
        expect(formatBr('')).toBe('')
    })

    it('soma dias e meses virando mês/ano', () => {
        expect(addDays('2026-11-30', 1)).toBe('2026-12-01')
        expect(addDays('2026-01-01', -1)).toBe('2025-12-31')
        expect(addMonths('2026-01-31', 1)).toBe('2026-02-28')
        expect(addMonths('2026-12-15', 1)).toBe('2027-01-15')
    })

    it('grade de 6 semanas começando no domingo', () => {
        const grid = monthGrid(2026, 10) // nov/2026 começa num domingo
        expect(grid).toHaveLength(42)
        expect(grid[0]).toEqual({ iso: '2026-11-01', day: 1, inMonth: true })
        expect(grid[29].iso).toBe('2026-11-30')
        expect(grid[30]).toEqual({ iso: '2026-12-01', day: 1, inMonth: false })
        expect(monthGrid(2026, 11)[0]).toEqual({ iso: '2026-11-29', day: 29, inMonth: false })
    })

    it('papel do dia no intervalo', () => {
        expect(rangeRole('2026-11-01', '2026-11-01', '2026-11-26')).toBe('start')
        expect(rangeRole('2026-11-10', '2026-11-01', '2026-11-26')).toBe('inside')
        expect(rangeRole('2026-11-26', '2026-11-01', '2026-11-26')).toBe('end')
        expect(rangeRole('2026-11-27', '2026-11-01', '2026-11-26')).toBeNull()
        expect(rangeRole('2026-11-05', '2026-11-05', '2026-11-05')).toBe('single')
    })
})
