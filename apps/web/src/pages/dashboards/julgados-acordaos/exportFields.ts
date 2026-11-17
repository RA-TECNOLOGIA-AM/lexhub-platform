import type { ExportGroup } from '../../../lib/exportFields.ts'

// Espelha _CAMPOS_EXPORT_JULGADOS_ACORDAO_NG e _LABELS_EXPORT_JULGADOS_ACORDAO_NG (iguais na LA e no RJ) de
// apps/api/src/app/analyses/v1_julgados_export.py: os mesmos slugs e rótulos. Os grupos (e a ordem das colunas no
// arquivo, que é a dos grupos) são os da janela de exportação da v1 (GRUPOS_CAMPOS_ACORDAO em
// components/dashboard/JulgadosExportDialog.tsx). Mudou no servidor? Muda aqui também: a API só aceita campos da
// lista dela (exportFields.test.ts confere).
export const julgadosAcordaosExport: ExportGroup[] = [
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
            { slug: 'camara_turma', label: 'Câmara/Turma' },
        ],
    },
    {
        group: 'Julgamento (2º Grau)',
        fields: [
            { slug: 'relator_2g', label: 'Relator (2G)' },
            { slug: 'merito_2g', label: 'Acórdão de Mérito' },
            { slug: 'valor_acordao', label: 'Valor do Acórdão' },
            { slug: 'motivo_extincao', label: 'Motivo da Extinção' },
            { slug: 'status_acordao_embargos', label: 'Status do Acórdão de Embargos' },
            { slug: 'resultado_embargos_estimado', label: 'Status Resultante dos Embargos' },
        ],
    },
    {
        group: 'Datas',
        fields: [
            { slug: 'data_ajuizamento', label: 'Data de Distribuição' },
            { slug: 'data_acordao', label: 'Data do Acórdão' },
            { slug: 'data_acordao_embargos', label: 'Data do Acórdão de Embargos' },
        ],
    },
]
