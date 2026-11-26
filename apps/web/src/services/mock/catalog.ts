import type { DashboardCatalog, DashboardSummary } from '../../types/index.ts'
import { minAgo } from './helpers.ts'

// Unidades mais usadas, para não repetir a lista em cada dashboard.
const ALL = ['NG', 'LA_AM', 'LA_RJ']
const NG_AM = ['NG', 'LA_AM']

type EntryParams = {
    key: string
    title: string
    area: string
    desc: string
    units: string[]
    source?: string // padrão: LexPre
    syncedMin?: number // há quantos minutos sincronizou (padrão: 4)
    maxDelayMin?: number // passou disso = "Fonte atrasada" (padrão: 60)
}

// Módulo: monta uma entrada do catálogo. Só o que muda vem por parâmetro; o resto tem padrão.
function entry({ source = 'LexPre', syncedMin = 4, maxDelayMin = 60, ...d }: EntryParams): DashboardSummary {
    // Mock: o usuário de teste é controller, que exporta e vê comissão em todos os setores.
    return {
        ...d,
        source,
        synced_at: minAgo(syncedMin),
        max_delay_min: maxDelayMin,
        can_export: true,
        can_see_commission: true,
    }
}

// Catálogo que a API devolveria para o usuário logado (app.my_dashboards()).
// A ordem define a ordem das áreas no hub.
export const catalog: DashboardCatalog = {
    available: [
        // Comercial (pares como na v1: <domínio> = banco NG, <domínio>-lexpre = LexPre)
        entry({
            key: 'comercial',
            title: 'Comercial',
            area: 'Comercial',
            desc: 'Atendimentos, contratos fechados e conversão.',
            units: ['NG'],
            source: 'NG',
            syncedMin: 8,
        }),
        entry({
            key: 'comercial-lexpre',
            title: 'Comercial (LexPre)',
            area: 'Comercial',
            desc: 'Atendimentos, contratos fechados e conversão.',
            units: ALL,
            syncedMin: 8,
        }),
        entry({
            key: 'comissao',
            title: 'Comissão Comercial',
            area: 'Comercial',
            desc: 'Comissão por atendente e por rubrica.',
            units: ['NG'],
            source: 'NG',
            syncedMin: 8,
        }),
        entry({
            key: 'comissao-lexpre',
            title: 'Comissão Comercial (LexPre)',
            area: 'Comercial',
            desc: 'Comissão por atendente e por rubrica.',
            units: NG_AM,
            syncedMin: 8,
        }),
        entry({
            key: 'marketing',
            title: 'Marketing',
            area: 'Comercial',
            desc: 'Leads e canais de origem.',
            units: ['NG'],
            source: 'NG',
            syncedMin: 60,
            maxDelayMin: 120,
        }),
        entry({
            key: 'marketing-lexpre',
            title: 'Marketing (LexPre)',
            area: 'Comercial',
            desc: 'Leads e canais de origem.',
            units: NG_AM,
            syncedMin: 60,
            maxDelayMin: 120,
        }),
        entry({
            key: 'nps',
            title: 'NPS',
            area: 'Comercial',
            desc: 'Satisfação dos clientes.',
            units: NG_AM,
            syncedMin: 180,
        }),

        // Pré-protocolo (o geral primeiro, depois cada setor)
        entry({
            key: 'pre-protocolo',
            title: 'Pré-protocolo',
            area: 'Pré-protocolo',
            desc: 'Processos em preparação para o protocolo.',
            units: ALL,
            syncedMin: 6,
        }),
        entry({
            key: 'protocolo',
            title: 'Protocolo',
            area: 'Pré-protocolo',
            desc: 'Métricas de protocolo, represados e comissionamento do setor (banco legado).',
            units: ALL,
            source: 'NG · LA',
        }),
        entry({
            key: 'protocolo-lexpre',
            title: 'Protocolo (LexPre)',
            area: 'Pré-protocolo',
            desc: 'Protocolados, represados e devoluções do setor Protocolo.',
            units: ALL,
        }),
        entry({
            key: 'pendencias',
            title: 'Pendências',
            area: 'Pré-protocolo',
            desc: 'Pendências abertas, resolvidas e tempo de resolução.',
            units: ALL,
            source: 'NG · LA',
        }),
        entry({
            key: 'pendencias-lexpre',
            title: 'Pendências (LexPre)',
            area: 'Pré-protocolo',
            desc: 'Pendências abertas, resolvidas e tempo de resolução.',
            units: ALL,
        }),
        entry({
            key: 'org-documentos',
            title: 'Organização de Documentos',
            area: 'Pré-protocolo',
            desc: 'Documentos organizados e devolvidos.',
            units: ALL,
            source: 'NG · LA',
        }),
        entry({
            key: 'org-documentos-lexpre',
            title: 'Organização de Documentos (LexPre)',
            area: 'Pré-protocolo',
            desc: 'Documentos organizados e devolvidos.',
            units: ALL,
        }),
        entry({
            key: 'peticionamento',
            title: 'Peticionamento',
            area: 'Pré-protocolo',
            desc: 'Peticionados, represados e valor de causa.',
            units: ALL,
            source: 'NG · LA',
        }),
        entry({
            key: 'peticionamento-lexpre',
            title: 'Peticionamento (LexPre)',
            area: 'Pré-protocolo',
            desc: 'Peticionados, represados e valor de causa.',
            units: ALL,
        }),

        // Jurídico
        entry({
            key: 'execucao',
            title: 'Execução Condenação',
            area: 'Jurídico',
            desc: 'Processos em execução da condenação: entradas, saídas, valores e alvarás.',
            units: ALL,
            source: 'LexFlow',
            syncedMin: 6,
        }),
        entry({
            key: 'acordos',
            title: 'Execução Acordos',
            area: 'Jurídico',
            desc: 'Acordos em execução: fechamento, entradas, pagamentos e valores.',
            units: ALL,
            source: 'LexFlow',
            syncedMin: 6,
        }),
        entry({
            key: 'recursal',
            title: 'Recursal',
            area: 'Jurídico',
            desc: 'Estoque e entradas na fase recursal, decisões 1º × 2º grau, magistrados e atividades do setor.',
            units: ALL,
            source: 'LexFlow',
            syncedMin: 6,
        }),
        entry({
            key: 'julgados-sentencas',
            title: 'Julgados Sentenças',
            area: 'Jurídico',
            desc: 'Resultados de sentença (1º grau) no período.',
            units: ALL,
            source: 'LexFlow',
            syncedMin: 6,
        }),
        entry({
            key: 'publicacoes',
            title: 'Publicações',
            area: 'Jurídico',
            desc: 'Publicações recebidas, tratadas e pendentes, por leitor, matéria e tribunal, e o agendamento depois.',
            units: ALL,
            source: 'LexFlow',
            syncedMin: 6,
        }),
        entry({
            key: 'pendencias-intermediarias',
            title: 'Pendências Intermediárias',
            area: 'Jurídico',
            desc: 'Agendamentos do setor de Pendências: por prazo e concluídas, dilações de prazo, demandas por funcionário e a lista de tarefas.',
            units: ALL,
            source: 'LexFlow',
            syncedMin: 6,
        }),
        entry({
            key: 'emendas-manifestacoes',
            title: 'Emendas e Manifestações',
            area: 'Jurídico',
            desc: 'Emendas, manifestações e dilações: agenda cumprida, peças por funcionário, comissão e a lista de tarefas.',
            units: ALL,
            source: 'LexFlow',
            syncedMin: 6,
        }),
        entry({
            key: 'replicas',
            title: 'Réplicas',
            area: 'Jurídico',
            desc: 'Réplicas por prazo e concluídas, taxa de procedência (1G) dos processos com réplica, demandas por funcionário e a lista de tarefas.',
            units: ALL,
            source: 'LexFlow',
            syncedMin: 6,
        }),
        entry({
            key: 'controle-processos',
            title: 'Controle de Processos',
            area: 'Jurídico',
            desc: 'Esteira de trabalho (protocolados, inicial, recursal, execução e arquivados), extintos, permanência por fase e subfases.',
            units: ALL,
            source: 'LexFlow',
            syncedMin: 6,
        }),
        entry({
            key: 'julgados-acordaos',
            title: 'Julgados Acórdãos',
            area: 'Jurídico',
            desc: 'Resultados de acórdão (2º grau) no período.',
            units: ALL,
            source: 'LexFlow',
            syncedMin: 6,
        }),

        // Tecnologia
        entry({
            key: 'tickets',
            title: 'Tickets',
            area: 'Tecnologia',
            desc: 'Chamados de suporte do Discord: fila, SLA, categorias e servidores.',
            units: ['NG'],
            source: 'NG',
            syncedMin: 5,
        }),

        // Financeiro
        entry({
            key: 'despesas',
            title: 'Despesas',
            area: 'Financeiro',
            desc: 'Contas a pagar e a receber.',
            units: ['Consolidado'],
            source: 'Conta Azul',
            syncedMin: 12,
        }),

        // Estratégico
        // Estratégico Geral: dashboard da organização (só Owner e Desenvolvedor), uma tela com as 3 unidades.
        {
            ...entry({
                key: 'estrategico-geral',
                title: 'Estratégico Geral',
                area: 'Estratégico',
                desc: 'NG, LAAM e LARJ juntas: a visão estratégica de todas as unidades.',
                units: ALL,
                source: 'Várias fontes',
                syncedMin: 10,
            }),
            scope: 'org',
        },
        entry({
            key: 'estrategico',
            title: 'Estratégico',
            area: 'Estratégico',
            desc: 'Comercial, protocolo e jurídico da unidade: contratos e ações fechadas, represados, protocolados, valor de causa e o avanço nas fases.',
            units: ALL,
            source: 'LexFlow, legado e LexPre',
            syncedMin: 10,
        }),
        entry({
            key: 'execucao-estrategico',
            title: 'Execução Estratégico Geral',
            area: 'Estratégico',
            desc: 'Condenação e acordos juntos: estoque, entradas, saídas, valores, Confecção CS e alvarás.',
            units: ALL,
            source: 'LexFlow',
            syncedMin: 6,
        }),
        entry({
            key: 'sobrevivencia-processual',
            title: 'Sobrevivência Processual',
            area: 'Estratégico',
            desc: 'Tempo até mérito, acordo e pagamento (Kaplan-Meier) e os gargalos por matéria, comarca e competência.',
            units: NG_AM,
            source: 'LexFlow',
            syncedMin: 6,
        }),
        entry({
            key: 'previsao-individualizada',
            title: 'Previsão Individualizada',
            area: 'Estratégico',
            desc: 'Tempo previsto até mérito/acordo e pagamento, chance de procedência e de acordo para uma combinação de processo (modelo XGBoost-AFT do estudo do TCC).',
            units: NG_AM,
            source: 'LexFlow',
            syncedMin: 6,
        }),
        entry({
            key: 'configuracoes-vinculacoes',
            title: 'Configurações das Vinculações',
            area: 'Estratégico',
            desc: 'Auditoria das vinculações (setor + atividade) do LexFlow: fluxos de cumprido e não cumprido, gatilhos de fase/subfase e o que falta configurar.',
            units: ALL,
            source: 'LexFlow',
            syncedMin: 6,
        }),
        entry({
            key: 'financeiro-estrategico',
            title: 'Financeiro Estratégico',
            area: 'Financeiro',
            desc: 'Receita, valor protocolado, conversão, evolução e previsão.',
            units: NG_AM,
            source: 'Planilha do financeiro + LexFlow',
            syncedMin: 30,
            maxDelayMin: 120,
        }),
        entry({
            key: 'meta-anual',
            title: 'Meta anual',
            area: 'Financeiro',
            desc: 'Faturamento do ano contra as metas, por trimestre, e análise preditiva.',
            units: NG_AM,
            source: 'Planilha do financeiro',
            syncedMin: 60,
            maxDelayMin: 120,
        }),
    ],
    // Todos viraram cards; a seção "Chegando na V2" fica vazia.
    upcoming: [],
}
