import type { ExportGroup } from '../../../lib/exportFields.ts'
import type { V1GenericoResponse } from '../v1Stats.ts'
import { lerProtocolo } from './protocolo.ts'

// Espelha _CAMPOS_EXPORT_PROTOCOLO_NG / _LA e os rótulos de apps/api/src/app/analyses/v1_legado_export.py: os
// mesmos slugs e rótulos. Grupos e ordem: GRUPOS_CAMPOS_NG / _LA da janela da v1 (ProtocoloExportDialog.tsx).
// Mudou no servidor? Muda aqui também (legadoExport.test.ts confere).
export const protocoloExportNG: ExportGroup[] = [
    {
        group: 'Identificação',
        fields: [
            { slug: 'nome', label: 'Nome do Cliente' },
            { slug: 'atendente', label: 'Atendente Comercial' },
            { slug: 'funcionario', label: 'Funcionário Responsável' },
            { slug: 'uf', label: 'UF' },
        ],
    },
    {
        group: 'Processo',
        fields: [
            { slug: 'status', label: 'Status' },
            { slug: 'materia', label: 'Matéria' },
            { slug: 'parte_adversa', label: 'Parte Adversa' },
            { slug: 'sistema', label: 'Sistema' },
            { slug: 'campanha', label: 'Campanha' },
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
            { slug: 'dano_material', label: 'Dano Material (R$)' },
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

export const protocoloExportLA: ExportGroup[] = [
    {
        group: 'Identificação',
        fields: [
            { slug: 'nome', label: 'Nome do Cliente' },
            { slug: 'atendente', label: 'Atendente Comercial' },
            { slug: 'funcionario', label: 'Funcionário Responsável' },
            { slug: 'uf', label: 'UF' },
        ],
    },
    {
        group: 'Processo',
        fields: [
            { slug: 'status', label: 'Status' },
            { slug: 'materia', label: 'Matéria' },
            { slug: 'parte_adversa', label: 'Parte Adversa' },
            { slug: 'sistema', label: 'Sistema' },
            { slug: 'action_id', label: 'ID da Ação' },
            { slug: 'processo_id', label: 'ID do Processo' },
            { slug: 'area_atuacao', label: 'Área de Atuação' },
            { slug: 'reajuizamento', label: 'Reajuizamento' },
        ],
    },
    {
        group: 'Valores',
        fields: [
            { slug: 'valor_causa', label: 'Valor de Causa (R$)' },
            { slug: 'dano_moral', label: 'Dano Moral (R$)' },
            { slug: 'dano_material', label: 'Dano Material (R$)' },
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
export const protocoloExport = (data: V1GenericoResponse): ExportGroup[] =>
    lerProtocolo(data).la ? protocoloExportLA : protocoloExportNG
