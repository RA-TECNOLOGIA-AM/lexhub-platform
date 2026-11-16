import { describe, expect, it } from 'vitest'
import { protocoloLegadoFor } from '../../../services/mock/protocoloLegado.ts'
import { protocoloLegadoFilters } from './filters.ts'
import { lerProtocolo, opcoesProtocolo } from './protocolo.ts'

const meta = { unit: 'NG', from: '2026-11-01', to: '2026-11-16', source: 'NG', synced_at: null, timezone: 'x' }

describe('lerProtocolo', () => {
    it('lê a rota da NG (/protocolo)', () => {
        const p = lerProtocolo({
            meta,
            dashboard: 'protocolo',
            stats: {
                protocolos_resolvidos: 4,
                nao_protocolados: 12,
                valor_causa_protocolo_novo: 1000,
                protocolados_de_reajuizamento: 2,
                comparativo_protocolos_resolvidos: -11.89,
                // a resposta da v1 traz também os campos da LA, vazios
                protocolos_resolvidos_LA: null,
                taxa_protocolados_LA: null,
            },
            protocolados_por_materia_LA: [],
            protocolados_por_materia: [{ name: 'ANP', value: 3 }],
        } as never)
        expect(p.la).toBe(false)
        expect(p.protocolados).toBe(4)
        expect(p.represados).toBe(12)
        expect(p.ticket).toBe(250) // sem o ticket do servidor: valor ÷ protocolados, como a v1
        expect(p.reajuizamento).toEqual({ protocolados: 2, represados: null })
        expect(p.taxa).toBeNull()
        expect(p.comparativo.protocolados).toBe(-11.89)
        expect(p.comparativo.medianaTempo).toBeNull()
        expect(p.porMateria).toEqual([{ name: 'ANP', value: 3 }])
    })

    it('lê a rota da LA (/protocolo_LA), com os nomes _LA', () => {
        const p = lerProtocolo({
            meta,
            dashboard: 'protocolo_LA',
            stats: { protocolos_resolvidos_LA: 7, taxa_protocolados_LA: 90, entradas_protocolo_LA: 8 },
            protocololados_por_funcionario_LA: [{ name: 'Ana', value: 7 }],
            represados_por_mes_LA: [{ name: 'mai 2026', value: 6 }],
            comissionamento_protocolo_LA_por_funcionario: [
                { funcionario: 'Ana', qtd_protocolados: 7, valor_comissao: 10.5 },
            ],
        } as never)
        expect(p.la).toBe(true)
        expect(p.protocolados).toBe(7)
        expect(p.reajuizamento).toBeNull()
        expect(p.taxa).toEqual({ valor: 90, entradas: 8 })
        expect(p.porFuncionario).toEqual([{ name: 'Ana', value: 7 }])
        expect(p.naoPorMes).toEqual([{ name: 'mai 2026', value: 6 }])
        expect(p.comissao).toEqual([{ funcionario: 'Ana', qtd_protocolados: 7, valor_comissao: 10.5 }])
    })

    it('resposta vazia (mock sem dados): tudo null ou lista vazia', () => {
        const p = lerProtocolo({ meta, stats: {} })
        expect(p.protocolados).toBeNull()
        expect(p.porDia).toEqual([])
        expect(p.comissao).toEqual([])
    })

    it('o mock da NG e o da LA dão a mesma tela', () => {
        const ng = lerProtocolo(protocoloLegadoFor('NG', { org: 'lexgroup', unit: 'NG' }))
        const la = lerProtocolo(protocoloLegadoFor('LA_AM', { org: 'lexgroup', unit: 'LA_AM' }))
        expect(ng.la).toBe(false)
        expect(la.la).toBe(true)
        for (const p of [ng, la]) {
            expect(p.protocolados).toBeGreaterThan(0)
            expect(p.porMes.length).toBeGreaterThan(12)
            expect(p.mediaPorFuncionario.length).toBe(8)
        }
    })
})

describe('filtros', () => {
    it('opções da resposta, sem repetir e sem "Sem matéria"; o sistema é de um valor só', () => {
        const p = lerProtocolo(protocoloLegadoFor('NG', { org: 'lexgroup', unit: 'NG' }))
        const o = opcoesProtocolo(p)
        expect(o.materias).toContain('ANP')
        expect(new Set(o.materias).size).toBe(o.materias.length)
        const campos = protocoloLegadoFilters(p)
        expect(campos.map((c) => c.key)).toEqual(['funcionario', 'materia', 'sistema'])
        expect(campos[1].options.some((x) => x.value === 'Sem matéria')).toBe(false)
        expect(campos[2].single).toBe(true)
    })
})
