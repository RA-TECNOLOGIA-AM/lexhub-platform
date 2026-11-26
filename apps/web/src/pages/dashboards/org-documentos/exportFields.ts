import type { ExportGroup } from '../../../lib/exportFields.ts'
import type { V1GenericoResponse } from '../v1Stats.ts'
import { lerOrgDocumentos } from './orgDocumentos.ts'

// Espelha _CAMPOS_EXPORT_ORG_DOC_NG / _LA e os rótulos de apps/api/src/app/analyses/v1_legado_export.py: os
// mesmos slugs e rótulos. Grupos e ordem: GRUPOS_CAMPOS_NG / _LA da janela da v1 (OrgDocExportDialog.tsx).
// Mudou no servidor? Muda aqui também (legadoExport.test.ts confere).
export const orgDocumentosExportNG: ExportGroup[] = [
    {
        group: 'Identificação',
        fields: [
            { slug: 'nome', label: 'Nome do Cliente' },
            { slug: 'atendente_comercial', label: 'Atendente Comercial' },
            { slug: 'funcionario', label: 'Funcionário Responsável' },
            { slug: 'uf', label: 'UF' },
        ],
    },
    {
        group: 'Processo',
        fields: [
            { slug: 'origem', label: 'Origem' },
            { slug: 'status', label: 'Status' },
            { slug: 'materia', label: 'Matéria' },
            { slug: 'id_action', label: 'ID da Ação' },
            { slug: 'id_processo', label: 'ID do Processo' },
            { slug: 'area_atuacao_id', label: 'Área de Atuação (ID)' },
            { slug: 'reajuizamento', label: 'Reajuizamento' },
        ],
    },
    {
        group: 'Valores',
        fields: [
            { slug: 'valor_da_causa', label: 'Valor de Causa (R$)' },
            { slug: 'dano_moral', label: 'Dano Moral (R$)' },
        ],
    },
    {
        group: 'Datas',
        fields: [
            { slug: 'data_contratacao', label: 'Data de Contratação' },
            { slug: 'entrada', label: 'Data de Entrada' },
            { slug: 'saida', label: 'Data de Saída' },
        ],
    },
]

export const orgDocumentosExportLA: ExportGroup[] = [
    {
        group: 'Identificação',
        fields: [
            { slug: 'nome', label: 'Nome do Cliente' },
            { slug: 'atendente_comercial', label: 'Atendente Comercial' },
            { slug: 'funcionario', label: 'Funcionário Responsável' },
            { slug: 'uf', label: 'UF' },
        ],
    },
    {
        group: 'Processo',
        fields: [
            { slug: 'setor_origem', label: 'Setor de Origem' },
            { slug: 'status', label: 'Status' },
            { slug: 'materia', label: 'Matéria' },
            { slug: 'action_id', label: 'ID da Ação' },
            { slug: 'processo_id', label: 'ID do Processo' },
            { slug: 'area_atuacao', label: 'Área de Atuação' },
            { slug: 'reajuizamento', label: 'Reajuizamento' },
            { slug: 'pet_auto', label: 'Petição Automática' },
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
            { slug: 'data_contratacao', label: 'Data de Contratação' },
            { slug: 'entrada', label: 'Data de Entrada' },
            { slug: 'saida', label: 'Data de Saída' },
        ],
    },
]

// A lista da unidade da resposta: LA (banco LA) ou NG/RJ, como a janela da v1 (office === 'LA').
export const orgDocumentosExport = (data: V1GenericoResponse): ExportGroup[] =>
    lerOrgDocumentos(data).la ? orgDocumentosExportLA : orgDocumentosExportNG
