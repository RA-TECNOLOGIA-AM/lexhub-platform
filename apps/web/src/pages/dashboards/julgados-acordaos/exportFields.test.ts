import { describe, expect, it } from 'vitest'
import { allSlugs } from '../../../lib/exportFields.ts'
import { julgadosAcordaosExport } from './exportFields.ts'
// A lista do servidor, lida do próprio arquivo da API: mudou lá sem mudar aqui, o teste quebra.
import exportPy from '../../../../../api/src/app/analyses/v1_julgados_export.py?raw'

// Os pares "slug": "valor" de um dicionário Python do arquivo (na ordem em que aparecem).
function dicionario(nome: string): [string, string][] {
    const bloco = new RegExp(`^${nome}: Dict\\[str, str\\] = \\{([\\s\\S]*?)^\\}`, 'm').exec(exportPy)
    if (!bloco) throw new Error(`${nome} não encontrado em v1_julgados_export.py`)
    return [...bloco[1].matchAll(/"([^"]+)":\s*"([^"]*)"/g)].map((m) => [m[1], m[2]])
}

// A ordem dos campos da API (_CAMPOS_EXPORT_JULGADOS_ACORDAO_NG), como no pedido do port.
const SLUGS_API = [
    'numero_processo',
    'materia',
    'competencia',
    'comarca',
    'uf',
    'fase',
    'subfase',
    'camara_turma',
    'relator_2g',
    'merito_2g',
    'motivo_extincao',
    'data_ajuizamento',
    'data_acordao',
    'valor_acordao',
    'data_acordao_embargos',
    'status_acordao_embargos',
    'resultado_embargos_estimado',
]

describe('exportação do Julgados Acórdãos', () => {
    const slugs = allSlugs(julgadosAcordaosExport)
    const rotulos = Object.fromEntries(julgadosAcordaosExport.flatMap((g) => g.fields.map((f) => [f.slug, f.label])))

    it('o arquivo da API tem os slugs esperados, nesta ordem', () => {
        expect(dicionario('_CAMPOS_EXPORT_JULGADOS_ACORDAO_NG').map(([slug]) => slug)).toEqual(SLUGS_API)
    })

    it('os campos da tela são exatamente os da API (nenhum a mais, nenhum faltando, sem repetir)', () => {
        expect(new Set(slugs).size).toBe(slugs.length)
        expect([...slugs].sort()).toEqual([...SLUGS_API].sort())
    })

    it('os rótulos são os de _LABELS_EXPORT_JULGADOS_ACORDAO_NG', () => {
        expect(rotulos).toEqual(Object.fromEntries(dicionario('_LABELS_EXPORT_JULGADOS_ACORDAO_NG')))
    })

    it('grupos e ordem das colunas da janela da v1 (GRUPOS_CAMPOS_ACORDAO)', () => {
        expect(julgadosAcordaosExport.map((g) => g.group)).toEqual([
            'Identificação',
            'Processo',
            'Julgamento (2º Grau)',
            'Datas',
        ])
        expect(slugs).toEqual([
            'numero_processo',
            'materia',
            'competencia',
            'comarca',
            'uf',
            'fase',
            'subfase',
            'camara_turma',
            'relator_2g',
            'merito_2g',
            'valor_acordao',
            'motivo_extincao',
            'status_acordao_embargos',
            'resultado_embargos_estimado',
            'data_ajuizamento',
            'data_acordao',
            'data_acordao_embargos',
        ])
    })
})
