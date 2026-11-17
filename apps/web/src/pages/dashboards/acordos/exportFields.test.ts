import { describe, expect, it } from 'vitest'
import { allSlugs, defaultOptions } from '../../../lib/exportFields.ts'
import { execucaoExport } from '../execucao/exportFields.ts'
import { acordosExport } from './exportFields.ts'

// Os campos batem com a API em apps/api/tests/test_dashboard_export.py; aqui, a forma dos relatórios.
describe('exportação da Execução Condenação e da Execução Acordos', () => {
    it('Execução: um relatório (processos) com o recorte da v1, padrão "entrada"', () => {
        expect(execucaoExport).toHaveLength(1)
        expect(execucaoExport[0].key).toBeNull()
        expect(defaultOptions(execucaoExport[0])).toEqual({ criterio: 'entrada' })
        expect(execucaoExport[0].options?.[0].choices.map((c) => c.value)).toEqual(['entrada', 'saida', 'total'])
        expect(allSlugs(execucaoExport[0].groups)).toContain('valor_saida_periodo')
    })

    it('Acordos: processos (recorte) e atividades (?relatorio=atividades, visão "concluidas" por padrão)', () => {
        expect(acordosExport.map((r) => [r.key, r.title])).toEqual([
            [null, 'Processos'],
            ['atividades', 'Atividades'],
        ])
        expect(defaultOptions(acordosExport[1])).toEqual({ view: 'concluidas' })
        expect(allSlugs(acordosExport[1].groups)).toEqual([
            'numero_processo',
            'atividade',
            'status',
            'situacao',
            'funcionario',
            'funcionario_atribuido',
            'funcionario_encerramento',
            'prazo',
            'criado_em',
            'descricao',
            'operacao',
        ])
    })

    it('relatório sem opções não tem escolha padrão', () => {
        expect(defaultOptions({ key: null, title: '', groups: [] })).toEqual({})
    })
})
