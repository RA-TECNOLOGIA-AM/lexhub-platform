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
            "Diferença entre 'ainda em execução' e 'entrou/saiu no período', entradas e saídas mês a mês, Diligências e a seção de Atividades (Concluídas/Por prazo).",
        dashboards: ['execucao'],
        offices: ['NG', 'LA', 'LARJ'],
    },
    {
        slug: 'acordos',
        title: 'Execução Acordos',
        description:
            'Processos resolvidos por acordo na fase de Execução, com datas e valor próprios (execução, pagamento, valor de alçada final) e Judicial x Extrajudicial.',
        dashboards: ['acordos'],
        offices: ['NG', 'LA', 'LARJ'],
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
    {
        slug: 'julgados-acordaos',
        title: 'Julgados — Acórdãos',
        description:
            'Classificação de mérito do 2º grau, não classificados, motivo das extinções, embargos e reversão, ranking de relatores e o Estudo das Improcedências.',
        dashboards: ['julgados-acordaos'],
        offices: ['NG', 'LA', 'LARJ'],
    },
    {
        slug: 'protocolo-ng',
        title: 'Protocolo — NG e LARJ',
        description:
            'Indicadores, represados, valor de causa, comissão por processo e comissão com Fator Multiplicador por estado.',
        dashboards: ['protocolo'],
        units: ['NG', 'RJ', 'LARJ', 'LA_RJ'],
        offices: ['NG', 'LARJ'],
    },
    {
        slug: 'protocolo-la',
        title: 'Protocolo — LA',
        description: 'Status CONCLUIDO e PROTOCOLO e a comissão escalonada por taxa de resolução.',
        dashboards: ['protocolo'],
        units: ['LA', 'LAAM', 'LA_AM'],
        offices: ['LA'],
    },
    {
        slug: 'pendencias-ng',
        title: 'Pendências — NG e LARJ',
        description: 'Ciclo de vida, indicadores, taxas, reajuizamento e comissionamento.',
        dashboards: ['pendencias'],
        units: ['NG', 'RJ', 'LARJ', 'LA_RJ'],
        offices: ['NG', 'LARJ'],
    },
    {
        slug: 'pendencias-la',
        title: 'Pendências — LA',
        description: 'Lógica própria, com status diferentes do NG e o conceito de resolvido via ORG DOC.',
        dashboards: ['pendencias'],
        units: ['LA', 'LAAM', 'LA_AM'],
        offices: ['LA'],
    },
    {
        slug: 'org-documentos-ng',
        title: 'Organização de Documentos — NG e LARJ',
        description: 'Represados, indicadores do período e comissionamento por valor de causa.',
        dashboards: ['org-documentos'],
        units: ['NG', 'RJ', 'LARJ', 'LA_RJ'],
        offices: ['NG', 'LARJ'],
    },
    {
        slug: 'org-documentos-la',
        title: 'Organização de Documentos — LA',
        description: 'Status próprios, campo PET_AUTO para manual/automático e comissionamento.',
        dashboards: ['org-documentos'],
        units: ['LA', 'LAAM', 'LA_AM'],
        offices: ['LA'],
    },
    {
        slug: 'peticionamento-ng',
        title: 'Peticionamento — NG e LARJ',
        description: 'Filtro especial por DATA_CONFECCAO, manual × automático e comissão por Massa e ESPECIFICA.',
        dashboards: ['peticionamento'],
        units: ['NG', 'RJ', 'LARJ', 'LA_RJ'],
        offices: ['NG', 'LARJ'],
    },
    {
        slug: 'peticionamento-la',
        title: 'Peticionamento — LA',
        description: "Terminologia 'confeccionados', filtro por SAIDA e a métrica de retorno do Protocolo.",
        dashboards: ['peticionamento'],
        units: ['LA', 'LAAM', 'LA_AM'],
        offices: ['LA'],
    },
    {
        slug: 'pendencias-intermediarias-ng',
        title: 'Pendências Intermediárias — NG',
        description:
            'Setor PENDÊNCIA, dilação encaminhada para MANIFESTAÇÃO - ELABORAR DILAÇÃO e as faixas Ouro/Prata/Bronze.',
        dashboards: ['pendencias-intermediarias'],
        units: ['NG', 'RJ', 'LARJ', 'LA_RJ'],
        offices: ['NG'],
    },
    {
        slug: 'pendencias-intermediarias-la',
        title: 'Pendências Intermediárias — LA',
        description: 'Indicadores do período e a Taxa de Dilação com faixas Ouro/Prata/Bronze.',
        dashboards: ['pendencias-intermediarias'],
        units: ['LA', 'LAAM', 'LA_AM'],
        offices: ['LA'],
    },
    {
        slug: 'emendas-manifestacoes-ng',
        title: 'Emendas e Manifestações — NG',
        description: 'Setor menor que o da LA, comissão em valor fixo sem faixa e filtro de UF.',
        dashboards: ['emendas-manifestacoes'],
        units: ['NG', 'RJ', 'LARJ', 'LA_RJ'],
        offices: ['NG'],
    },
    {
        slug: 'emendas-manifestacoes-la',
        title: 'Emendas e Manifestações — LA',
        description: 'Classificação de atividades e comissionamento por faixa de agenda cumprida (85%/97%).',
        dashboards: ['emendas-manifestacoes'],
        units: ['LA', 'LAAM', 'LA_AM'],
        offices: ['LA'],
    },
    {
        slug: 'replicas-la',
        title: 'Réplicas — LA',
        description: 'Taxa de Procedência (1G) e comissionamento fixo de R$ 1,50 por peça concluída.',
        dashboards: ['replicas'],
        offices: ['LA'],
    },
    {
        slug: 'julgados-sentencas',
        title: 'Julgados — Sentenças',
        description:
            'Classificação de mérito do 1º grau, motivo das extinções, tempo médio até a sentença, embargos e reversão, e por que a maioria dos processos não tem juiz preenchido.',
        dashboards: ['julgados-sentencas'],
        offices: ['NG', 'LA', 'LARJ'],
    },
    {
        slug: 'marketing-lexpre',
        title: 'Marketing (LexPre)',
        description:
            'Perfil e triagem dos clientes, Facebook Ads, fechamento de campanhas, análise de aquisição e indicadores do canal pago e orgânico.',
        dashboards: ['marketing-lexpre'],
        offices: ['NG', 'LA'],
    },
    {
        slug: 'marketing-ng',
        title: 'Marketing — NG',
        description:
            'Banco NG legado somado ao LexPre (escritório NG): perfil e triagem com dispositivo, Facebook Ads e funil de pipeline, campanhas RA × NG, aquisição e indicadores pago e orgânico.',
        dashboards: ['marketing'],
        offices: ['NG'],
    },
    {
        slug: 'publicacoes',
        title: 'Publicações',
        description:
            'Recebidas, pendentes e cumpridas, tempo de tratamento, taxa de resolução, agendamento depois do cumprimento e a comissão dos leitores (certas × erradas).',
        dashboards: ['publicacoes'],
        offices: ['NG', 'LA', 'LARJ'],
    },
    {
        slug: 'controle-processos',
        title: 'Controle de Processos',
        description:
            'A esteira da carteira (protocolados, inicial, recursal, trânsito, execução e arquivados), extintos e taxa de provimento, carteira líquida, tempo por fase frente às metas e subfases.',
        dashboards: ['controle-processos'],
        offices: ['NG', 'LA', 'LARJ'],
    },
    {
        slug: 'execucao-estrategico',
        title: 'Execução Estratégico Geral',
        description:
            'Condenação e Acordos somados, filtros de Escopo, UF, Comarca, Matéria e Subfase (também por clique no gráfico) e o Relatório Personalizado. LARJ não tem a seção Confecção CS.',
        dashboards: ['execucao-estrategico'],
        offices: ['NG', 'LA', 'LARJ'],
    },
    {
        slug: 'sobrevivencia-processual',
        title: 'Sobrevivência Processual',
        description:
            'Como cada número é calculado: censura, mediana de Kaplan-Meier, a precedência entre acordo, sentença e acórdão e o estágio de pagamento.',
        dashboards: ['sobrevivencia-processual'],
        offices: ['NG', 'LA'],
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

// Guias de uso do LexHub (como entrar, achar e ler um dashboard...). Não dependem de dashboard:
// todo mundo vê. Ficam no topo do índice, antes dos guias dos dashboards.
export type GuideEntry = {
    slug: string // endereço: /:org/documentacao/:slug (não pode repetir um slug de DOC_ENTRIES)
    title: string
    description: string
}

export const GUIDE_ENTRIES: GuideEntry[] = [
    {
        slug: 'guia-do-usuario',
        title: 'Como usar o LexHub',
        description:
            'Primeiros passos: entrar, escolher a unidade, achar e ler um dashboard, filtrar, exportar e deixar o app do seu jeito.',
    },
    {
        slug: 'api-publica',
        title: 'API pública',
        description:
            'Para Owners, Gestores e Controllers: pedir a chave, gerar e renovar tokens e buscar os dados do Exportar por API (Power BI, planilhas, scripts).',
    },
]

// Título de qualquer guia (de uso ou de dashboard) pelo slug. null = não existe.
export function guideOrDoc(slug: string): { title: string } | null {
    return GUIDE_ENTRIES.find((g) => g.slug === slug) ?? DOC_ENTRIES.find((d) => d.slug === slug) ?? null
}

export type DocGroup = { area: string; docs: DocEntry[] }

// Os guias agrupados pela área do dashboard (a mesma do hub: Comercial, Pré-protocolo, Jurídico...), na ordem
// em que as áreas aparecem no catálogo. Guia de dashboard sem área no catálogo vai para "Outros".
export function groupDocs(docs: DocEntry[], dashboards: { key: string; area: string }[]): DocGroup[] {
    const groups: DocGroup[] = []
    for (const doc of docs) {
        const area = dashboards.find((d) => doc.dashboards.includes(d.key))?.area || 'Outros'
        const group = groups.find((g) => g.area === area)
        if (group) group.docs.push(doc)
        else groups.push({ area, docs: [doc] })
    }
    const order = (area: string) => {
        const i = dashboards.findIndex((d) => d.area === area)
        return i < 0 ? Number.MAX_SAFE_INTEGER : i
    }
    return groups.sort((a, b) => order(a.area) - order(b.area))
}

// Busca do índice: título, descrição ou área contêm o texto (sem diferença de maiúsculas e acentos); e,
// com uma unidade escolhida, só os guias dela.
const fold = (text: string) => text.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()

export function filterDocs(groups: DocGroup[], query: string, office: string | null): DocGroup[] {
    const q = fold(query.trim())
    return groups
        .map((g) => ({
            area: g.area,
            docs: g.docs.filter(
                (d) =>
                    (!office || d.offices.includes(office)) &&
                    (!q || fold(`${d.title} ${d.description} ${g.area}`).includes(q)),
            ),
        }))
        .filter((g) => g.docs.length > 0)
}
