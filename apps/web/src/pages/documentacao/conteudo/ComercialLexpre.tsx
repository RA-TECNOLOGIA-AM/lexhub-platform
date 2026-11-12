import {
    Code,
    DashLink,
    DocCard,
    DocGrid,
    DocLink,
    DocPage,
    DocSection,
    InfoBox,
    MetricCard,
    type TocItem,
} from '../components/DocParts.tsx'

// Guia do Comercial (LexPre). Texto da v1: LexHub/src/pages/documentacao/Comercial_Lexpre.tsx.

const TOC: TocItem[] = [
    { id: 'como-funciona', label: 'Como funciona' },
    { id: 'meta-anual', label: 'Meta Anual' },
    { id: 'captacao', label: 'Captação por Origem' },
    { id: 'performance', label: 'Leads e performance' },
    { id: 'protocolos', label: 'Protocolos' },
    { id: 'distribuicao', label: 'Distribuição por Rubrica' },
    { id: 'meta-atendente', label: 'Meta por Atendente' },
    { id: 'filtros', label: 'Filtros' },
    { id: 'limitacoes', label: 'Diferenças para o legado' },
]

const FILTERS = [
    {
        name: 'Período',
        desc: 'Filtra a maioria dos cards pela data de assinatura do atendimento — os cards de Protocolo usam a data de protocolo da demanda, não a de assinatura.',
    },
    {
        name: 'Funcionários',
        desc: "Restringe a visão a um ou mais atendentes — pelo filtro no topo da página ou clicando num gráfico 'por atendente' (Ranking, Fila de Pré-Protocolo, Valor de Causa).",
    },
    {
        name: 'Área de atuação',
        desc: 'Filtra pela área de atuação vinculada à rubrica da demanda (via public.area_atuacao) — hoje só existe CONSUMIDOR; ADMINISTRATIVO aparece quando novas operações forem cadastradas.',
    },
    {
        name: 'UF',
        desc: 'Filtra pela UF do cliente (customer.uf) — catálogo único reaproveitado por todos os dashboards lexpre.',
    },
    {
        name: 'Rubrica',
        desc: "Clicar numa fatia do gráfico 'Distribuição por Rubrica' filtra a página inteira por aquela rubrica.",
    },
]

export function ComercialLexpreDoc() {
    return (
        <DocPage
            title="Comercial (LexPre)"
            tags={['NG', 'LA']}
            note="Banco lexpre — base nova, em construção"
            toc={TOC}
            intro={
                <>
                    Este guia explica cada número e gráfico do dashboard Comercial a partir da nova base de dados (banco{' '}
                    <Code>lexpre</Code>), a partir das tabelas <Code>public.atendimento</Code> e{' '}
                    <Code>public.demandas</Code> — diferente dos outros dashboards lexpre (Pendências, Organização de
                    Documentos, Peticionamento, Protocolo), que partem do log de movimentação de setor. Nenhum
                    conhecimento técnico é necessário.
                </>
            }
            header={
                <InfoBox>
                    Este guia vale para o <DashLink dashboard="comercial-lexpre">Comercial (LexPre)</DashLink> em todas
                    as unidades (troque a unidade no seletor da barra lateral). Mesma query, mesma fórmula de comissão
                    (documentada no <DocLink to="comissao-lexpre">dashboard irmão Comissão Comercial</DocLink>) e as
                    mesmas regras descritas abaixo — a única diferença de negócio real entre as duas versões é a{' '}
                    <strong>Meta por Atendente</strong> (ver seção própria: R$12mi/trimestre no NG, R$15mi/trimestre no
                    LA). No mais, a única coisa que muda é o escritório (<Code>escritorio_id</Code>) pelo qual os dados
                    são filtrados — cada escritório tem seu próprio bloco de <Code>setor_id</Code> no log de
                    movimentação usado pelos outros dashboards lexpre, mas aqui a filtragem por escritório já vem direto
                    de <Code>atendimento.escritorio_id</Code>.
                </InfoBox>
            }
        >
            <DocSection
                id="como-funciona"
                title="Como o dashboard funciona"
                subtitle="Origem, fluxo de atendimento e comissão embutida"
                icon="db"
            >
                <InfoBox>
                    Diferente dos outros dashboards lexpre, o Comercial parte de <Code>public.atendimento</Code> (um
                    atendimento por cliente, com data de assinatura, canal de origem, escritório e UF) e de{' '}
                    <Code>public.demandas</Code> (cada demanda/ação vinculada a um atendimento, com rubrica, valor de
                    causa, status de protocolo e cancelamento). A maioria dos cards filtra por{' '}
                    <strong>data de assinatura</strong> do atendimento (Seção 01), mas os cards de protocolo (Seção 03)
                    usam a <strong>data de protocolo</strong> da demanda — por isso um cliente pode aparecer em "Total
                    Contratos" num mês e só entrar em "Protocolados" num mês diferente.
                </InfoBox>
                <DocCard title='Comissão vem "de brinde" nessa mesma consulta'>
                    <p>
                        O endpoint que alimenta este dashboard já calcula, junto com as métricas comerciais, todos os
                        campos de comissão (comissão base, Fator Multiplicador, proporcionais por estado, desconto de
                        cancelamento tardio) — é a mesma resposta consumida pelo dashboard{' '}
                        <DocLink to="comissao-lexpre">Comissão Comercial (LexPre)</DocLink>, que só exibe esses campos
                        numa página separada. Não há chamada nem cálculo duplicado entre os dois.
                    </p>
                </DocCard>
            </DocSection>

            <DocSection
                id="meta-anual"
                title="Meta Anual"
                subtitle="Progresso do valor de causa protocolado contra a meta do ano"
                icon="trendingUp"
            >
                <MetricCard
                    name="Valor de Causa Protocolado (LexPre) vs. Meta Anual"
                    icon="trendingUp"
                    what="O quanto já foi protocolado neste ano, contra a meta anual da empresa."
                    counts="Soma do valor de causa de todas as demandas protocoladas no ano corrente, tanto no banco lexpre quanto no banco legado (ng)."
                    calc={
                        <>
                            O card soma dois valores: o protocolado no <strong>lexpre</strong> (dados novos,
                            pós-migração) e o protocolado no <strong>legado</strong> — banco <Code>ng</Code> para o NG,
                            e <Code>protocolo_LA</Code> para o LA. Ambos os lados usam o ano fixo em 2026, sem filtro de
                            período — é sempre o ano inteiro.
                        </>
                    }
                    interpret="Mostra o progresso real da empresa contra a meta, já que os dados de protocolado de 2026 estão divididos entre as duas bases (a migração pro lexpre não aconteceu de uma vez para todas as demandas)."
                    caveat="Meta em R$270 milhões — mesmo valor para NG e LA, confirmado com o usuário em 22/09/2026 (constante no frontend, não vem do backend)."
                />
                <InfoBox>
                    Adicionado em 21/09/2026 (Meta Anual) e ampliado no mesmo dia para a{' '}
                    <a className="doc-link" href="#meta-atendente">
                        Meta por Atendente
                    </a>
                    . O card não quebra a soma em "R$X lexpre + R$Y legado" — mostra só o total combinado.
                </InfoBox>
            </DocSection>

            <DocSection
                id="captacao"
                title="Captação por Origem"
                subtitle="Clientes que assinaram contrato no período, por canal"
                icon="grid"
            >
                <InfoBox>
                    Cada canal (Campanha, Redes Sociais, Retorno, Resgate, Indicação, Site, Parceiros, Externos) mostra
                    quantos clientes assinaram contrato originados daquele canal, no período selecionado — clicar num
                    card filtra a página inteira por esse segmento (o mesmo clique de novo remove o filtro). "Campanha"
                    não distingue mais Campanha RA/NG (a Campanha RA está sendo descontinuada), e "Externos" é um card
                    separado de "Parceiros" — não são mais somados juntos como no legado.
                </InfoBox>
                <DocGrid>
                    <MetricCard
                        name="Total Contratos"
                        icon="grid"
                        what="Soma de todos os contratos assinados no período, de todas as origens."
                        counts="Contagem de atendimentos com data de assinatura dentro do período, somando Campanha + Indicação + Retorno + Resgate + Redes Sociais + Site + Parceiros + Externos."
                        calc="Contagem direta, sem filtro de canal."
                        interpret="Visão consolidada da captação comercial no período."
                    />
                    <MetricCard
                        name="Ações Fechadas"
                        icon="grid"
                        what="Total de demandas (ações) fechadas no período, de clientes que assinaram contrato."
                        counts="Demandas de atendimentos assinados no período, excluindo as canceladas. O subtítulo mostra quantas dessas são 'rubricas reunidas' (pacotes que agrupam várias rubricas associadas, ex.: RUBRICAS_BRADESCO)."
                        calc="Contagem direta das demandas não canceladas."
                        interpret="Quanto maior, mais volume de trabalho jurídico gerado pela captação do período."
                        caveat="O lexpre ainda não modela reajuizamento — diferente do dashboard Comercial NG legado, este card não desconta reajuizamentos."
                    />
                    <MetricCard
                        name="Cancelados"
                        icon="grid"
                        what="Demandas canceladas no período, de clientes que assinaram contrato."
                        counts="Contagem de demandas (não de atendimentos) com status de cancelamento, dentro do período."
                        calc="Contagem direta — um mesmo cliente pode ter mais de uma demanda, e só uma ser cancelada."
                        interpret="Ajuda a identificar concentração de cancelamento em algum período ou canal."
                    />
                    <MetricCard
                        name="Aproveitamento"
                        icon="grid"
                        what="Quantas ações fecham, em média, por cliente assinado no período."
                        counts="Razão entre Ações Fechadas e Total Contratos do período."
                        calc="Ações Fechadas ÷ Total Contratos — não é percentual, é uma razão (ex.: 1,4 ações por cliente)."
                        interpret="Quanto maior, mais demandas em média cada cliente novo está gerando."
                    />
                </DocGrid>
            </DocSection>

            <DocSection
                id="performance"
                title="Leads e performance"
                subtitle="Funil de conversão e produtividade diária da equipe"
                icon="trendingUp"
            >
                <DocGrid>
                    <MetricCard
                        name="Leads Geral / Leads Campanha"
                        icon="trendingUp"
                        what="Quantidade de leads (atendimentos) que entraram no período, no total e via campanha."
                        counts="Atendimentos com data de entrada dentro do período — Leads Geral inclui todas as origens, Leads Campanha só os vindos de campanha (anúncios pagos)."
                        calc="Contagem direta por data de entrada do atendimento (não de assinatura)."
                        interpret="Base para o funil de conversão em contratos — quanto mais leads, mais material bruto para a equipe trabalhar."
                    />
                    <MetricCard
                        name="Taxa de Leads Geral / Taxa de Leads Campanha"
                        icon="trendingUp"
                        what="Qual fração dos leads do período virou contrato assinado no mesmo período."
                        counts="Leads do período que também têm data de assinatura dentro do mesmo período — a versão 'Campanha' exige que a assinatura tenha sido pela mesma origem."
                        calc="Contratos assinados no período ÷ Leads gerados no período, em percentual."
                        interpret="Indica a eficiência de conversão da equipe (geral) ou da campanha especificamente."
                    />
                </DocGrid>
                <InfoBox>
                    <strong>Ranking de Ações Fechadas:</strong> gráfico de corrida (race chart) por atendente, clicável
                    — filtra a página inteira pelo atendente selecionado. <strong>Ações/Contratos Diários:</strong>{' '}
                    mapas de calor com os 3 atendentes mais ativos do dia, atualizados em tempo real (sem filtro de
                    período).
                </InfoBox>
            </DocSection>

            <DocSection
                id="protocolos"
                title="Protocolos e valor de causa"
                subtitle="Volume protocolado, ticket médio e tempo até a entrada no fluxo"
                icon="check"
            >
                <DocGrid>
                    <MetricCard
                        name="Protocolados"
                        icon="check"
                        what="Quantidade de demandas protocoladas no período."
                        counts="Demandas com data de protocolo preenchida dentro do período selecionado (não a data de assinatura)."
                        calc="Contagem direta."
                        interpret="Volume de demandas que efetivamente avançaram para a etapa de protocolo."
                    />
                    <MetricCard
                        name="Valor de Causa Protocolado / Ticket Médio"
                        icon="check"
                        what="Volume financeiro (em valor de causa) protocolado no período, e a média por demanda."
                        counts="Soma do valor de causa das demandas protocoladas no período; o Ticket Médio divide essa soma pela quantidade de Protocolados."
                        calc="Soma direta / divisão simples."
                        interpret="Mede o volume financeiro que entrou em protocolo, não só a quantidade de processos."
                    />
                    <MetricCard
                        name="Tempo Médio até o Protocolo"
                        icon="check"
                        what="Quantos dias/horas, em média, uma demanda leva da assinatura até o protocolo."
                        counts="Diferença entre a data de assinatura do atendimento e a data de protocolo da demanda, para as demandas protocoladas no período."
                        calc="Média simples das diferenças, em horas (exibido formatado)."
                        interpret="Indicador de velocidade do fluxo pré-protocolo — quanto menor, mais rápido o cliente sai da assinatura e entra no processo."
                        caveat="A demanda não tem data própria de criação no lexpre, então a base de início usada é sempre a data de assinatura do atendimento."
                    />
                    <MetricCard
                        name="Fila de Demandas no Pré-Protocolo / Valor de Causa por Atendente"
                        icon="check"
                        what="Onde estão hoje as demandas não canceladas que ainda não foram protocoladas, por atendente e estágio do fluxo."
                        counts="Demandas não canceladas cujo status de protocolo ainda não foi atingido, classificadas em um bucket (Pendências, Triagem, Não Confeccionado, Não Protocolado, Não Organizado) — mesma lógica reaproveitada do dashboard Protocolo (LexPre)."
                        calc="Gráfico empilhado por atendente e bucket; o segundo gráfico soma o valor de causa dessas mesmas demandas, separando Protocolado x Não Protocolado."
                        interpret="Mostra onde o trabalho pendente está represado no funil — e para quem."
                    />
                </DocGrid>
            </DocSection>

            <DocSection
                id="distribuicao"
                title="Distribuição por Rubrica"
                subtitle="Composição das ações fechadas por rubrica, dentro de cada canal"
                icon="pieChart"
            >
                <MetricCard
                    name="Total de Rubricas (gráfico de pizza)"
                    icon="pieChart"
                    what="Como as ações fechadas do período se distribuem entre as diferentes rubricas."
                    counts="Ações fechadas no período, agrupadas por rubrica — o seletor 'Origem' no cabeçalho do card restringe a mesma pizza a um canal específico (Campanha, Site, etc.) em vez do total."
                    calc="Contagem por rubrica, dentro do recorte de canal escolhido."
                    interpret="Ajuda a identificar quais tipos de ação dominam a captação, e se isso muda por canal."
                    caveat="Clicar numa fatia filtra a PÁGINA INTEIRA por aquela rubrica (não só o gráfico) — o mesmo mecanismo de clique usado nos cards 'por atendente'. Clicar de novo na mesma fatia remove o filtro."
                />
            </DocSection>

            <DocSection
                id="meta-atendente"
                title="Meta por Atendente"
                subtitle="Desempenho individual contra a meta do trimestre/semestre selecionado"
                icon="trendingUp"
            >
                <MetricCard
                    name="Ranking de Meta por Atendente"
                    icon="trendingUp"
                    what="Quanto cada atendente já protocolou de valor de causa, contra a meta do período (trimestre ou semestre) selecionado no card."
                    counts="Valor de causa protocolado por atendente, somando lexpre + legado (mesmo princípio da Meta Anual, mas por atendente e por trimestre/semestre em vez de ano)."
                    calc="Barra de progresso por atendente (protocolado ÷ meta do período), ordenada do maior para o menor percentual atingido — mostra só os 10 primeiros."
                    interpret="Visão individual de quem está perto ou longe da meta, com destaque visual (verde = perto/acima da meta, vermelho = longe)."
                    caveat='A meta do período é DIFERENTE entre NG e LA: R$12 milhões/trimestre (R$24mi/semestre) no NG, R$15 milhões/trimestre (R$30mi/semestre) no LA — confirmado com o usuário em 22/09/2026. O card "Meta Inteligente" logo abaixo usa o mesmo valor trimestral de cada escritório.'
                />
                <InfoBox>
                    <strong>Merge por primeiro nome:</strong> como não existe um id compartilhado entre as tabelas de
                    funcionário do lexpre e do banco legado, a soma lexpre+legado por atendente é feita batendo pelo
                    primeiro nome — dois atendentes diferentes com o mesmo primeiro nome (num banco ou nos dois) teriam
                    os valores somados por engano. Risco conhecido e aceito, já que é o mesmo critério usado hoje dentro
                    de cada banco isoladamente. <strong>Meta Inteligente:</strong> card separado, calcula uma meta
                    sugerida por atendente a partir do histórico de meses anteriores (com stretch goal configurável),
                    distribuindo proporcionalmente a meta global do período.
                </InfoBox>
            </DocSection>

            <DocSection
                id="filtros"
                title="Filtros disponíveis"
                subtitle="Como personalizar a visão do dashboard"
                icon="filter"
            >
                <DocGrid>
                    {FILTERS.map((f) => (
                        <DocCard key={f.name} title={f.name}>
                            <p>{f.desc}</p>
                        </DocCard>
                    ))}
                </DocGrid>
            </DocSection>

            <DocSection
                id="limitacoes"
                title="Diferenças para o dashboard legado (banco ng)"
                subtitle="O que já existe, o que ainda não existe, e por quê"
                icon="alert"
            >
                <DocGrid>
                    <DocCard title="Sem reajuizamento">
                        <p>
                            O lexpre ainda não modela o conceito de reajuizamento nas demandas — o card "Ações Fechadas"
                            não desconta reajuizamentos como o dashboard Comercial NG legado fazia.
                        </p>
                    </DocCard>
                    <DocCard title="Campanha RA descontinuada">
                        <p>
                            O legado distinguia Campanha RA de Campanha NG; essa distinção está sendo descontinuada e o
                            lexpre já trata os dois como um único canal "Campanha".
                        </p>
                    </DocCard>
                    <DocCard title="Meta Anual e Meta por Atendente somam com o legado">
                        <p>
                            Como os dados de 2026 estão divididos entre lexpre e o banco legado (a migração não
                            aconteceu de uma vez para todas as demandas), os dois cards de meta somam os dois lados em
                            vez de mostrar só o protocolado no lexpre — do contrário, o progresso mostrado seria uma
                            fração do real.
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>
        </DocPage>
    )
}
