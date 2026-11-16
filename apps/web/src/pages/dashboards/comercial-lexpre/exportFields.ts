import type { ExportGroup } from '../../../lib/exportFields.ts'

// Espelha `_CAMPOS_EXPORT_COMERCIAL_LEXPRE_NG` (api_dashboards/src/app/dashboard_routes.py, v1): as colunas da
// query comercial_lexpre_NG. Mudou no servidor? Muda aqui também: a API só aceita campos da lista dela.
export const comercialExport: ExportGroup[] = [
    {
        group: 'Atendimento',
        fields: [
            { slug: 'id_action', label: 'ID do Atendimento' },
            { slug: 'cliente', label: 'Nome do Cliente' },
            { slug: 'atendente', label: 'Atendente' },
            { slug: 'uf', label: 'UF' },
            { slug: 'canal_aquisicao', label: 'Canal de Aquisição' },
            { slug: 'motivo_encerramento', label: 'Motivo de Encerramento' },
        ],
    },
    {
        group: 'Contrato',
        fields: [
            { slug: 'rubrica', label: 'Rubrica' },
            { slug: 'area_atuacao', label: 'Área de Atuação' },
            { slug: 'valor_am', label: 'Valor (R$)' },
        ],
    },
    {
        group: 'Demanda',
        fields: [
            { slug: 'status_demanda', label: 'Status da Demanda' },
            { slug: 'valor_causa', label: 'Valor de Causa (R$)' },
            { slug: 'numero_processo', label: 'Número do Processo' },
            { slug: 'setor', label: 'Setor' },
        ],
    },
    {
        group: 'Datas',
        fields: [
            { slug: 'assinatura', label: 'Data de Assinatura' },
            { slug: 'data_protocolo', label: 'Data de Protocolo' },
        ],
    },
]
