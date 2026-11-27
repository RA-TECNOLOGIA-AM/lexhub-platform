import {
    Code,
    DocCallout,
    DocChange,
    DocFeature,
    DocGrid,
    DocLink,
    DocMini,
    DocPage,
    DocSection,
    Hl,
    MetricCard,
    type TocItem,
} from '../components/DocParts.tsx'

// Guia novo da V2 (a v1 não tinha guia do Marketing NG). Cálculo: apps/api/src/app/dashboards/marketing.py
// (cópia da v1 /marketing_NG) + a soma do LexPre em marketing_soma_lexpre.py.
// Os números 01–07 são as seções do próprio dashboard; as demais seções usam ícone.

const TOC: TocItem[] = [
    { id: 'como-funciona', label: 'Como funciona' },
    { id: 'soma-lexpre', label: 'Soma com o LexPre' },
    { id: 'perfil', label: '01 · Perfil de Clientes' },
    { id: 'triados', label: '02 · Triados' },
    { id: 'facebook', label: '03 · Facebook Ads' },
    { id: 'fechamento', label: '04 · Fechamento RA × NG' },
    { id: 'aquisicao', label: '05 · Análise de Aquisição' },
    { id: 'performance', label: '06 · Ind. Performance NG' },
    { id: 'organico', label: '07 · Ind. Orgânico NG' },
    { id: 'filtros', label: 'Filtros' },
    { id: 'diferencas', label: 'Diferenças para o Marketing (LexPre)' },
]

export function MarketingNgDoc() {
    return (
        <DocPage
            title="Marketing — NG"
            tags={['NG']}
            note="Banco NG legado + LexPre (escritório NG)"
            toc={TOC}
            intro={
                <>
                    Este guia explica cada número e gráfico do dashboard de Marketing da NG: perfil dos clientes,
                    triagem, investimento em anúncios, fechamento das campanhas RA e NG, rastreio de aquisição e
                    indicadores dos canais pago e orgânico. Os números vêm do banco NG legado e, desde set/2026, também
                    do LexPre. <strong>Nenhum conhecimento técnico é necessário.</strong>
                </>
            }
            header={
                <DocCallout caps title="Duas bases, um dashboard" badge="Banco NG parado desde 22/10/2026">
                    <p>
                        Os números juntam o banco NG legado e o{' '}
                        <DocLink to="marketing-lexpre">Marketing (LexPre)</DocLink> do escritório NG, com o mesmo
                        período e os mesmos filtros — veja a seção{' '}
                        <a className="doc-link" href="#soma-lexpre">
                            Soma com o LexPre
                        </a>
                        .
                    </p>
                    <DocGrid>
                        <DocMini label="Cliente assinado (banco NG)">
                            Atendimento encerrado com o motivo "fechado" (motivo de encerramento <Code>11</Code>).
                        </DocMini>
                        <DocMini label="Duas campanhas">
                            <Hl mono>Campanha RA</Hl> = canal "Anúncio";{' '}
                            <Hl tone="info" mono>
                                Campanha NG
                            </Hl>{' '}
                            = canal "Anúncio NG".
                        </DocMini>
                    </DocGrid>
                </DocCallout>
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
                            Clientes assinados do banco NG, com os dados do cliente, o dispositivo e as respostas da
                            pesquisa socioeconômica (triagem).
                        </p>
                    </DocFeature>
                    <DocFeature title="Pipeline comercial" tone="accent" badge="Seção 03">
                        <p>
                            Atendimentos do banco NG pela data de entrada: leads, indicação, retorno e as etapas do
                            pipeline (onboarding, etapas 1 a 3, em assinatura).
                        </p>
                    </DocFeature>
                    <DocFeature title="Análise de campanhas" tone="ok" badge="Seções 04, 06 e 07">
                        <p>
                            Atendimentos e ações do banco NG por canal de aquisição (Anúncio RA, Anúncio NG, orgânicos),
                            com rubrica, assinatura e saída do Protocolo.
                        </p>
                    </DocFeature>
                    <DocFeature title="Trackeamento" tone="info" badge="Seção 05">
                        <p>
                            Tabela de rastreio do anúncio do banco NG (campanha, posicionamento, conjunto e criativo),
                            pela data do trackeamento.
                        </p>
                    </DocFeature>
                    <DocFeature title="Anúncios" tone="violet" badge="Seções 03 e 06" wide>
                        <p>
                            Tabela de Facebook Ads do banco NG (<Code>metrics_ads.facebook_ads</Code>): valor gasto,
                            cliques, pageview e leads do anúncio, por dia.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="soma-lexpre"
                title="Soma com o LexPre"
                subtitle="Por que os números juntam duas bases, e o que não soma"
                icon="layers"
            >
                <DocCallout icon="clock" title="Por que somar?">
                    <p>
                        Desde set/2026 o comercial da NG é registrado no LexPre, e o banco NG parou de receber
                        atendimentos em <strong>22/10/2026</strong>. Sem a soma, clientes, leads, campanha e CAC
                        zerariam no período novo. Por isso o dashboard soma aos números do banco NG os do{' '}
                        <strong>Marketing (LexPre) do escritório NG</strong>, com o mesmo período e os mesmos filtros. O
                        aviso no topo da página diz se a soma entrou.
                    </p>
                </DocCallout>
                <DocGrid cols={2}>
                    <DocFeature title="O que soma" tone="ok" icon="plus" framed>
                        <p>
                            Contagens e valores (clientes, leads, indicação, retorno, protocolados, valor de causa,
                            ações) e os gráficos, juntados pelo nome. A campanha do LexPre (canal "anúncio") entra como{' '}
                            <strong>Campanha NG</strong>.
                        </p>
                    </DocFeature>
                    <DocFeature title="O que é recalculado" tone="info" icon="refresh" framed>
                        <p>
                            Médias de idade (ponderadas pela quantidade de clientes de cada base) e as razões:
                            conversão, ticket médio, aproveitamento, CPL e taxa de fechamento, refeitas sobre as somas.
                            CAC e ROAS usam o mesmo valor gasto nas duas bases.
                        </p>
                    </DocFeature>
                    <DocFeature title="O que não soma" tone="danger" icon="minus" framed>
                        <p>
                            Facebook Ads (valor gasto, cliques, pageview, leads do anúncio e a série por dia): é a mesma
                            tabela nas duas bases. Funil de pipeline e dispositivo: só existem no banco NG.
                        </p>
                    </DocFeature>
                    <DocFeature title="Sem contar duas vezes" icon="check" badge="Conferido em 25/11/2026">
                        <p>
                            Dos 135 clientes fechados no banco NG e 524 assinados no LexPre (NG) desde 15/08/2026, só{' '}
                            <strong>5</strong> aparecem nas duas bases, em meses diferentes (clientes que voltaram).
                        </p>
                    </DocFeature>
                </DocGrid>
                <DocCallout tone="warn" icon="alert" title="Quando a soma não entra">
                    <p>
                        O aviso fica amarelo e diz o motivo: LexPre fora do ar, unidade sem LexPre ligado ou o filtro de{' '}
                        <strong>dispositivo</strong> ativo (o LexPre não registra dispositivo, então com esse filtro
                        aparecem só os números do banco NG).
                    </p>
                </DocCallout>
            </DocSection>

            <DocSection
                id="perfil"
                title="01 — Perfil de Clientes"
                subtitle="Quem são os clientes assinados no período"
                badge="Data de assinatura"
            >
                <MetricCard
                    icon="users"
                    name="Perfil de Clientes (todos os gráficos da seção)"
                    what="O perfil demográfico e de aquisição dos clientes assinados: idade, gênero, canal de aquisição, tipo de tráfego, ocupação, prospecção, faixa salarial e dispositivo."
                    counts="Clientes assinados do banco NG cuja data de assinatura está no período, somados aos do LexPre (NG)."
                    calc={
                        <>
                            Cada gráfico conta os clientes por um campo: <strong>Média de idade</strong> calcula a idade
                            pela data de nascimento e agrupa em faixas etárias; <strong>Canal de aquisição</strong> usa
                            a origem do cliente; <strong>Ocupação</strong> e <strong>Média salarial mensal</strong> vêm
                            das respostas da triagem.
                        </>
                    }
                    interpret="Mostra o perfil típico de quem fecha contrato, útil para ajustar o público das campanhas."
                    caveat="O gráfico de Dispositivo só tem os clientes do banco NG. Ocupação e faixa salarial só aparecem para quem respondeu a triagem."
                />
            </DocSection>

            <DocSection id="triados" title="02 — Triados" subtitle="Clientes que responderam a pesquisa socioeconômica">
                <MetricCard
                    icon="fileText"
                    name="Triados (todos os gráficos da seção)"
                    what="O mesmo perfil da Seção 01, só para os clientes que responderam a triagem, mais moradia, dependentes e dispositivo."
                    counts="Os clientes da Seção 01 marcados como respondentes da triagem."
                    calc="Mesmos agrupamentos da Seção 01; Tipo de residência e Pessoas dependentes vêm das respostas da triagem."
                    interpret="Aprofunda o perfil com dados socioeconômicos que só existem para quem passou pela triagem."
                />
            </DocSection>

            <DocSection id="facebook" title="03 — Facebook Ads" subtitle="Investimento, funis e origem dos leads">
                <DocGrid>
                    <MetricCard
                        icon="dollar"
                        name="Valor gasto"
                        what="Quanto foi investido em anúncios no período."
                        counts="Soma do valor gasto na tabela de Facebook Ads, pela data do anúncio."
                        calc="Soma direta. Não soma com o LexPre: é a mesma tabela."
                        interpret="Base de todos os indicadores de custo (CAC, CPL) e retorno (ROAS)."
                    />
                    <MetricCard
                        icon="users"
                        name="CAC campanha / CAC geral"
                        what="Custo de aquisição por cliente."
                        counts="Clientes fechados de campanha (CAC campanha) ou de campanha + indicação (CAC geral) que entraram no período."
                        calc="Valor gasto ÷ quantidade desses clientes. Com o LexPre, os clientes das duas bases entram juntos no divisor."
                        interpret="Quanto menor, mais barato está sendo trazer cada cliente."
                    />
                    <MetricCard
                        icon="trendingUp"
                        name="ROAS campanha / ROAS geral"
                        what="Retorno do investimento em anúncios, em valor de causa."
                        counts="Valor de causa protocolado no período dos clientes de campanha (ROAS campanha) ou de todo o escritório (ROAS geral)."
                        calc="Valor de causa protocolado ÷ valor gasto (ex.: 200 = R$ 200 de causa para cada R$ 1 investido). Com o LexPre, os dois retornos somam."
                        interpret="Quanto maior, mais valor de causa cada real investido gerou."
                    />
                    <MetricCard
                        icon="filter"
                        name="Anúncio · Funil de conversão"
                        what="Do clique no anúncio até o cliente fechado."
                        counts="Cliques, pageview e leads vêm da tabela de Facebook Ads; Clientes é o total de clientes da Seção 01."
                        calc="Barras proporcionais ao primeiro degrau, com a taxa de passagem entre eles."
                        interpret="Mostra onde o funil perde mais gente."
                        caveat="O degrau de clientes conta todos os canais, não só os vindos do anúncio. Para os de campanha, veja Clientes campanha."
                    />
                    <MetricCard
                        icon="flow"
                        name="Funil de pipeline comercial"
                        what="Quantos atendimentos passaram por cada etapa do pipeline: onboarding, etapas 1 a 3 (e as respostas) e em assinatura."
                        counts="Atendimentos do banco NG que entraram no período."
                        calc="Cada etapa conta quem tem a data ou a marcação daquela etapa. A ordem é fixa; etapas zeradas aparecem agrupadas."
                        interpret="Mostra em que etapa do atendimento o lead para."
                        caveat="Só banco NG: o LexPre não tem essas etapas. Como um cliente pode pular etapas, o funil nem sempre diminui de uma etapa para a outra."
                    />
                    <MetricCard
                        icon="users"
                        name="Clientes campanha, Leads totais, Indicação e Retorno (ativa/passiva)"
                        what="Quantos clientes vieram de campanha e quantos leads entraram por cada origem."
                        counts="Clientes campanha: clientes fechados de campanha. Leads: atendimentos pela data de entrada, todos os canais. Indicação/Retorno: leads desses canais, separados pela prospecção (ativa ou passiva)."
                        calc="Contagem de atendimentos distintos, somada à do LexPre."
                        interpret="Compara o volume do canal pago com o das indicações e retornos."
                    />
                    <MetricCard
                        icon="barChart"
                        name="Investimento por dia / Cliques e leads por dia"
                        what="A evolução diária do investimento e da resposta do anúncio."
                        counts="Por dia do período: valor gasto, cliques e leads da tabela de Facebook Ads."
                        calc="Soma diária."
                        interpret="Mostra se aumentos de investimento vêm acompanhados de mais cliques e leads."
                    />
                </DocGrid>
            </DocSection>

            <DocSection
                id="fechamento"
                title="04 — Fechamento de campanhas (RA × NG)"
                subtitle="Resultado de cada campanha comparado ao total do escritório"
                tone="ok"
                badge="RA × NG"
            >
                <DocGrid cols={2}>
                    <DocFeature title="Campanha RA" tone="accent" badge='Canal "Anúncio"'>
                        <p>Só tem dados do banco NG.</p>
                    </DocFeature>
                    <DocFeature title="Campanha NG" tone="info" badge='Canal "Anúncio NG"'>
                        <p>
                            Banco NG <strong>+ a campanha do LexPre</strong>, que entra nesta parte.
                        </p>
                    </DocFeature>
                </DocGrid>
                <DocGrid>
                    <MetricCard
                        icon="check"
                        name="Campanha RA / Campanha NG (com % de conversão)"
                        what="Clientes fechados por campanha e a taxa de conversão dos leads dela."
                        counts="Clientes: fechados pela data de assinatura. Conversão: esses clientes ÷ leads da campanha que entraram no período."
                        calc="Duas turmas diferentes (assinatura e entrada), como no Power BI da v1."
                        interpret="Quantos contratos cada campanha fechou e com que eficiência."
                    />
                    <MetricCard
                        icon="dollar"
                        name="Protocolados / Valor de causa / Ticket médio"
                        what="O que cada campanha já virou em processo protocolado."
                        counts="Processos resolvidos no Protocolo cuja saída do setor está no período, por campanha."
                        calc="Valor de causa usa o dano moral nas rubricas ANP e o valor da causa nas demais. Ticket médio = Valor de causa ÷ Ações fechadas (regra do banco NG)."
                        interpret="Mede o retorno jurídico real da campanha, não só os contratos."
                    />
                    <MetricCard
                        icon="pieChart"
                        name="Roscas: Total de clientes, Protocolo resolvido e Valor de causa"
                        what="A fatia de cada campanha ao lado da base geral do escritório."
                        counts="Os mesmos números dos cards, mais o total sem filtro de canal."
                        calc="Contagem e soma por campanha."
                        interpret="Mostra quanto do resultado do escritório vem das campanhas pagas."
                    />
                    <MetricCard
                        icon="barChart"
                        name="Comparativo por rubrica (RA × NG)"
                        what="Quais rubricas cada campanha trouxe e quais já foram protocoladas."
                        counts="Ações fechadas e protocoladas de clientes de campanha, por rubrica, separadas em RA e NG."
                        calc="Contagem por rubrica; as do LexPre somam na coluna NG."
                        interpret="Mostra os tipos de ação que cada campanha mais gera."
                        caveat="Clicar numa rubrica filtra os indicadores da seção."
                    />
                </DocGrid>
            </DocSection>

            <DocSection
                id="aquisicao"
                title="05 — Análise de Aquisição"
                subtitle="Rastreio dos leads e dos que fecharam contrato"
                badge="Data do trackeamento"
            >
                <MetricCard
                    icon="search"
                    name="Categoria, Posicionamento, Canal de aquisição, Campanha, Conjunto e Criativo"
                    what="Por onde os leads chegaram e por onde vieram os que fecharam."
                    counts="Linhas do trackeamento pela data do trackeamento (Trackeamento) e as que fecharam contrato (Fechamento)."
                    calc={
                        <>
                            <strong>Categoria</strong> padroniza o posicionamento em Stories, Reels ou Feed;{' '}
                            <strong>Posicionamento</strong> agrupa em Facebook, Instagram, Bio, AN ou Threads. Campanha,
                            conjunto e criativo mostram os 10 maiores.
                        </>
                    }
                    interpret="Compara o que traz volume de leads com o que realmente fecha contrato."
                    caveat="Fechamento usa a mesma data do trackeamento (não a de assinatura), como no Power BI da v1."
                />
            </DocSection>

            <DocSection
                id="performance"
                title="06 — Indicadores de performance — NG"
                subtitle="Indicadores consolidados só da campanha NG"
            >
                <DocCallout icon="layers" title='Recorte do canal "Anúncio NG" (com a campanha do LexPre somada)'>
                    <p>
                        Esta seção reúne numa só vista números das seções anteriores: Valor gasto, CAC e ROAS vêm da{' '}
                        <strong>03</strong>; Clientes, Valor de causa e Ticket médio vêm da <strong>04</strong>; os
                        gráficos de rastreio são os da <strong>05</strong>.
                    </p>
                </DocCallout>
                <DocGrid>
                    <MetricCard
                        icon="trendingUp"
                        name="Leads / CPL"
                        what="Quantos leads a campanha NG gerou e quanto custou cada um."
                        counts="Atendimentos com canal Anúncio NG que entraram no período."
                        calc="CPL = Valor gasto ÷ Leads."
                        interpret="Quanto menor o CPL, mais barato está cada lead."
                    />
                    <MetricCard
                        icon="trendingUp"
                        name="Ações / Aproveitamento / Rubricas (ações NG)"
                        what="Quantas ações a campanha NG gerou por cliente fechado, e de quais rubricas."
                        counts="Ações de clientes fechados da campanha NG, pela data de assinatura."
                        calc="Aproveitamento = Ações ÷ Clientes (é uma razão, não um percentual)."
                        interpret="Quanto maior, mais ações cada cliente de campanha está gerando."
                    />
                </DocGrid>
            </DocSection>

            <DocSection
                id="organico"
                title="07 — Indicadores orgânicos — NG"
                subtitle="Os mesmos indicadores, para os canais orgânicos"
            >
                <MetricCard
                    icon="layers"
                    name="Indicadores orgânicos"
                    what="Leads, contratos, ações e valor de causa dos canais orgânicos Facebook, Instagram, Site e Google."
                    counts="Atendimentos desses 4 canais: leads pela entrada, contratos pela assinatura, ações e valor protocolado pela regra da Seção 04."
                    calc="Taxa de fechamento = Contratos ÷ Total de leads. Aproveitamento = Ações ÷ Contratos. Ticket médio = Valor de causa ÷ Ações."
                    interpret="Compara o desempenho do tráfego orgânico com o da campanha paga."
                    caveat="Clicar num canal mostra as rubricas só dele. Retorno e indicação não entram."
                />
            </DocSection>

            <DocSection
                id="filtros"
                title="Filtros disponíveis"
                subtitle="Como personalizar e cruzar a visão do dashboard"
                icon="filter"
                tone="info"
            >
                <DocGrid cols={2}>
                    <DocFeature title="Período" badge="Data por seção" badgeTone="accent">
                        <p>
                            Cada seção usa a data que faz sentido para ela: <strong>assinatura</strong> (perfil,
                            clientes, ações), <strong>entrada</strong> (leads, pipeline),{' '}
                            <Hl tone="ok">saída do Protocolo</Hl> (protocolados), data do trackeamento (rastreio) e data
                            do anúncio (Facebook Ads).
                        </p>
                    </DocFeature>
                    <DocFeature title="Clique nos gráficos" badge="Cross-filter" badgeTone="info">
                        <p>
                            Clicar numa barra ou fatia (faixa etária, gênero, canal, rubrica, campanha,
                            posicionamento...) liga o filtro daquela dimensão na página toda, inclusive na parte somada
                            do LexPre.
                        </p>
                    </DocFeature>
                    <DocFeature title="Dispositivo" badge="Só banco NG" badgeTone="danger">
                        <p>
                            Só existe no banco NG. Com ele ligado, o LexPre <strong>sai da soma</strong> e o aviso no
                            topo explica.
                        </p>
                    </DocFeature>
                    <DocFeature title="Combinação" badge="OU · E" badgeTone="neutral">
                        <p>
                            Vários valores na mesma dimensão somam (<strong>OU</strong>); dimensões diferentes se
                            combinam (<strong>E</strong>). Os filtros ativos aparecem como chips na barra do topo.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="diferencas"
                title="Diferenças para o Marketing (LexPre)"
                subtitle="Os dois dashboards têm as mesmas seções, mas não as mesmas regras"
                icon="alert"
                tone="danger"
            >
                <DocGrid cols={2}>
                    <DocChange status="RA × NG" tone="info" area="Seção 04" title="Duas campanhas">
                        <p>
                            Aqui a Seção 04 compara <strong>Campanha RA × Campanha NG</strong>; no LexPre é Campanha ×
                            Total.
                        </p>
                    </DocChange>
                    <DocChange status="Só NG" tone="ok" area="Perfil e funil" title="Dispositivo e pipeline">
                        <p>Só o Marketing NG tem os gráficos de dispositivo e o funil de pipeline comercial.</p>
                    </DocChange>
                    <DocChange status="Regra NG" area="Protocolo" title="Ticket médio">
                        <p>
                            Aqui o ticket divide o valor de causa pelas <strong>ações fechadas</strong> (regra do banco
                            NG); no LexPre, pelos protocolados.
                        </p>
                    </DocChange>
                    <DocChange status="Regra NG" area="Clientes" title="Cliente assinado">
                        <p>
                            Aqui é o motivo de encerramento <strong>"fechado"</strong>; no LexPre é o status "Assinado"
                            com data de assinatura.
                        </p>
                    </DocChange>
                </DocGrid>
            </DocSection>
        </DocPage>
    )
}
