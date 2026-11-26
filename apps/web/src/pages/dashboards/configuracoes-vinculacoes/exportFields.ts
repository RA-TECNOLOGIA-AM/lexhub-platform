import type { ExportGroup } from '../../../lib/exportFields.ts'

// Espelha COLUNAS de app/dashboards/configuracoes_vinculacoes.py (= _CAMPOS_EXPORT_CONFIGURACOES_VINCULACOES da v1).
// Mudou no servidor? Muda aqui também: a API só aceita os campos da lista dela. O arquivo sai com os filtros da tela.
export const vinculacoesExport: ExportGroup[] = [
    {
        group: 'Vinculação',
        fields: [
            { slug: 'escritorio', label: 'Escritório' },
            { slug: 'status', label: 'Status' },
            { slug: 'vinculacao_ativa', label: 'Vinculação ativa' },
            { slug: 'setor', label: 'Setor' },
            { slug: 'atividade', label: 'Atividade' },
            { slug: 'tem_configuracao', label: 'Tem configuração' },
            { slug: 'configuracao_ativa', label: 'Configuração ativa' },
        ],
    },
    {
        group: 'Gatilhos de fase/subfase',
        fields: [
            { slug: 'fase_agendamento', label: 'Fase no agendamento' },
            { slug: 'subfase_agendamento', label: 'Subfase no agendamento' },
            { slug: 'situacao_agendamento', label: 'Situação no agendamento' },
            { slug: 'fase_conclusao', label: 'Fase na conclusão (cumprido)' },
            { slug: 'subfase_conclusao', label: 'Subfase na conclusão (cumprido)' },
            { slug: 'fase_conclusao_nao_cumprido', label: 'Fase na conclusão (não cumprido)' },
            { slug: 'subfase_conclusao_nao_cumprido', label: 'Subfase na conclusão (não cumprido)' },
            { slug: 'gatilhos_conclusao', label: 'Gatilhos de encerramento por encaminhamento' },
        ],
    },
    {
        group: 'Regras e encerramento',
        fields: [
            { slug: 'campos_obrigatorios', label: 'Campos obrigatórios' },
            { slug: 'outras_configuracoes', label: 'Outras configurações' },
            { slug: 'regra_cumprido', label: 'Regra para cumprido' },
            { slug: 'regra_nao_cumprido', label: 'Regra para não cumprido' },
            { slug: 'proxima_atividade_cumprido', label: 'Próxima atividade (cumprido)' },
            { slug: 'proxima_atividade_nao_cumprido', label: 'Próxima atividade (não cumprido)' },
        ],
    },
    {
        group: 'Problemas',
        fields: [
            { slug: 'qtd_problemas', label: 'Qtd. problemas' },
            { slug: 'problemas', label: 'Problemas encontrados' },
        ],
    },
]
