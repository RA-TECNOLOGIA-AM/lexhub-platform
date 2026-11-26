import type { ExportGroup } from '../../../lib/exportFields.ts'
import type { V1GenericoResponse } from '../v1Stats.ts'
import { pendenciasDaLA } from './pendencias.ts'

// Espelha _CAMPOS_EXPORT_PENDENCIAS_NG / _LA e os rótulos de apps/api/src/app/analyses/v1_legado_export.py: os
// mesmos slugs e rótulos. Grupos e ordem: GRUPOS_CAMPOS_NG / _LA da janela da v1 (PendenciasExportDialog.tsx).
// Mudou no servidor? Muda aqui também (legadoExport.test.ts confere).
export const pendenciasExportNG: ExportGroup[] = [
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
        group: 'Pendência',
        fields: [
            { slug: 'status', label: 'Status' },
            { slug: 'origem', label: 'Origem' },
            { slug: 'tipo_pendencia', label: 'Tipo de Pendência' },
            { slug: 'motivo_cancelamento', label: 'Motivo de Cancelamento' },
            { slug: 'id_action', label: 'ID da Ação' },
            { slug: 'id_processo', label: 'ID do Processo' },
            { slug: 'area_atuacao_id', label: 'Área de Atuação (ID)' },
            { slug: 'reajuizamento', label: 'Reajuizamento' },
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

export const pendenciasExportLA: ExportGroup[] = [
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
        group: 'Pendência',
        fields: [
            { slug: 'status', label: 'Status' },
            { slug: 'setor_origem', label: 'Setor de Origem' },
            { slug: 'tipo_pendencia', label: 'Tipo de Pendência' },
            { slug: 'motivo_cancelamento', label: 'Motivo de Cancelamento' },
            { slug: 'action_id', label: 'ID da Ação' },
            { slug: 'processo_id', label: 'ID do Processo' },
            { slug: 'area_atuacao', label: 'Área de Atuação' },
            { slug: 'reajuizamento', label: 'Reajuizamento' },
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
export const pendenciasExport = (data: V1GenericoResponse): ExportGroup[] =>
    pendenciasDaLA(data) ? pendenciasExportLA : pendenciasExportNG
