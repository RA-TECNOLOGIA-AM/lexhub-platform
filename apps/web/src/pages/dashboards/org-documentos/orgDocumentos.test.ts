import { describe, expect, it } from 'vitest'
import { orgDocumentosLegadoFor } from '../../../services/mock/orgDocumentosLegado.ts'
import { orgDocumentosLegadoFilters } from './filters.ts'
import { lerOrgDocumentos } from './orgDocumentos.ts'

const meta = { unit: 'NG', from: '2026-09-01', to: '2026-09-30', source: 'NG', synced_at: null, timezone: 'x' }

describe('lerOrgDocumentos', () => {
    it('lê a rota da NG (/org-documentos)', () => {
        const p = lerOrgDocumentos({
            meta,
            dashboard: 'org-documentos',
            stats: { resolvidos_total: 46, nao_organizados: 11, retorno_pendencia: 3, retorno_pet: 0 },
            resolvidos_total_por_materia: [{ name: 'MORA', value: 7 }],
            comissionamento_por_funcionario: [
                { funcionario: 'João Pedro', qtd_resolvidos: 16, valor_causa_gerado: 418372.28, valor_comissao: 4.02 },
            ],
        } as never)
        expect(p.resolvidos).toBe(46)
        expect(p.represados).toBe(11)
        expect(p.retornoPendencia).toBe(3)
        expect(p.retornoConfeccao).toBe(0)
        expect(p.porMateria).toEqual([{ name: 'MORA', value: 7 }])
        expect(p.comissao[0]).toMatchObject({ funcionario: 'João Pedro', qtd_resolvidos: 16 })
    })

    it('lê a rota da LA (/org_doc_LA), com os nomes _LA', () => {
        const p = lerOrgDocumentos({
            meta,
            dashboard: 'org_doc_LA',
            stats: { total_organizados_LA: 10, nao_organizados_LA: 8, retorno_pendencia_LA: 35 },
            organizados_por_funcionario_LA: [{ name: 'ISABELLY CRISTINNE', value: 5 }],
            resolvidos_por_dia_LA: [{ name: '2026-11-09', value: 7 }],
        } as never)
        expect(p.la).toBe(true)
        expect(p.resolvidos).toBe(10)
        expect(p.represados).toBe(8)
        expect(p.retornoPendencia).toBe(35)
        expect(p.retornoConfeccao).toBeNull()
        expect(p.reajuizamento).toBeNull()
        expect(p.porDia).toEqual([{ name: '2026-11-09', value: 7 }])
    })

    it('NG com os campos _LA vazios na resposta continua NG', () => {
        const p = lerOrgDocumentos({
            meta,
            dashboard: 'org-documentos',
            stats: { resolvidos_total: 4, total_organizados_LA: null },
        } as never)
        expect(p.la).toBe(false)
        expect(p.resolvidos).toBe(4)
    })

    it('resposta vazia: null ou lista vazia', () => {
        const p = lerOrgDocumentos({ meta, stats: {} })
        expect(p.resolvidos).toBeNull()
        expect(p.porMes).toEqual([])
    })
})

describe('filtros', () => {
    it('sem a matéria vazia ("-") e sem repetir a pessoa com o nome completo', () => {
        const p = lerOrgDocumentos(orgDocumentosLegadoFor('NG', { org: 'lexgroup', unit: 'NG' }))
        const [func, mat] = orgDocumentosLegadoFilters(p)
        expect(func.options.map((o) => o.value)).toEqual(['Hingrid Conrrado', 'João Pedro', 'José Henrique'])
        expect(mat.options.map((o) => o.value)).not.toContain('-')
        expect(mat.options.map((o) => o.value)).toContain('MORA')
    })
})
