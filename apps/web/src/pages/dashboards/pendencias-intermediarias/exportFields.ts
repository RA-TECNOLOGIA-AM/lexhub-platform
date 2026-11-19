import type { ExportReport } from '../../../lib/exportFields.ts'

// Espelha `_HEADERS_EXPORT_INTERMEDIARIAS` da v1 (as colunas fixas do relatório de Pendências Intermediárias) e a
// `visao` da lista exportada (?visao=, a mesma dos botões Por prazo | Concluídas). Mudou no servidor? Muda aqui
// também: a API só aceita os campos da lista dela (dashboards/pendencias_intermediarias.py).
export const intermediariasExport: ExportReport[] = [
    {
        key: null,
        title: 'Lista de tarefas',
        options: [
            {
                key: 'visao',
                label: 'Lista',
                choices: [
                    { value: 'por_prazo', label: 'Por prazo' },
                    { value: 'concluidas', label: 'Concluídas' },
                ],
            },
        ],
        groups: [
            {
                group: 'Tarefa',
                fields: [
                    { slug: 'id', label: 'ID' },
                    { slug: 'numero_processo', label: 'Nº Processo' },
                    { slug: 'descricao', label: 'Descrição' },
                    { slug: 'operacao', label: 'Operação' },
                    { slug: 'status', label: 'Status' },
                    { slug: 'responsavel', label: 'Responsável' },
                    { slug: 'encerrado_pelo_responsavel', label: 'Encerrado pelo responsável' },
                    { slug: 'setor_atividade', label: 'Setor / Atividade' },
                    { slug: 'atividade', label: 'Atividade' },
                ],
            },
            {
                group: 'Datas e situação',
                fields: [
                    { slug: 'criado_em', label: 'Criado em' },
                    { slug: 'prazo', label: 'Prazo' },
                    { slug: 'em_andamento', label: 'Em andamento' },
                    { slug: 'vencida', label: 'Vencida' },
                    { slug: 'vence_hoje', label: 'Vence hoje' },
                    { slug: 'concluida', label: 'Concluída' },
                ],
            },
        ],
    },
]
