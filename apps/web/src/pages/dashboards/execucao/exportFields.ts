import type { ExportGroup, ExportOptionDef, ExportReport } from '../../../lib/exportFields.ts'

// Espelha `_CAMPOS_EXPORT_EXECUCAO_NG` e `_LABELS_EXPORT_EXECUCAO_NG` (api_dashboards/src/app/dashboard_routes.py,
// v1), com os grupos da janela da v1 (ExecucaoRelatorioPersonalizadoDialog). Mudou no servidor? Muda aqui também:
// a API só aceita campos da lista dela (dashboards/execucao_export.py).

// O recorte da v1 (?criterio=): o mesmo dos cards de Indicadores. O primeiro é o padrão.
export const RECORTE: ExportOptionDef = {
    key: 'criterio',
    label: 'Recorte',
    choices: [
        { value: 'entrada', label: 'Entradas no período' },
        { value: 'saida', label: 'Saídas no período' },
        { value: 'total', label: 'Total em execução agora' },
    ],
}

export const camposExecucao: ExportGroup[] = [
    {
        group: 'Identificação',
        fields: [
            { slug: 'numero_processo', label: 'Número do Processo' },
            { slug: 'fase', label: 'Fase' },
            { slug: 'subfase', label: 'Subfase' },
            { slug: 'materia', label: 'Matéria' },
            { slug: 'uf', label: 'UF' },
            { slug: 'comarca', label: 'Comarca' },
            { slug: 'vara', label: 'Vara' },
            { slug: 'competencia', label: 'Competência' },
        ],
    },
    {
        group: 'Datas',
        fields: [
            { slug: 'data_distribuicao', label: 'Data de Distribuição' },
            { slug: 'data_execucao', label: 'Data de Execução' },
            { slug: 'ultima_movimentacao', label: 'Última Movimentação' },
            { slug: 'data_transito_julgado', label: 'Data de Trânsito em Julgado' },
            { slug: 'data_encerramento', label: 'Data de Encerramento' },
            { slug: 'data_expedicao_alvara', label: 'Data da Expedição do Alvará' },
            { slug: 'data_saida', label: 'Data de Saída (Compensação do Alvará)' },
        ],
    },
    {
        group: 'Valores',
        fields: [
            { slug: 'valor_causa', label: 'Valor de Causa (R$)' },
            { slug: 'dano_material', label: 'Dano Material (R$)' },
            { slug: 'dano_moral', label: 'Dano Moral (R$)' },
            { slug: 'valor_execucao', label: 'Valor de Execução (R$)' },
            { slug: 'dano_material_execucao', label: 'Dano Material Execução (R$)' },
            { slug: 'dano_moral_execucao', label: 'Dano Moral Execução (R$)' },
            { slug: 'valor_honorarios', label: 'Valor de Honorários (R$)' },
            { slug: 'valor_ted', label: 'Valor TED (R$)' },
            { slug: 'valor_multas', label: 'Valor das Multas (R$)' },
            { slug: 'sucumbencia_porcentagem', label: 'Sucumbência (%)' },
            { slug: 'valor_sucumbencia', label: 'Valor da Sucumbência (R$)' },
            { slug: 'valor_alvara', label: 'Valor do Alvará (R$)' },
        ],
    },
    {
        group: 'Incontroverso',
        fields: [
            { slug: 'valor_incontroverso', label: 'Valor Incontroverso (R$)' },
            { slug: 'valor_alvara_incontroverso', label: 'Valor do Alvará do Incontroverso (R$)' },
            { slug: 'data_expedicao_alvara_incontroverso', label: 'Data da Expedição do Alvará do Incontroverso' },
            { slug: 'data_compensacao_alvara_incontroverso', label: 'Data de Compensação do Alvará do Incontroverso' },
            { slug: 'valor_remanescente', label: 'Valor Remanescente (R$)' },
        ],
    },
    {
        group: 'Saída no período',
        fields: [
            { slug: 'tipo_saida_periodo', label: 'Tipo de Saída no Período' },
            { slug: 'valor_saida_periodo', label: 'Valor de Saída no Período (R$)' },
        ],
    },
]

export const execucaoExport: ExportReport[] = [
    { key: null, title: 'Processos', groups: camposExecucao, options: [RECORTE] },
]
