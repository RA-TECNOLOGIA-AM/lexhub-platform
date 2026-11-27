import { describe, expect, it } from 'vitest'
import { alertText, limitAlerts, seatAlert } from './planLimits.ts'
import type { PlanUsage } from '../types/index.ts'

const usage = (key: string, used: number, total: number | null): PlanUsage => ({ key, label: key, used, total })

describe('limitAlerts', () => {
    it('não avisa abaixo de 80% nem sem teto', () => {
        expect(limitAlerts([usage('seats', 47, 60), usage('units', 3, null)])).toEqual([])
    })

    it('avisa "near" de 80% até antes do teto e "full" no teto ou acima', () => {
        const alerts = limitAlerts([usage('seats', 48, 60), usage('units', 5, 5), usage('sources', 16, 15)])
        expect(alerts.map((a) => [a.key, a.level])).toEqual([
            ['sources', 'full'],
            ['units', 'full'],
            ['seats', 'near'],
        ])
    })

    it('ignora o histórico, que cheio é o normal', () => {
        expect(limitAlerts([usage('history', 24, 24)])).toEqual([])
    })

    it('ignora teto zero', () => {
        expect(limitAlerts([usage('seats', 1, 0)])).toEqual([])
    })
})

describe('alertText', () => {
    it('escreve "rótulo: usado de total"', () => {
        const [a] = limitAlerts([{ key: 'seats', label: 'Assentos', used: 56, total: 60 }])
        expect(alertText(a)).toBe('Assentos: 56 de 60')
    })
})

describe('seatAlert', () => {
    it('devolve só o aviso de assentos', () => {
        expect(seatAlert([usage('units', 5, 5), usage('seats', 60, 60)])?.level).toBe('full')
    })

    it('null quando sobra espaço ou não há dados', () => {
        expect(seatAlert([usage('seats', 10, 60)])).toBeNull()
        expect(seatAlert(null)).toBeNull()
    })
})
