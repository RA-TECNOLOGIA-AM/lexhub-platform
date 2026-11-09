import { describe, expect, it } from 'vitest'
import { protocoloFor } from './protocolo.ts'

const q = (filters = {}) => ({ org: 'lexgroup', unit: 'NG', filters })

describe('protocoloFor', () => {
    it('traz metas fixas do mock', () => {
        expect(protocoloFor('NG').metas).toEqual({
            tempo_medio_dias: 3,
            no_prazo_pct: 90,
            protocolados_por_funcionario: 20,
        })
    })
    it('LA_RJ é menor que NG nas contagens', () => {
        expect(protocoloFor('LA_RJ').stats.protocolados_total.total).toBeLessThan(
            protocoloFor('NG').stats.protocolados_total.total,
        )
    })
    it('filtro de matéria reduz os protocolados', () => {
        const all = protocoloFor('NG', q()).stats.protocolados_total.total
        const one = protocoloFor('NG', q({ materia: ['ANP'] })).stats.protocolados_total.total
        expect(one).toBeLessThan(all)
        expect(one).toBeGreaterThan(0)
    })
    it('funcionário inexistente zera tudo sem NaN', () => {
        const r = protocoloFor('NG', q({ funcionario: ['Ninguém'] }))
        expect(r.stats.protocolados_total.total).toBe(0)
        expect(Number.isFinite(r.stats.ticket_medio_protocolado.total)).toBe(true)
        expect(r.protocolados_por_dia.every((p) => p.value === 0)).toBe(true)
    })
    it('mês a mês usa name AAAA-MM', () => {
        expect(protocoloFor('NG').protocolados_por_mes.every((p) => /^\d{4}-\d{2}$/.test(p.name))).toBe(true)
    })
    it('opções de filtro listam as matérias da resposta', () => {
        const r = protocoloFor('NG')
        expect(r.opcoes_filtro.materias).toEqual(r.protocolados_por_materia.map((p) => p.name))
    })
})
