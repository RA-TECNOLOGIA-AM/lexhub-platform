import { describe, expect, it } from 'vitest'
import { allSlugs, type ExportGroup } from '../../lib/exportFields.ts'
import type { V1GenericoResponse } from './v1Stats.ts'
import { orgDocumentosExport, orgDocumentosExportLA, orgDocumentosExportNG } from './org-documentos/exportFields.ts'
import { pendenciasExport, pendenciasExportLA, pendenciasExportNG } from './pendencias/exportFields.ts'
import { peticionamentoExport, peticionamentoExportLA, peticionamentoExportNG } from './peticionamento/exportFields.ts'
import { protocoloExport, protocoloExportLA, protocoloExportNG } from './protocolo/exportFields.ts'
// A lista do servidor, lida do próprio arquivo da API: mudou lá sem mudar aqui, o teste quebra.
import exportPy from '../../../../api/src/app/analyses/v1_legado_export.py?raw'

// Os pares "slug": "valor" de um dicionário Python do arquivo (na ordem em que aparecem).
function dicionario(nome: string): [string, string][] {
    const bloco = new RegExp(`^${nome}: Dict\\[str, str\\] = \\{([\\s\\S]*?)^\\}`, 'm').exec(exportPy)
    if (!bloco) throw new Error(`${nome} não encontrado em v1_legado_export.py`)
    return [...bloco[1].matchAll(/"([^"]+)":\s*"([^"]*)"/g)].map((m) => [m[1], m[2]])
}

// dashboard -> (prefixo na API, lista NG/RJ, lista LA, escolha pela resposta, rota da LA na v1)
const casos: [string, string, ExportGroup[], ExportGroup[], (d: V1GenericoResponse) => ExportGroup[], string][] = [
    ['Protocolo', 'PROTOCOLO', protocoloExportNG, protocoloExportLA, protocoloExport, 'protocolo_LA'],
    [
        'Peticionamento',
        'PETICIONAMENTO',
        peticionamentoExportNG,
        peticionamentoExportLA,
        peticionamentoExport,
        'peticionamento_LA',
    ],
    ['Org. de Documentos', 'ORG_DOC', orgDocumentosExportNG, orgDocumentosExportLA, orgDocumentosExport, 'org_doc_LA'],
    ['Pendências', 'PENDENCIAS', pendenciasExportNG, pendenciasExportLA, pendenciasExport, 'pendencia_LA'],
]

describe.each(casos)('exportação do %s (banco legado)', (_, prefixo, ng, la, escolher, rotaLA) => {
    it.each([
        ['NG', ng],
        ['LA', la],
    ] as const)('%s: os campos e rótulos são exatamente os da API', (unidade, grupos) => {
        const slugs = allSlugs(grupos)
        const rotulos = Object.fromEntries(grupos.flatMap((g) => g.fields.map((f) => [f.slug, f.label])))
        const api = dicionario(`_CAMPOS_EXPORT_${prefixo}_${unidade}`).map(([slug]) => slug)
        expect(new Set(slugs).size).toBe(slugs.length)
        expect([...slugs].sort()).toEqual([...api].sort())
        expect(rotulos).toEqual(Object.fromEntries(dicionario(`_LABELS_EXPORT_${prefixo}_${unidade}`)))
    })

    it('a resposta da LA abre a lista da LA; a de NG/RJ, a da NG', () => {
        expect(escolher({ dashboard: rotaLA } as V1GenericoResponse)).toBe(la)
        expect(escolher({ dashboard: rotaLA.replace('_LA', '_RJ') } as V1GenericoResponse)).toBe(ng)
    })
})
