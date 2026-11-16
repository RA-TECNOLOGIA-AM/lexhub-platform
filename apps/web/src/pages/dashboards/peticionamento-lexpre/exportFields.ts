import type { ExportGroup } from '../../../lib/exportFields.ts'

// Espelha CAMPOS_EXPORT de apps/api/src/app/dashboards/peticionamento_lexpre.py (cópia da v1).
// Mudou no servidor? Muda aqui também: a API só aceita campos da lista dela.
export const peticionamentoExport: ExportGroup[] = [
    {
        group: 'Identificação',
        fields: [
            { slug: 'id_demanda', label: 'ID da Demanda' },
            { slug: 'numero_processo', label: 'Número do Processo' },
            { slug: 'cliente_nome', label: 'Nome do Cliente' },
            { slug: 'funcionario', label: 'Funcionário Responsável' },
        ],
    },
    {
        group: 'Processo',
        fields: [
            { slug: 'materia', label: 'Matéria' },
            { slug: 'situacao', label: 'Situação' },
            { slug: 'status_demanda', label: 'Status da Demanda' },
            { slug: 'setor_atual', label: 'Setor Atual' },
            { slug: 'destino', label: 'Destino' },
            { slug: 'area_atuacao', label: 'Área de Atuação' },
        ],
    },
    {
        group: 'Valores',
        fields: [
            { slug: 'valor_causa', label: 'Valor de Causa (R$)' },
            { slug: 'dano_moral', label: 'Dano Moral (R$)' },
        ],
    },
    {
        group: 'Datas',
        fields: [
            { slug: 'data_entrada', label: 'Data de Entrada' },
            { slug: 'data_saida', label: 'Data de Saída' },
            { slug: 'data_protocolo', label: 'Data de Protocolo' },
        ],
    },
]
