import type { ExportGroup } from '../../../lib/exportFields.ts'

// Espelha _CAMPOS_EXPORT_JULGADOS_SENTENCA_NG e _LABELS_EXPORT_JULGADOS_SENTENCA_NG (iguais na LA e no RJ) de
// apps/api/src/app/analyses/v1_julgados_export.py: os mesmos slugs e rótulos. Os grupos (e a ordem das colunas no
// arquivo, que é a dos grupos) são os da janela de exportação da v1 (GRUPOS_CAMPOS_SENTENCA em
// components/dashboard/JulgadosExportDialog.tsx). Mudou no servidor? Muda aqui também (exportFields.test.ts confere).
export const julgadosSentencasExport: ExportGroup[] = [
    {
        group: 'Identificação',
        fields: [
            { slug: 'numero_processo', label: 'Número do Processo' },
            { slug: 'materia', label: 'Matéria' },
            { slug: 'competencia', label: 'Competência' },
            { slug: 'comarca', label: 'Comarca' },
            { slug: 'uf', label: 'UF' },
        ],
    },
    {
        group: 'Processo',
        fields: [
            { slug: 'fase', label: 'Fase' },
            { slug: 'subfase', label: 'Subfase' },
        ],
    },
    {
        group: 'Julgamento (1º Grau)',
        fields: [
            { slug: 'juiz_1g', label: 'Juiz (1G)' },
            { slug: 'merito_1g', label: 'Sentença de Mérito' },
            { slug: 'valor_sentenca', label: 'Valor da Sentença' },
            { slug: 'motivo_extincao', label: 'Motivo da Extinção' },
            { slug: 'status_sentenca_embargos', label: 'Status da Sentença de Embargos' },
            { slug: 'resultado_embargos_estimado', label: 'Status Resultante dos Embargos' },
        ],
    },
    {
        group: 'Datas',
        fields: [
            { slug: 'data_ajuizamento', label: 'Data de Distribuição' },
            { slug: 'data_sentenca', label: 'Data da Sentença' },
            { slug: 'data_sentenca_embargos', label: 'Data da Sentença de Embargos' },
        ],
    },
]
