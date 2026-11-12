// Módulo: quais documentações existem e a que dashboards cada uma se refere, sem React
// (testado em docRegistry.test.ts). O texto de cada uma veio da v1 (LexHub/src/pages/documentacao).
// Dashboard novo na V2 = uma entrada aqui + o conteúdo em conteudo/ (ligado em docPages.tsx).

export type DocEntry = {
    slug: string // endereço: /:org/documentacao/:slug
    title: string
    description: string
    dashboards: string[] // keys dos dashboards da V2 que este guia explica
    units?: string[] // só para estas unidades (ex.: Recursal LA); sem = todas
    offices: string[] // etiquetas do card (como na v1)
}

export const DOC_ENTRIES: DocEntry[] = [
    {
        slug: 'protocolo-lexpre',
        title: 'Protocolo (LexPre)',
        description:
            'Log de movimentação de setor, critério de status Aguardando Despacho Inicial e devoluções para qualquer setor anterior.',
        dashboards: ['protocolo-lexpre'],
        offices: ['NG', 'LA'],
    },
    {
        slug: 'pendencias-lexpre',
        title: 'Pendências (LexPre)',
        description:
            'Log de movimentação de setor, visitas múltiplas ao setor, período por data de entrada e comissionamento por funcionário.',
        dashboards: ['pendencias-lexpre'],
        offices: ['NG', 'LA'],
    },
    {
        slug: 'org-documentos-lexpre',
        title: 'Organização de Documentos (LexPre)',
        description: 'Log de movimentação de setor, represados, retornos, tempo de resolução e comissionamento.',
        dashboards: ['org-documentos-lexpre'],
        offices: ['NG', 'LA'],
    },
    {
        slug: 'peticionamento-lexpre',
        title: 'Peticionamento (LexPre)',
        description:
            'Log de movimentação de setor, represados, retorno de pendências, valor confeccionado e comissionamento por faixas.',
        dashboards: ['peticionamento-lexpre'],
        offices: ['NG', 'LA'],
    },
    {
        slug: 'comercial-lexpre',
        title: 'Comercial (LexPre)',
        description:
            'Captação por origem, leads e performance, protocolos, distribuição por rubrica e meta anual e por atendente somando com o banco legado.',
        dashboards: ['comercial-lexpre'],
        offices: ['NG', 'LA'],
    },
    {
        slug: 'comissao-lexpre',
        title: 'Comissão Comercial (LexPre)',
        description:
            'Mesma consulta do Comercial (LexPre): comissão base, Fator Multiplicador, proporcionais por estado e desconto de cancelamento tardio.',
        dashboards: ['comissao-lexpre'],
        offices: ['NG', 'LA'],
    },
    {
        slug: 'execucao',
        title: 'Execução Condenação',
        description:
            "Diferença entre 'ainda em execução' e 'entrou/saiu no período', entradas por mês com clique para filtrar e a seção de Atividades (Concluídas/Por prazo).",
        dashboards: ['execucao'],
        offices: ['NG', 'LA'],
    },
    {
        slug: 'acordos',
        title: 'Execução Acordos',
        description:
            'Processos resolvidos por acordo na fase de Execução, com datas e valor próprios (acordo fechado, pagamento, valor de alçada final) e Judicial x Extrajudicial.',
        dashboards: ['acordos'],
        offices: ['NG'],
    },
    {
        slug: 'recursal-ng',
        title: 'Recursal — NG',
        description:
            'Estoque e extintos 2º grau, Matriz de Julgamento 1G×2G, Meta de Provimento Mensal e a regra de comissionamento do setor RECURSOS.',
        dashboards: ['recursal'],
        units: ['NG'],
        offices: ['NG'],
    },
    {
        slug: 'recursal-la',
        title: 'Recursal — LA',
        description:
            'Estoque e extintos 2º grau, Matriz de Julgamento 1G×2G, catálogo dinâmico de atividades do setor RECURSOS e o Relatório Personalizado.',
        dashboards: ['recursal'],
        units: ['LA', 'LA_AM'],
        offices: ['LA'],
    },
]

// As documentações que a pessoa vê: só as dos dashboards que ela pode abrir (mesma regra da v1).
// Guia de uma unidade só (ex.: Recursal LA) aparece se o dashboard estiver liberado nessa unidade.
export function visibleDocs(entries: DocEntry[], dashboards: { key: string; units: string[] }[]): DocEntry[] {
    return entries.filter((entry) =>
        dashboards.some(
            (d) => entry.dashboards.includes(d.key) && (!entry.units || d.units.some((u) => entry.units!.includes(u))),
        ),
    )
}

// O guia de um dashboard numa unidade (o atalho "Como ler este dashboard"). null = ainda sem guia.
export function docFor(entries: DocEntry[], dashboard: string, unit: string): DocEntry | null {
    const matches = entries.filter((e) => e.dashboards.includes(dashboard))
    return matches.find((e) => e.units?.includes(unit)) ?? matches.find((e) => !e.units) ?? null
}
