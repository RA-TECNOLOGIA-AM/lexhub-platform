import type { ExportGroup } from '../../../lib/exportFields.ts'

// Espelha `_CAMPOS_EXPORT_RECURSAL_NG` e `_LABELS_EXPORT_RECURSAL_NG` (iguais no LA e no RJ) da v1, com os grupos da
// janela "Relatório Personalizado" dela (RecursalRelatorioPersonalizadoDialog). Mudou no servidor? Muda aqui também:
// a API só aceita campos da lista dela (dashboards/recursal_export.py).
export const recursalExport: ExportGroup[] = [
    {
        group: 'Identificação',
        fields: [
            { slug: 'id', label: 'ID' },
            { slug: 'numero_processo', label: 'Número do Processo' },
            { slug: 'uf', label: 'UF' },
            { slug: 'parte_adversa', label: 'Parte Adversa' },
        ],
    },
    {
        group: 'Processo',
        fields: [
            { slug: 'materia', label: 'Matéria' },
            { slug: 'fase', label: 'Fase' },
            { slug: 'subfase', label: 'Subfase' },
            { slug: 'operacao', label: 'Operação' },
            { slug: 'vara', label: 'Vara' },
            { slug: 'competencia', label: 'Competência' },
        ],
    },
    {
        group: 'Status judicial',
        fields: [
            { slug: 'status_1g', label: 'Status 1º Grau' },
            { slug: 'juiz_1g', label: 'Juiz (1º Grau)' },
            { slug: 'status_2g', label: 'Status 2º Grau' },
            { slug: 'relator_2g', label: 'Relator (2º Grau)' },
            { slug: 'decisao', label: 'Decisão' },
        ],
    },
    {
        group: 'Valores',
        fields: [
            { slug: 'valor_causa_sentenca', label: 'Valor da Causa (Sentença)' },
            { slug: 'valor_causa_acordo', label: 'Valor da Causa (Acordo)' },
            { slug: 'dano_moral_sentenca', label: 'Dano Moral (Sentença)' },
            { slug: 'dano_material_sentenca', label: 'Dano Material (Sentença)' },
        ],
    },
    {
        group: 'Datas',
        fields: [
            { slug: 'data_ajuizamento', label: 'Data de Ajuizamento' },
            { slug: 'data_sentenca', label: 'Data da Sentença' },
            { slug: 'data_acordao', label: 'Data do Acórdão' },
            { slug: 'data_transito_julgado', label: 'Data Trânsito em Julgado' },
            { slug: 'dt_entrada_recursal', label: 'Data Entrada Recursal' },
            { slug: 'dt_saida_recursal', label: 'Data Saída Recursal' },
            { slug: 'data_ultima_movimentacao', label: 'Última Movimentação' },
        ],
    },
    {
        group: 'Atividades',
        fields: [
            { slug: 'atividade_recursos', label: 'Atividade em Andamento' },
            { slug: 'status_agendamento_recursos', label: 'Status da Atividade' },
        ],
    },
]
