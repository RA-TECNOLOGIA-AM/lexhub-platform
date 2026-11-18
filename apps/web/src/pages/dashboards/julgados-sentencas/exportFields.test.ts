import { describe, expect, it } from 'vitest'
import { allSlugs } from '../../../lib/exportFields.ts'
import { julgadosSentencasExport } from './exportFields.ts'
// A lista do servidor, lida do próprio arquivo da API: mudou lá sem mudar aqui, o teste quebra.
import exportPy from '../../../../../api/src/app/analyses/v1_julgados_export.py?raw'

// Os pares "slug": "valor" de um dicionário Python do arquivo (na ordem em que aparecem).
function dicionario(nome: string): [string, string][] {
    const bloco = new RegExp(`^${nome}: Dict\\[str, str\\] = \\{([\\s\\S]*?)^\\}`, 'm').exec(exportPy)
    if (!bloco) throw new Error(`${nome} não encontrado em v1_julgados_export.py`)
    return [...bloco[1].matchAll(/"([^"]+)":\s*"([^"]*)"/g)].map((m) => [m[1], m[2]])
}

describe('exportação do Julgados Sentenças', () => {
    const slugs = allSlugs(julgadosSentencasExport)
    const rotulos = Object.fromEntries(julgadosSentencasExport.flatMap((g) => g.fields.map((f) => [f.slug, f.label])))
    const api = dicionario('_CAMPOS_EXPORT_JULGADOS_SENTENCA_NG').map(([slug]) => slug)

    it('os campos da tela são exatamente os da API (nenhum a mais, nenhum faltando, sem repetir)', () => {
        expect(new Set(slugs).size).toBe(slugs.length)
        expect([...slugs].sort()).toEqual([...api].sort())
    })

    it('os rótulos são os de _LABELS_EXPORT_JULGADOS_SENTENCA_NG', () => {
        expect(rotulos).toEqual(Object.fromEntries(dicionario('_LABELS_EXPORT_JULGADOS_SENTENCA_NG')))
    })

    it('grupos da janela da v1 (GRUPOS_CAMPOS_SENTENCA)', () => {
        expect(julgadosSentencasExport.map((g) => g.group)).toEqual([
            'Identificação',
            'Processo',
            'Julgamento (1º Grau)',
            'Datas',
        ])
    })
})
