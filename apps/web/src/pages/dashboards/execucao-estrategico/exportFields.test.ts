import { describe, expect, it } from 'vitest'
import { allSlugs } from '../../../lib/exportFields.ts'
import { camposProcessos } from '../acordos/exportFields.ts'
import { camposExecucao } from '../execucao/exportFields.ts'
import { estrategicoExport, relatorioDoEscopo } from './exportFields.ts'

describe('relatório do Execução Estratégico Geral', () => {
    const [condenacao, acordos, ambos] = estrategicoExport

    it('Condenação (principal), Acordos e os dois juntos, todos com origem e recorte', () => {
        expect(estrategicoExport.map((r) => r.key)).toEqual([null, 'acordos', 'ambos'])
        for (const r of estrategicoExport) expect(r.options?.map((o) => o.key)).toEqual(['origem', 'criterio'])
        expect(condenacao.groups).toBe(camposExecucao)
        expect(acordos.groups).toBe(camposProcessos)
    })

    it('os dois juntos: os campos de cada lado com o prefixo da API, um bloco de cada', () => {
        expect(allSlugs(ambos.groups)).toEqual([
            ...allSlugs(camposExecucao).map((s) => `condenacao.${s}`),
            ...allSlugs(camposProcessos).map((s) => `acordos.${s}`),
        ])
        expect([...new Set(ambos.groups.map((g) => g.block))]).toEqual(['Condenação', 'Acordos'])
    })

    it('a janela abre no escopo da página (Ambos = os dois juntos)', () => {
        expect(relatorioDoEscopo({})).toBe('ambos')
        expect(relatorioDoEscopo({ escopo: ['condenacao'] })).toBeNull()
        expect(relatorioDoEscopo({ escopo: ['acordos'] })).toBe('acordos')
    })
})
