import {
    Code,
    DocCallout,
    DocChange,
    DocChips,
    DocFeature,
    DocGrid,
    DocPage,
    DocPanel,
    DocSection,
    Hl,
    MetricCard,
    type TocItem,
} from '../components/DocParts.tsx'

// Guia trazido da v1: LexHub/src/pages/documentacao/Marketing_Lexpre.tsx (convertido para as peças da V2).
// Os números 01–07 são as seções do próprio dashboard (o texto cita "Seção 03"...); as demais seções usam ícone.

const TOC: TocItem[] = [
    { id: 'como-funciona', label: 'Como funciona' },
    { id: 'perfil', label: '01 · Perfil de Clientes' },
    { id: 'triados', label: '02 · Triados' },
    { id: 'facebook', label: '03 · Facebook Ads' },
    { id: 'fechamento', label: '04 · Fechamento Campanhas' },
    { id: 'aquisicao', label: '05 · Análise de Aquisição' },
    { id: 'performance', label: '06 · Ind. Performance' },
    { id: 'organico', label: '07 · Ind. Orgânico' },
    { id: 'filtros', label: 'Filtros' },
    { id: 'limitacoes', label: 'Diferenças para o legado' },
]

export function MarketingLexpreDoc() {
    return (
        <DocPage
            title="Marketing (LexPre) — NG e LA"
            tags={['NG', 'LA']}
            note={
                <>
                    Banco <Code>lexpre</Code> — base nova, em construção
                </>
            }
            toc={TOC}
            intro={
                <>
                    Este guia explica cada número e gráfico do dashboard de Marketing a partir da nova base de dados
                    (banco <Code>lexpre</Code>): perfil dos clientes, triagem, investimento em anúncios, fechamento das
                    campanhas, rastreio de aquisição e indicadores dos canais pago e orgânico.{' '}
                    <strong>Nenhum conhecimento técnico é necessário.</strong>
                </>
            }
        >
            <DocSection
                id="como-funciona"
                title="Como o dashboard funciona"
                subtitle="De onde vêm os dados e o que é um cliente assinado"
                icon="db"
            >
                <DocGrid cols={2}>
                    <DocFeature title="Perfil de clientes" tone="info" badge="Seções 01 e 02">
                        <p>
                            Atendimentos assinados do lexpre (<Code>public.atendimento</Code>), com os dados do cliente
                            e as respostas da pesquisa socioeconômica (triagem).
                        </p>
                    </DocFeature>
                    <DocFeature title="Comercial" tone="accent" badge="Seções 03 a 07">
                        <p>
                            Atendimentos e demandas do lexpre — a mesma consulta do dashboard Comercial (LexPre). Traz
                            canal de aquisição, campanha, posicionamento, conjunto, criativo, rubrica e valor de causa.
                        </p>
                    </DocFeature>
                    <DocFeature title="Protocolados" tone="ok" badge="Seções 04, 06 e 07">
                        <p>
                            Log de movimentação de setor do lexpre — a mesma fonte e as mesmas regras do dashboard
                            Protocolo (LexPre), para os números baterem entre as duas páginas.
                        </p>
                    </DocFeature>
                    <DocFeature title="Anúncios" tone="violet" badge="Seções 03 e 06">
                        <p>
                            Tabela de Facebook Ads do banco legado (<Code>metrics_ads.facebook_ads</Code>): valor gasto,
                            cliques, pageview e leads do anúncio, por dia.
                        </p>
                    </DocFeature>
                </DocGrid>
                <DocCallout tone="warn" icon="check" title="O que conta como cliente assinado e como campanha?">
                    <p>
                        <strong>Cliente assinado</strong> é o atendimento com status "Assinado" e data de assinatura
                        preenchida — a mesma regra do Comercial (LexPre). O motivo de encerramento <strong>não</strong>{' '}
                        é usado: ele só é preenchido quando o atendimento é encerrado, bem depois da assinatura (em
                        set/2026, só 14 de 172 assinados do NGAM tinham esse campo preenchido).
                    </p>
                    <p>
                        <strong>Campanha</strong> é o canal de aquisição "anúncio" — no lexpre não existe mais a
                        separação Campanha RA x Campanha NG do legado.
                    </p>
                </DocCallout>
            </DocSection>

            <DocSection
                id="perfil"
                title="01 — Perfil de Clientes"
                subtitle="Quem são os clientes assinados que entraram no período"
                badge="Data de entrada"
            >
                <MetricCard
                    icon="users"
                    name="Perfil de Clientes (todos os gráficos da seção)"
                    what="O perfil demográfico e de aquisição dos clientes assinados: idade, gênero, tipo de tráfego, origem, ocupação, faixa salarial e prospecção."
                    counts="Atendimentos assinados do escritório cuja data de entrada está dentro do período."
                    calc={
                        <>
                            Cada gráfico conta os atendimentos por um campo: <strong>Média Idade</strong> calcula a
                            idade pela data de nascimento e agrupa em faixas etárias; <strong>Origem</strong> usa o
                            canal de aquisição; <strong>Ocupação</strong> e <strong>Média Salarial Mensal</strong> vêm
                            das respostas da triagem.
                        </>
                    }
                    interpret="Mostra o perfil típico de quem fecha contrato — útil para ajustar o público das campanhas."
                    caveat="O período desta seção filtra pela data de ENTRADA do atendimento (não pela assinatura), igual ao legado. Ocupação e faixa salarial só aparecem para quem respondeu a triagem."
                />
            </DocSection>

            <DocSection id="triados" title="02 — Triados" subtitle="Clientes que responderam a pesquisa socioeconômica">
                <MetricCard
                    icon="fileText"
                    name="Triados (todos os gráficos da seção)"
                    what="O mesmo perfil da Seção 01, só para os clientes que responderam a triagem, mais moradia e dependentes."
                    counts="Os clientes da Seção 01 com pelo menos uma resposta da pesquisa socioeconômica preenchida."
                    calc="Mesmos agrupamentos da Seção 01; Tipo de Residência e Pessoas Dependentes vêm das respostas da triagem."
                    interpret="Aprofunda o perfil com dados socioeconômicos que só existem para quem passou pela triagem."
                />
            </DocSection>

            <DocSection
                id="facebook"
                title="03 — Facebook Ads"
                subtitle="Investimento, funil do anúncio e origem dos leads"
                badge="LA: anúncios ainda não integrados"
            >
                <DocGrid>
                    <MetricCard
                        icon="dollar"
                        name="Valor Gasto"
                        what="Quanto foi investido em anúncios no período."
                        counts="Soma do valor gasto na tabela de Facebook Ads, pela data do anúncio."
                        calc="Soma direta."
                        interpret="Base de todos os indicadores de custo (CAC, CPL) e retorno (ROAS)."
                        caveat="A tabela de anúncios não informa o escritório. No NG entra a tabela inteira; no LA entram só campanhas com prefixo “[LA]”, que ainda não existem nessa tabela (a conta de anúncios do LA não está integrada). Por isso o LA mostra valor gasto, cliques, pageview, CAC, ROAS e CPL zerados."
                    />
                    <MetricCard
                        icon="users"
                        name="CAC Campanha / CAC Geral"
                        what="Custo de aquisição por cliente."
                        counts="Clientes assinados de campanha (CAC Campanha) ou de campanha + indicação (CAC Geral) cuja data de entrada está no período."
                        calc="Valor Gasto ÷ quantidade desses clientes."
                        interpret="Quanto menor, mais barato está sendo trazer cada cliente."
                    />
                    <MetricCard
                        icon="trendingUp"
                        name="ROAS Campanha / ROAS Geral"
                        what="Retorno do investimento em anúncios, em valor de causa."
                        counts="Valor de causa das demandas protocoladas no período — dos clientes de campanha (ROAS Campanha) ou de todo o escritório (ROAS Geral)."
                        calc="Valor de causa protocolado ÷ Valor Gasto (ex.: 200 = R$200 de causa para cada R$1 investido)."
                        interpret="Quanto maior, mais valor de causa cada real investido gerou."
                        caveat="Aqui o protocolado usa a data de protocolo da demanda; a Seção 04 usa o log de setor do dashboard Protocolo (LexPre). Os valores podem diferir um pouco entre as duas seções."
                    />
                    <MetricCard
                        icon="filter"
                        name="Funil Anúncio"
                        what="Do clique no anúncio até o cliente assinado."
                        counts="Cliques, pageview e leads vêm da tabela de Facebook Ads; Clientes é o total de clientes da Seção 01."
                        calc="Barras proporcionais ao primeiro degrau (Cliques = 100%)."
                        interpret="Mostra onde o funil perde mais gente."
                        caveat="O degrau CLIENTES conta clientes de todos os canais (igual ao legado), não só os vindos do anúncio — para os de campanha, veja o card Clientes de Campanha."
                    />
                    <MetricCard
                        icon="users"
                        name="Clientes de Campanha, Leads, Indicação e Retorno (Ativa/Passiva)"
                        what="Quantos clientes vieram do anúncio e quantos leads entraram por cada origem."
                        counts="Clientes de Campanha: assinados via anúncio pela data de assinatura. Leads: atendimentos pela data de entrada. Indicação/Retorno: leads desses canais, separados pela prospecção (ativa ou passiva)."
                        calc="Contagem de atendimentos distintos."
                        interpret="Compara o volume do canal pago com o das indicações e retornos."
                    />
                    <MetricCard
                        icon="barChart"
                        name="Investimento x Cliques x Leads"
                        what="A evolução diária do investimento e da resposta do anúncio."
                        counts="Por dia do período: valor gasto (barra), leads (barra fina) e cliques (linha)."
                        calc="Soma diária da tabela de Facebook Ads."
                        interpret="Mostra se aumentos de investimento vêm acompanhados de mais cliques e leads."
                    />
                </DocGrid>
            </DocSection>

            <DocSection
                id="fechamento"
                title="04 — Fechamento Campanhas"
                subtitle="Resultado da campanha comparado ao total do escritório"
                tone="ok"
                badge="Campanha × Total"
            >
                <DocCallout tone="info" icon="layers" title="Por que não existe mais Campanha RA × Campanha NG?">
                    <p>
                        No legado esta seção comparava Campanha RA x Campanha NG. No lexpre a campanha é um canal só,
                        então a seção compara <strong>Campanha x Total</strong>: os cards mostram a campanha, e as
                        roscas mostram a fatia da campanha ao lado do total do escritório.
                    </p>
                </DocCallout>
                <DocGrid>
                    <MetricCard
                        icon="check"
                        name="Campanha (com % de conversão)"
                        what="Clientes assinados via campanha e a taxa de conversão dos leads de campanha."
                        counts="Clientes: assinados com canal anúncio, pela data de assinatura. Conversão: esses clientes ÷ leads de campanha que entraram no período."
                        calc="Mesmas funções do Comercial (LexPre) — o número bate com o card Campanha daquele dashboard."
                        interpret="Quantos contratos a campanha fechou e com que eficiência."
                    />
                    <MetricCard
                        icon="dollar"
                        name="Protocolados / Valor de Causa / Ticket Médio"
                        what="O que a campanha já virou em processo protocolado."
                        counts="Demandas protocoladas no período cujo atendimento veio de campanha. Uma demanda conta uma vez, mesmo que seja um pacote de rubricas reunidas."
                        calc="Mesmas regras do dashboard Protocolo (LexPre): a última saída da demanda do setor Protocolo com status “Aguardando Despacho Inicial”, pela data dessa saída. Ticket Médio = Valor de Causa ÷ Protocolados."
                        interpret="Mede o retorno jurídico real da campanha, não só os contratos."
                        caveat="O Total das roscas bate com os cards do dashboard Protocolo (LexPre) no mesmo período (validado em set/2026). Demandas que voltaram ao setor Protocolo depois de protocoladas não contam."
                    />
                    <MetricCard
                        icon="pieChart"
                        name="Rubrica — Campanha / Rubrica — Protocolado"
                        what="Quais rubricas a campanha trouxe e quais já foram protocoladas."
                        counts="Rubrica — Campanha: ações fechadas de clientes de campanha, por rubrica (pacotes de rubricas reunidas contam cada componente). Rubrica — Protocolado: protocolados de campanha, pelo nome da rubrica da demanda."
                        calc="Contagem por rubrica."
                        interpret="Mostra os tipos de ação que a campanha mais gera."
                        caveat="Clicar numa rubrica recorta os números de campanha e orgânico (Seções 04, 06 e 07), exceto Valor Gasto, CAC e ROAS, que vêm da 03. O clique funciona tanto pelo nome do pacote (ex.: RUBRICAS_BRADESCO) quanto pelo de um componente."
                    />
                </DocGrid>
            </DocSection>

            <DocSection
                id="aquisicao"
                title="05 — Análise de Aquisição"
                subtitle="Rastreio dos leads e dos que fecharam contrato"
            >
                <DocGrid cols={2}>
                    <DocFeature title="Trackeamento" tone="info" badge="Data de entrada">
                        <p>
                            Os atendimentos que <strong>entraram</strong> no período. No lexpre não existe uma tabela de
                            trackeamento separada: campanha, posicionamento, conjunto e criativo ficam no próprio
                            atendimento.
                        </p>
                    </DocFeature>
                    <DocFeature title="Fechamento" tone="ok" badge="Mesma turma">
                        <p>
                            Os atendimentos do Trackeamento que <strong>assinaram</strong> — a mesma turma de entrada,
                            como no legado.
                        </p>
                    </DocFeature>
                </DocGrid>
                <MetricCard
                    icon="search"
                    name="Categoria, Posicionamento, Canal de Aquisição e Campanha"
                    what="Por onde os leads chegaram e por onde vieram os que fecharam."
                    counts="Atendimentos do escritório pela data de entrada (Trackeamento) e o subconjunto assinado (Fechamento)."
                    calc={
                        <>
                            <strong>Categoria</strong> padroniza o posicionamento em Stories, Reels ou Feed;{' '}
                            <strong>Posicionamento</strong> agrupa em Facebook, Instagram, Bio, AN ou Threads — as
                            mesmas regras do legado. Campanha mostra as 10 maiores.
                        </>
                    }
                    interpret="Compara o que traz volume de leads com o que realmente fecha contrato."
                    caveat="“(Em branco)” são os leads de retorno, indicação e orgânico, que não passam por anúncio e por isso não têm posicionamento nem campanha."
                />
            </DocSection>

            <DocSection
                id="performance"
                title="06 — Ind. Performance de MKT"
                subtitle="Indicadores consolidados só da campanha (anúncio)"
            >
                <DocPanel>
                    <DocChips
                        label="Reúne, só com o canal anúncio:"
                        items={[
                            { label: 'Valor Gasto · CAC · ROAS ← 03', tone: 'violet' },
                            { label: 'Clientes · % Fechamento · Valor de Causa · Ticket ← 04', tone: 'ok' },
                            { label: 'Rastreio ← 05', tone: 'info' },
                        ]}
                    />
                    <p>
                        Como no legado, esta seção reúne numa só vista números que já aparecem nas seções anteriores;
                        Rubricas é o mesmo dado de “Rubrica — Campanha”.
                    </p>
                </DocPanel>
                <DocGrid>
                    <MetricCard
                        icon="trendingUp"
                        name="Leads / CPL"
                        what="Quantos leads a campanha gerou e quanto custou cada um."
                        counts="Atendimentos com canal anúncio cuja data de entrada está no período."
                        calc="CPL = Valor Gasto ÷ Leads."
                        interpret="Quanto menor o CPL, mais barato está cada lead."
                    />
                    <MetricCard
                        icon="trendingUp"
                        name="Ações / % Aproveitamento"
                        what="Quantas ações a campanha gerou por cliente assinado."
                        counts="Demandas não canceladas de clientes de campanha, pela data de assinatura."
                        calc="Mesma regra do card Ações Fechadas do Comercial (LexPre): um pacote de rubricas reunidas conta uma ação por componente. % Aproveitamento = Ações ÷ Clientes (é uma razão, não um percentual)."
                        interpret="Quanto maior, mais ações cada cliente de campanha está gerando."
                        caveat="Por contar os componentes dos pacotes, o número de ações é bem maior que o de demandas (set/2026 no NG: 312 ações para 138 demandas)."
                    />
                </DocGrid>
            </DocSection>

            <DocSection
                id="organico"
                title="07 — Ind. Orgânico de MKT"
                subtitle="Os mesmos indicadores, para os canais orgânicos"
            >
                <DocChips
                    label="Canais orgânicos:"
                    items={[
                        { label: 'Facebook', tone: 'info' },
                        { label: 'Instagram', tone: 'violet' },
                        { label: 'Site' },
                        { label: 'Google', tone: 'ok' },
                        { label: '“Orgânico” genérico', tone: 'accent' },
                    ]}
                />
                <MetricCard
                    icon="layers"
                    name="Indicadores orgânicos"
                    what="Leads, contratos, ações e valor de causa dos canais orgânicos Facebook, Instagram, Site e Google."
                    counts="Atendimentos desses 4 canais. O Total Leads também inclui os marcados só como “Orgânico”, sem canal específico — mesmo agrupamento do Comercial (LexPre)."
                    calc="Mesmas regras das Seções 04 e 06: leads pela entrada, contratos pela assinatura, ações pela regra do Comercial (LexPre), valor de causa e ticket pela regra do Protocolo (LexPre). % Taxa Fechamento = Contratos ÷ Total Leads."
                    interpret="Compara o desempenho do tráfego orgânico com o da campanha paga."
                    caveat="Hoje nenhum atendimento do lexpre está cadastrado com os canais Facebook, Instagram, Site ou Google — só o “Orgânico” genérico. Os cards por canal ficam zerados até esses canais começarem a ser usados. Retorno e indicação não entram, mesmo com tipo de tráfego “Orgânico” (igual ao legado)."
                />
            </DocSection>

            <DocSection
                id="filtros"
                title="Filtros disponíveis"
                subtitle="Como personalizar e cruzar a visão do dashboard"
                icon="filter"
                tone="info"
            >
                <DocGrid cols={3}>
                    <DocFeature title="Período" badge="Data por seção" badgeTone="accent">
                        <p>
                            Cada seção usa a data que faz sentido para ela: <strong>entrada</strong> do atendimento
                            (perfil, leads, rastreio), <strong>assinatura</strong> (clientes, ações),{' '}
                            <Hl tone="ok">protocolo</Hl> (protocolados) e data do anúncio (Facebook Ads).
                        </p>
                    </DocFeature>
                    <DocFeature title="Perfil" badge="Seções 01 e 02" badgeTone="info">
                        <p>
                            Clicar em faixa etária, gênero, origem, tipo de tráfego, ocupação, prospecção, tipo de
                            residência ou pessoas dependentes filtra os gráficos de perfil.
                        </p>
                    </DocFeature>
                    <DocFeature title="Rubrica" badge="Seções 04, 06 e 07" badgeTone="ok">
                        <p>
                            Clicar numa rubrica recorta os números de campanha e orgânico — não mexe no perfil, nos
                            anúncios nem em Valor Gasto/CAC/ROAS, igual ao legado.
                        </p>
                    </DocFeature>
                    <DocFeature title="Rastreio" badge="Seções 05, 06 e 07" badgeTone="violet">
                        <p>
                            Clicar em categoria, posicionamento, canal, campanha, conjunto ou criativo filtra os
                            gráficos de rastreio. O filtro de canal também vale para a Origem da Seção 01.
                        </p>
                    </DocFeature>
                    <DocFeature title="Combinação" badge="OU · E" badgeTone="neutral" wide>
                        <p>
                            Vários valores na mesma dimensão somam (<strong>OU</strong>); dimensões diferentes se
                            combinam (<strong>E</strong>). Os filtros ativos aparecem como chips na barra do topo.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="limitacoes"
                title="Diferenças para o dashboard legado (Marketing NG)"
                subtitle="O que mudou, o que ainda não existe e o motivo de cada decisão"
                icon="alert"
                tone="danger"
            >
                <DocGrid cols={2}>
                    <DocChange status="Simplificado" tone="info" area="Canais" title="Campanha única">
                        <p>
                            A separação Campanha RA x Campanha NG foi descontinuada — a Seção 04 compara{' '}
                            <strong>Campanha x Total</strong>.
                        </p>
                    </DocChange>
                    <DocChange status="Não existe" tone="danger" area="Perfil" title="Sem dispositivo">
                        <p>
                            O <Code>lexpre</Code> não registra o dispositivo do lead, então os gráficos de dispositivo
                            do legado não existem aqui.
                        </p>
                    </DocChange>
                    <DocChange status="Regra lexpre" tone="ok" area="Protocolo" title="Ticket médio por protocolado">
                        <p>
                            O legado dividia o valor de causa pelas ações fechadas; aqui divide pelos{' '}
                            <strong>protocolados</strong>, a regra dos dashboards lexpre.
                        </p>
                    </DocChange>
                    <DocChange status="Em evolução" area="Anúncios" title="Anúncios do LA ainda não integrados">
                        <p>
                            A tabela de Facebook Ads só tem as contas do NG. Os indicadores de anúncio do LA passam a
                            aparecer quando a conta de anúncios do LA for integrada.
                        </p>
                    </DocChange>
                </DocGrid>
            </DocSection>
        </DocPage>
    )
}
