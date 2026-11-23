import type { DashboardFilters } from '../../../types/index.ts'
import type { ExportGroup, ExportOptionDef, ExportReport } from '../../../lib/exportFields.ts'
import { camposProcessos } from '../acordos/exportFields.ts'
import { camposExecucao, RECORTE } from '../execucao/exportFields.ts'
import { escopoDe } from './estrategico.ts'

// O "Relatório" da página da v1 (ExecucaoRelatorioPersonalizadoDialog), na janela de exportação da V2. Espelha
// dashboards/execucao_estrategico_export.py: Condenação (o principal), Acordos e os dois num arquivo só (no XLSX uma
// aba de cada, no CSV um .zip com um CSV de cada). Os campos são os da Execução Condenação e da Execução Acordos.

// A origem da v1: com os filtros da página ou do zero (só o período e o recorte).
export const ORIGEM: ExportOptionDef = {
    key: 'origem',
    label: 'Origem',
    choices: [
        {
            value: 'pagina',
            label: 'Filtros ativos na página',
            note: 'O arquivo sai filtrado pelo período e pela UF, comarca, matéria, subfase e ano de ajuizamento da página.',
        },
        {
            value: 'personalizado',
            label: 'Relatório personalizado',
            note: 'Do zero: só o período e o recorte, sem os filtros da página.',
        },
    ],
}

const OPCOES = [ORIGEM, RECORTE]

// Os campos de uma parte no relatório dos dois: com o prefixo que a API espera e o bloco na janela.
const comPrefixo = (groups: ExportGroup[], prefixo: string, bloco: string): ExportGroup[] =>
    groups.map((g) => ({
        group: g.group,
        block: bloco,
        fields: g.fields.map((f) => ({ slug: `${prefixo}.${f.slug}`, label: f.label })),
    }))

export const estrategicoExport: ExportReport[] = [
    { key: null, title: 'Condenação', groups: camposExecucao, options: OPCOES },
    { key: 'acordos', title: 'Acordos', groups: camposProcessos, options: OPCOES },
    {
        key: 'ambos',
        title: 'Os dois juntos',
        groups: [
            ...comPrefixo(camposExecucao, 'condenacao', 'Condenação'),
            ...comPrefixo(camposProcessos, 'acordos', 'Acordos'),
        ],
        options: OPCOES,
    },
]

// A janela abre no escopo da página, como a origem "Filtros ativos" da v1 (Ambos = os dois juntos).
export function relatorioDoEscopo(filters: DashboardFilters): string | null {
    const escopo = escopoDe(filters.escopo)
    return escopo === 'condenacao' ? null : escopo === 'acordos' ? 'acordos' : 'ambos'
}
