import { describe, expect, it } from 'vitest'
import { paramsFromQuery, queryFromParams } from '../../../lib/dashboardQuery.ts'
import { filterChips, toggleFilter } from '../../../lib/filters.ts'
import { julgadosAcordaosFor } from '../../../services/mock/julgadosAcordaos.ts'
import { criarMemoriaOpcoes, julgadosFilters, opcoesMantidas, valorDoFiltro } from './filters.ts'
import type { JulgadosAcordaosResponse } from './types.ts'

const resposta = (
    stats: Record<string, unknown> = {},
    extra: Record<string, unknown> = {},
): JulgadosAcordaosResponse => ({
    meta: { unit: 'NG', from: '2026-10-01', to: '2026-10-31', source: 'LexFlow', synced_at: null, timezone: 'x' },
    dashboard: 'julgados_acordaos_NG',
    stats,
    ...extra,
})

describe('parâmetros dos filtros (os nomes da v1)', () => {
    it('ida e volta pela URL, com valores repetidos', () => {
        const texto =
            'from=2026-10-01&to=2026-10-31&materia_julgados=ANP&materia_julgados=MORA&relator_julgados=Roberta+Sales' +
            '&comarca_julgados=Manaus&competencia_julgados=C%C3%ADvel&categoria_julgados=procedente&uf_julgados=AM' +
            '&motivo_extincao_julgados=Litispend%C3%AAncia&ano_ajuizamento_julgados=2023' +
            '&resultado_embargos_julgados=Revertido+Ganho&situacao_processo=ATIVO'
        const q = queryFromParams(new URLSearchParams(texto))
        expect(q.filters).toEqual({
            materia_julgados: ['ANP', 'MORA'],
            relator_julgados: ['Roberta Sales'],
            comarca_julgados: ['Manaus'],
            competencia_julgados: ['Cível'],
            categoria_julgados: ['procedente'],
            uf_julgados: ['AM'],
            motivo_extincao_julgados: ['Litispendência'],
            ano_ajuizamento_julgados: ['2023'],
            resultado_embargos_julgados: ['Revertido Ganho'],
            situacao_processo: ['ATIVO'],
        })
        expect(paramsFromQuery(q).toString()).toBe(texto)
    })
})

describe('valorDoFiltro (clique nos gráficos)', () => {
    it('limpa o valor, põe a UF em maiúsculas e ignora vazio', () => {
        expect(valorDoFiltro('relator_julgados', '  Roberta Sales ')).toBe('Roberta Sales')
        expect(valorDoFiltro('uf_julgados', ' am ')).toBe('AM')
        expect(valorDoFiltro('materia_julgados', '   ')).toBeNull()
        expect(valorDoFiltro('materia_julgados', 'Sem matéria')).toBe('Sem matéria') // a API também filtra por ele
    })

    it('clicar de novo desliga (toggle, como toggleJulgadosAcordaoFilterValue)', () => {
        const um = toggleFilter({}, 'relator_julgados', 'Roberta Sales')
        expect(um).toEqual({ relator_julgados: ['Roberta Sales'] })
        expect(
            toggleFilter(toggleFilter(um, 'relator_julgados', 'Mariana Couto'), 'relator_julgados', 'Roberta Sales'),
        ).toEqual({
            relator_julgados: ['Mariana Couto'],
        })
        expect(toggleFilter(um, 'relator_julgados', 'Roberta Sales')).toEqual({})
    })
})

describe('opções de matéria (useOpcoesFiltroMateria da v1)', () => {
    it('sem matéria escolhida, acompanham os dados (em ordem, sem vazio e sem "—")', () => {
        expect(opcoesMantidas(['VELHA'], ['MORA', 'ANP', ' ', '—', 'ANP'], [])).toEqual(['ANP', 'MORA'])
    })

    it('com matéria escolhida, mantêm as já vistas e o escolhido', () => {
        expect(opcoesMantidas(['ANP', 'MORA'], ['ANP'], ['ANP', 'CESTA'])).toEqual(['ANP', 'CESTA', 'MORA'])
    })

    it('a memória guarda o que já apareceu enquanto se filtra', () => {
        const lembrar = criarMemoriaOpcoes()
        expect(lembrar('NG', ['ANP', 'MORA', 'SEGURO'], [])).toEqual(['ANP', 'MORA', 'SEGURO'])
        // filtrou por ANP: a resposta só traz ANP, mas MORA e SEGURO continuam na lista
        expect(lembrar('NG', ['ANP'], ['ANP'])).toEqual(['ANP', 'MORA', 'SEGURO'])
        // limpou: volta a acompanhar os dados
        expect(lembrar('NG', ['ANP', 'CESTA'], [])).toEqual(['ANP', 'CESTA'])
        // outra unidade, outra memória
        expect(lembrar('LA_AM', ['MORA'], [])).toEqual(['MORA'])
    })
})

describe('julgadosFilters', () => {
    const data = resposta(
        { julgados_acordao_uf_opcoes_NG: ['AM', 'PA'] },
        {
            julgados_acordao_por_materia_NG: [{ name: 'ANP', value: 3 }],
            historico_julgados_acordao_por_materia_NG: [
                { name: 'MORA', value: 9 },
                { name: 'ANP', value: 20 },
            ],
        },
    )

    it('a janela tem UF, situação do processo e matéria (como a v1); o resto só vira etiqueta', () => {
        const fields = julgadosFilters(data, {}, criarMemoriaOpcoes())
        expect(fields.filter((f) => !f.fromChart).map((f) => [f.key, f.label])).toEqual([
            ['uf_julgados', 'UF'],
            ['situacao_processo', 'Situação do processo'],
            ['materia_julgados', 'Matéria'],
        ])
        expect(fields.filter((f) => f.fromChart).map((f) => f.key)).toEqual([
            'relator_julgados',
            'comarca_julgados',
            'competencia_julgados',
            'categoria_julgados',
            'motivo_extincao_julgados',
            'ano_ajuizamento_julgados',
            'resultado_embargos_julgados',
        ])
        const opcoes = (key: string) => fields.find((f) => f.key === key)?.options.map((o) => o.value)
        expect(opcoes('uf_julgados')).toEqual(['AM', 'PA'])
        expect(opcoes('materia_julgados')).toEqual(['ANP', 'MORA']) // período + histórico
        expect(opcoes('situacao_processo')).toEqual(['ATIVO', 'SUSPENSO/SOBRESTADO', 'ARQUIVADO'])
    })

    it('sem UF na base, sem o filtro de UF (v1)', () => {
        const fields = julgadosFilters(resposta(), {}, criarMemoriaOpcoes())
        expect(fields.some((f) => f.key === 'uf_julgados')).toBe(false)
    })

    it('etiquetas com os textos da v1 (categoria e embargos)', () => {
        const fields = julgadosFilters(data, {}, criarMemoriaOpcoes())
        const chips = filterChips(fields, {
            categoria_julgados: ['improcedente'],
            resultado_embargos_julgados: ['Revertido Ganho'],
            relator_julgados: ['Roberta Sales'],
            situacao_processo: ['SUSPENSO/SOBRESTADO'],
        })
        expect(chips.map((c) => c.text)).toEqual([
            'Suspenso / Sobrestado',
            'Roberta Sales',
            'Improcedentes',
            'Embargos: Revertido Ganho',
        ])
        expect(chips.map((c) => c.label)).toContain('Relator: Roberta Sales')
    })

    it('no mock, filtrar de verdade muda os números', () => {
        const q = (filters = {}) => ({ org: 'lexgroup', unit: 'NG', from: '2026-01-01', to: '2026-10-31', filters })
        const total = (r: JulgadosAcordaosResponse) => (r.stats?.julgados_acordao_total_NG as number) ?? 0
        const todos = total(julgadosAcordaosFor('NG', q()))
        const procedentes = julgadosAcordaosFor('NG', q({ categoria_julgados: ['procedente'] }))
        expect(total(procedentes)).toBeLessThan(todos)
        expect(total(procedentes)).toBe(procedentes.stats?.julgados_acordao_procedentes_NG)
        expect(procedentes.stats?.julgados_acordao_improcedentes_NG).toBe(0)
        const relator = julgadosAcordaosFor('NG', q({ relator_julgados: ['roberta sales'] })) // sem diferenciar maiúsculas
        const linhas = relator.julgados_acordao_lista_NG as { relator: string }[]
        expect(linhas.length).toBeGreaterThan(0)
        expect(linhas.every((l) => l.relator === 'Roberta Sales')).toBe(true)
    })
})
