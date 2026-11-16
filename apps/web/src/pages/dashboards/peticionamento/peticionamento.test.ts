import { describe, expect, it } from 'vitest'
import { peticionamentoLegadoFor } from '../../../services/mock/peticionamentoLegado.ts'
import { peticionamentoLegadoFilters } from './filters.ts'
import { lerPeticionamento } from './peticionamento.ts'

const meta = { unit: 'NG', from: '2026-09-01', to: '2026-10-08', source: 'NG', synced_at: null, timezone: 'x' }

describe('lerPeticionamento', () => {
    it('lê a rota da NG (/peticionamento)', () => {
        const p = lerPeticionamento({
            meta,
            dashboard: 'peticionamento',
            stats: {
                total_peticionados: 68,
                processos_em_revisao: 5,
                nao_peticionados: 9,
                peticionamento_taxa_resolvidos: 88.31,
                comparativo_mediana_tempo_pet: 100,
            },
            peticionados_por_materia: [{ name: 'CESTA', value: 13 }],
            comissionamento_peticionamento_por_funcionario: [
                { funcionario: 'Ana', qtd_acoes_massa: 2, valor_comissao: 6, taxa_resolvidos: null },
            ],
        } as never)
        expect(p.total).toBe(68)
        expect(p.revisao).toBe(5)
        expect(p.naoPeticionados).toBe(9)
        expect(p.taxas.resolvidos).toBe(88.31)
        expect(p.comparativo.medianaTempo).toBe(100)
        expect(p.porMateria).toEqual([{ name: 'CESTA', value: 13 }])
        expect(p.comissao[0]).toMatchObject({ funcionario: 'Ana', qtd_acoes_massa: 2, valor_comissao: 6 })
    })

    it('lê a rota da LA (/peticionamento_LA), com os nomes _LA', () => {
        const p = lerPeticionamento({
            meta,
            dashboard: 'peticionamento_LA',
            stats: {
                total_confeccionados_LA: 1,
                nao_confeccionados_LA: 12,
                peticionamento_taxa_retorno_protocolo_LA: 50,
                peticionamento_qtd_retorno_protocolo_LA: 1,
                peticionamento_qtd_entrada_protocolo_LA: 2,
            },
            confeccionados_por_funcionario_LA: [{ name: 'JAMINIE FARIAS', value: 1 }],
        } as never)
        expect(p.la).toBe(true)
        expect(p.total).toBe(1)
        expect(p.naoPeticionados).toBe(12)
        expect(p.revisao).toBeNull()
        expect(p.reajuizamento).toBeNull()
        expect(p.retornoProtocolo).toEqual({ taxa: 50, retornos: 1, entradas: 2 })
        expect(p.porFuncionario).toEqual([{ name: 'JAMINIE FARIAS', value: 1 }])
    })

    it('NG com os campos _LA vazios na resposta continua NG', () => {
        const p = lerPeticionamento({
            meta,
            dashboard: 'peticionamento',
            stats: { total_peticionados: 3, total_confeccionados_LA: null },
        } as never)
        expect(p.la).toBe(false)
        expect(p.total).toBe(3)
    })

    it('resposta vazia: null ou lista vazia', () => {
        const p = lerPeticionamento({ meta, stats: {} })
        expect(p.total).toBeNull()
        expect(p.porMes).toEqual([])
    })
})

describe('filtros', () => {
    it('funcionários pelo nome dos gráficos, sem repetir a mesma pessoa com o nome completo', () => {
        const p = lerPeticionamento(peticionamentoLegadoFor('NG', { org: 'lexgroup', unit: 'NG' }))
        const [func, mat] = peticionamentoLegadoFilters(p)
        const nomes = func.options.map((o) => o.value)
        expect(nomes).toContain('Millena de')
        expect(nomes).not.toContain('Millena de Souza Sá Graça')
        expect(mat.options.map((o) => o.value)).toContain('CESTA')
    })
})
