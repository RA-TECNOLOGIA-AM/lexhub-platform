import { describe, expect, it } from 'vitest'
import { julgadosSentencasFor } from '../../../services/mock/julgadosSentencas.ts'
import { criarMemoriaOpcoes } from '../julgados-acordaos/filters.ts'
import { sentencasFilters, valorDoFiltro } from './filters.ts'

describe('Julgados Sentenças: filtros', () => {
    it('janela com UF, situação e matéria; juiz (no lugar do relator) só pelos gráficos', () => {
        const fields = sentencasFilters(julgadosSentencasFor('NG'), {}, criarMemoriaOpcoes())
        const keys = fields.map((f) => f.key)
        expect(keys.slice(0, 3)).toEqual(['uf_julgados', 'situacao_processo', 'materia_julgados'])
        expect(keys).toContain('juiz_julgados')
        expect(keys).not.toContain('relator_julgados')
        expect(fields.find((f) => f.key === 'juiz_julgados')?.fromChart).toBe(true)
    })

    it('valor do clique: sem espaço, UF em maiúsculas, vazio não filtra', () => {
        expect(valorDoFiltro('uf_julgados', ' rj ')).toBe('RJ')
        expect(valorDoFiltro('juiz_julgados', ' Dra. Fulana ')).toBe('Dra. Fulana')
        expect(valorDoFiltro('juiz_julgados', '  ')).toBeNull()
    })
})
