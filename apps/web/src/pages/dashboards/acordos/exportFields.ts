import type { ExportGroup, ExportReport } from '../../../lib/exportFields.ts'
import { RECORTE } from '../execucao/exportFields.ts'

// Espelha `_CAMPOS_EXPORT_EXECUCAO_ACORDOS_NG` e `_CAMPOS_EXPORT_EXECUCAO_ACORDOS_ATIVIDADES_NG` (v1), com os grupos
// da janela da v1 (ExecucaoAcordosExportDialog): os processos (com o recorte) e as atividades da seção (com a
// visão Concluídas / Por prazo). Mudou no servidor? Muda aqui também (dashboards/execucao_export.py).

export const camposProcessos: ExportGroup[] = [
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
            { slug: 'data_acordo_fechado', label: 'Data de Acordo Fechado' },
            { slug: 'data_acordo_homologado', label: 'Data de Acordo Homologado' },
            { slug: 'data_pagamento_acordo', label: 'Data de Pagamento do Acordo' },
            { slug: 'data_expedicao_alvara_acordo', label: 'Data da Expedição do Alvará de Acordo' },
            { slug: 'data_distribuicao', label: 'Data de Distribuição' },
            { slug: 'data_execucao', label: 'Data de Execução' },
            { slug: 'ultima_movimentacao', label: 'Última Movimentação' },
        ],
    },
    {
        group: 'Valores',
        fields: [
            { slug: 'valor_alcada_final', label: 'Valor de Alçada Final (R$)' },
            { slug: 'valor_proposta_recebida', label: 'Valor de Proposta Recebida (R$)' },
            { slug: 'valor_contraproposta', label: 'Valor de Contraproposta (R$)' },
            { slug: 'valor_alvara', label: 'Valor do Alvará (R$)' },
        ],
    },
]

const camposAtividades: ExportGroup[] = [
    {
        group: 'Identificação',
        fields: [
            { slug: 'numero_processo', label: 'Número do Processo' },
            { slug: 'atividade', label: 'Atividade' },
            { slug: 'status', label: 'Status' },
            { slug: 'situacao', label: 'Situação' },
        ],
    },
    {
        group: 'Responsáveis',
        fields: [
            { slug: 'funcionario', label: 'Responsável Atual' },
            { slug: 'funcionario_atribuido', label: 'Funcionário Atribuído' },
            { slug: 'funcionario_encerramento', label: 'Funcionário que Encerrou' },
        ],
    },
    {
        group: 'Datas',
        fields: [
            { slug: 'prazo', label: 'Prazo' },
            { slug: 'criado_em', label: 'Criado em' },
        ],
    },
    {
        group: 'Detalhes',
        fields: [
            { slug: 'descricao', label: 'Descrição' },
            { slug: 'operacao', label: 'Operação' },
        ],
    },
]

export const acordosExport: ExportReport[] = [
    { key: null, title: 'Processos', groups: camposProcessos, options: [RECORTE] },
    {
        key: 'atividades',
        title: 'Atividades',
        groups: camposAtividades,
        options: [
            {
                key: 'view',
                label: 'Visão das atividades',
                choices: [
                    { value: 'concluidas', label: 'Concluídas' },
                    { value: 'por_prazo', label: 'Por prazo' },
                ],
            },
        ],
    },
]
