import { describe, expect, it } from 'vitest'
import { periodError, periodLabel, presetPeriod, todayIso } from './period.ts'

const NOW = new Date(2026, 10, 10) // 10/11/2026, no horário local

describe('period', () => {
    it('hoje no formato da API', () => {
        expect(todayIso(NOW)).toBe('2026-11-10')
    })

    it('atalhos a partir de hoje', () => {
        expect(presetPeriod('este-mes', NOW)).toEqual({ from: '2026-11-01', to: '2026-11-10' })
        expect(presetPeriod('mes-passado', NOW)).toEqual({ from: '2026-10-01', to: '2026-10-31' })
        expect(presetPeriod('ultimos-30', NOW)).toEqual({ from: '2026-10-12', to: '2026-11-10' })
        expect(presetPeriod('este-ano', NOW)).toEqual({ from: '2026-01-01', to: '2026-11-10' })
    })

    it('mês passado em janeiro volta para dezembro do ano anterior', () => {
        expect(presetPeriod('mes-passado', new Date(2026, 0, 15))).toEqual({ from: '2025-12-01', to: '2025-12-31' })
    })

    it('valida o período livre', () => {
        const today = '2026-11-10'
        expect(periodError({ from: '2024-01-01', to: '2026-11-10' }, today)).toBeNull()
        expect(periodError({ from: '', to: '2026-11-10' }, today)).toBe('Escolha as duas datas.')
        expect(periodError({ from: '2026-11-05', to: '2026-11-01' }, today)).toBe(
            'A data inicial precisa ser antes da final.',
        )
        expect(periodError({ from: '2026-11-01', to: '2026-12-01' }, today)).toBe(
            'A data final não pode ser depois de hoje.',
        )
    })

    it('texto do botão sem repetir o que é igual', () => {
        expect(periodLabel({ from: '2026-10-05', to: '2026-10-05' })).toBe('5 de out. de 2026')
        expect(periodLabel({ from: '2026-10-01', to: '2026-10-30' })).toBe('1 a 30 de out. de 2026')
        expect(periodLabel({ from: '2026-09-28', to: '2026-10-05' })).toBe('28 de set. a 5 de out. de 2026')
        expect(periodLabel({ from: '2025-12-01', to: '2026-01-31' })).toBe('1 de dez. de 2025 a 31 de jan. de 2026')
    })
})
