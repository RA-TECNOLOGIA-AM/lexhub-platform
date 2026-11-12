import { describe, expect, it } from 'vitest'
import type { Meta } from '../../../types/index.ts'
import { lerSetor, type PreProtocoloResponse } from './setores.ts'

const meta = { unit: 'NG' } as Meta

describe('lerSetor', () => {
    const data: PreProtocoloResponse = {
        meta,
        pendencias: { stats: { pendencias_resolvidas: 12, comparativo_pendencias_resolvidas: null } },
        protocolo: { stats: { protocolados_total: { total: 40, comparativo: -5.5 }, represados: 3 } },
    }

    it('lê campo solto e campo aninhado', () => {
        expect(lerSetor(data, 'pendencias', 'pendencias_resolvidas')).toBe(12)
        expect(lerSetor(data, 'protocolo', 'protocolados_total.total')).toBe(40)
        expect(lerSetor(data, 'protocolo', 'protocolados_total.comparativo')).toBe(-5.5)
    })

    it('null, campo ausente ou setor ausente (mock) viram null', () => {
        expect(lerSetor(data, 'pendencias', 'comparativo_pendencias_resolvidas')).toBeNull()
        expect(lerSetor(data, 'protocolo', 'nao_existe.total')).toBeNull()
        expect(lerSetor(data, 'org_documentos', 'represados')).toBeNull()
        expect(lerSetor({ meta }, 'peticionamento', 'represados')).toBeNull()
    })
})
