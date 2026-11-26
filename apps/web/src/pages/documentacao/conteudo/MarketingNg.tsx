import {
    Code,
    DocCard,
    DocGrid,
    DocPage,
    DocSection,
    InfoBox,
    MetricCard,
    type TocItem,
} from '../components/DocParts.tsx'

// Guia novo da V2 (a v1 não tinha guia do Marketing NG). Cálculo: apps/api/src/app/dashboards/marketing.py
// (cópia da v1 /marketing_NG) + a soma do LexPre em marketing_soma_lexpre.py.

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
                    do LexPre. Nenhum conhecimento técnico é necessário.
                </>
            }
        >
            <DocSection
                id="como-funciona"
                title="Como o dashboard funciona"
                subtitle="De onde vêm os dados e o que é um cliente assinado"
            >
                <DocGrid>
                    {[
                        {
                            name: 'Perfil de clientes (Seções 01 e 02)',
                            desc: 'Clientes assinados do banco NG, com os dados do cliente, o dispositivo e as respostas da pesquisa socioeconômica (triagem).',
                        },
                        {
                            name: 'Pipeline comercial (Seção 03)',
                            desc: 'Atendimentos do banco NG pela data de entrada: leads, indicação, retorno e as etapas do pipeline (onboarding, etapas 1 a 3, em assinatura).',
                        },
                        {
                            name: 'Análise de campanhas (Seções 04, 06 e 07)',
                            desc: 'Atendimentos e ações do banco NG por canal de aquisição (Anúncio RA, Anúncio NG, orgânicos), com rubrica, assinatura e saída do Protocolo.',
                        },
                        {
                            name: 'Trackeamento (Seção 05)',
                            desc: 'Tabela de rastreio do anúncio do banco NG (campanha, posicionamento, conjunto e criativo), pela data do trackeamento.',
                        },
                        {
                            name: 'Anúncios (Seções 03 e 06)',
                            desc: 'Tabela de Facebook Ads do banco NG (metrics_ads.facebook_ads): valor gasto, cliques, pageview e leads do anúncio, por dia.',
                        },
                    ].map((f) => (
                        <DocCard key={f.name}>
                            <p>{f.name}</p>
                            <p>{f.desc}</p>
                        </DocCard>
                    ))}
                </DocGrid>
                <InfoBox>
                    No banco NG, <strong>cliente assinado</strong> é o atendimento encerrado com o motivo "fechado"
                    (motivo de encerramento <Code>11</Code>). <strong>Campanha RA</strong> é o canal de aquisição
                    "Anúncio" e <strong>Campanha NG</strong> é o canal "Anúncio NG".
                </InfoBox>
            </DocSection>

            <DocSection
                id="soma-lexpre"
                title="Soma com o LexPre"
                subtitle="Por que os números juntam duas bases, e o que não soma"
            >
                <p>
                    Desde set/2026 o comercial da NG é registrado no LexPre, e o banco NG parou de receber atendimentos
                    em 22/10/2026. Sem a soma, clientes, leads, campanha e CAC zerariam no período novo. Por isso o
                    dashboard soma aos números do banco NG os do <strong>Marketing (LexPre) do escritório NG</strong>,
                    com o mesmo período e os mesmos filtros. O aviso no topo da página diz se a soma entrou.
                </p>
                <DocGrid>
                    <DocCard title="O que soma">
                        <p>
                            Contagens e valores (clientes, leads, indicação, retorno, protocolados, valor de causa,
                            ações) e os gráficos, juntados pelo nome. A campanha do LexPre (canal "anúncio") entra como{' '}
                            <strong>Campanha NG</strong>.
                        </p>
                    </DocCard>
                    <DocCard title="O que é recalculado">
                        <p>
                            Médias de idade (ponderadas pela quantidade de clientes de cada base) e as razões:
                            conversão, ticket médio, aproveitamento, CPL e taxa de fechamento, refeitas sobre as somas.
                            CAC e ROAS usam o mesmo valor gasto nas duas bases.
                        </p>
                    </DocCard>
                    <DocCard title="O que não soma">
                        <p>
                            Facebook Ads (valor gasto, cliques, pageview, leads do anúncio e a série por dia): é a mesma
                            tabela nas duas bases. Funil de pipeline e dispositivo: só existem no banco NG.
                        </p>
                    </DocCard>
                    <DocCard title="Sem contar duas vezes">
                        <p>
                            Conferido em 25/11/2026: dos 135 clientes fechados no banco NG e 524 assinados no LexPre
                            (NG) desde 15/08/2026, só 5 aparecem nas duas bases, em meses diferentes (clientes que
                            voltaram).
                        </p>
                    </DocCard>
                </DocGrid>
                <InfoBox>
                    Quando a soma não entra, o aviso fica amarelo e diz o motivo: LexPre fora do ar, unidade sem LexPre
                    ligado ou o filtro de <strong>dispositivo</strong> ativo (o LexPre não registra dispositivo, então
                    com esse filtro aparecem só os números do banco NG).
                </InfoBox>
            </DocSection>

            <DocSection
                id="perfil"
                title="01 · Perfil de Clientes"
                subtitle="Quem são os clientes assinados no período"
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

            <DocSection id="triados" title="02 · Triados" subtitle="Clientes que responderam a pesquisa socioeconômica">
                <MetricCard
                    icon="fileText"
                    name="Triados (todos os gráficos da seção)"
                    what="O mesmo perfil da Seção 01, só para os clientes que responderam a triagem, mais moradia, dependentes e dispositivo."
                    counts="Os clientes da Seção 01 marcados como respondentes da triagem."
                    calc="Mesmos agrupamentos da Seção 01; Tipo de residência e Pessoas dependentes vêm das respostas da triagem."
                    interpret="Aprofunda o perfil com dados socioeconômicos que só existem para quem passou pela triagem."
                />
            </DocSection>

            <DocSection id="facebook" title="03 · Facebook Ads" subtitle="Investimento, funis e origem dos leads">
                <DocGrid>
                    <MetricCard
                        icon="trendingUp"
                        name="Valor gasto"
                        what="Quanto foi investido em anúncios no período."
                        counts="Soma do valor gasto na tabela de Facebook Ads, pela data do anúncio."
                        calc="Soma direta. Não soma com o LexPre: é a mesma tabela."
                        interpret="Base de todos os indicadores de custo (CAC, CPL) e retorno (ROAS)."
                    />
                    <MetricCard
                        icon="trendingUp"
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
                        icon="trendingUp"
                        name="Anúncio · Funil de conversão"
                        what="Do clique no anúncio até o cliente fechado."
                        counts="Cliques, pageview e leads vêm da tabela de Facebook Ads; Clientes é o total de clientes da Seção 01."
                        calc="Barras proporcionais ao primeiro degrau, com a taxa de passagem entre eles."
                        interpret="Mostra onde o funil perde mais gente."
                        caveat="O degrau de clientes conta todos os canais, não só os vindos do anúncio. Para os de campanha, veja Clientes campanha."
                    />
                    <MetricCard
                        icon="trendingUp"
                        name="Funil de pipeline comercial"
                        what="Quantos atendimentos passaram por cada etapa do pipeline: onboarding, etapas 1 a 3 (e as respostas) e em assinatura."
                        counts="Atendimentos do banco NG que entraram no período."
                        calc="Cada etapa conta quem tem a data ou a marcação daquela etapa. A ordem é fixa; etapas zeradas aparecem agrupadas."
                        interpret="Mostra em que etapa do atendimento o lead para."
                        caveat="Só banco NG: o LexPre não tem essas etapas. Como um cliente pode pular etapas, o funil nem sempre diminui de uma etapa para a outra."
                    />
                    <MetricCard
                        icon="trendingUp"
                        name="Clientes campanha, Leads totais, Indicação e Retorno (ativa/passiva)"
                        what="Quantos clientes vieram de campanha e quantos leads entraram por cada origem."
                        counts="Clientes campanha: clientes fechados de campanha. Leads: atendimentos pela data de entrada, todos os canais. Indicação/Retorno: leads desses canais, separados pela prospecção (ativa ou passiva)."
                        calc="Contagem de atendimentos distintos, somada à do LexPre."
                        interpret="Compara o volume do canal pago com o das indicações e retornos."
                    />
                    <MetricCard
                        icon="trendingUp"
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
                title="04 · Fechamento de campanhas (RA × NG)"
                subtitle="Resultado de cada campanha comparado ao total do escritório"
            >
                <InfoBox>
                    O banco NG separa duas campanhas: <strong>RA</strong> (canal "Anúncio") e <strong>NG</strong> (canal
                    "Anúncio NG"). A campanha do LexPre entra na parte <strong>NG</strong>; a RA só tem dados do banco
                    NG.
                </InfoBox>
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
                        icon="check"
                        name="Protocolados / Valor de causa / Ticket médio"
                        what="O que cada campanha já virou em processo protocolado."
                        counts="Processos resolvidos no Protocolo cuja saída do setor está no período, por campanha."
                        calc="Valor de causa usa o dano moral nas rubricas ANP e o valor da causa nas demais. Ticket médio = Valor de causa ÷ Ações fechadas (regra do banco NG)."
                        interpret="Mede o retorno jurídico real da campanha, não só os contratos."
                    />
                    <MetricCard
                        icon="check"
                        name="Roscas: Total de clientes, Protocolo resolvido e Valor de causa"
                        what="A fatia de cada campanha ao lado da base geral do escritório."
                        counts="Os mesmos números dos cards, mais o total sem filtro de canal."
                        calc="Contagem e soma por campanha."
                        interpret="Mostra quanto do resultado do escritório vem das campanhas pagas."
                    />
                    <MetricCard
                        icon="check"
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
                title="05 · Análise de Aquisição"
                subtitle="Rastreio dos leads e dos que fecharam contrato"
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
                title="06 · Indicadores de performance — NG"
                subtitle="Indicadores consolidados só da campanha NG"
            >
                <InfoBox>
                    Esta seção reúne numa só vista números das seções anteriores, recortados para o canal "Anúncio NG"
                    (com a campanha do LexPre somada): Valor gasto, CAC e ROAS vêm da 03; Clientes, Valor de causa e
                    Ticket médio vêm da 04; os gráficos de rastreio são os da 05.
                </InfoBox>
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
                title="07 · Indicadores orgânicos — NG"
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

            <DocSection id="filtros" title="Filtros disponíveis" subtitle="Como personalizar a visão do dashboard">
                <DocGrid>
                    {[
                        {
                            name: 'Período',
                            desc: 'Cada seção usa a data que faz sentido para ela: assinatura (perfil, clientes, ações), entrada (leads, pipeline), saída do Protocolo (protocolados), data do trackeamento (rastreio) e data do anúncio (Facebook Ads).',
                        },
                        {
                            name: 'Clique nos gráficos',
                            desc: 'Clicar numa barra ou fatia (faixa etária, gênero, canal, rubrica, campanha, posicionamento...) liga o filtro daquela dimensão na página toda, inclusive na parte somada do LexPre.',
                        },
                        {
                            name: 'Dispositivo',
                            desc: 'Só existe no banco NG. Com ele ligado, o LexPre sai da soma e o aviso no topo explica.',
                        },
                        {
                            name: 'Combinação',
                            desc: 'Vários valores na mesma dimensão somam (OU); dimensões diferentes se combinam (E). Os filtros ativos aparecem como chips na barra do topo.',
                        },
                    ].map((f) => (
                        <DocCard key={f.name}>
                            <p>{f.name}</p>
                            <p>{f.desc}</p>
                        </DocCard>
                    ))}
                </DocGrid>
            </DocSection>

            <DocSection
                id="diferencas"
                title="Diferenças para o Marketing (LexPre)"
                subtitle="Os dois dashboards têm as mesmas seções, mas não as mesmas regras"
            >
                <DocGrid>
                    <DocCard title="Duas campanhas">
                        <p>Aqui a Seção 04 compara Campanha RA × Campanha NG; no LexPre é Campanha × Total.</p>
                    </DocCard>
                    <DocCard title="Dispositivo e pipeline">
                        <p>Só o Marketing NG tem os gráficos de dispositivo e o funil de pipeline comercial.</p>
                    </DocCard>
                    <DocCard title="Ticket médio">
                        <p>
                            Aqui o ticket divide o valor de causa pelas ações fechadas (regra do banco NG); no LexPre,
                            pelos protocolados.
                        </p>
                    </DocCard>
                    <DocCard title="Cliente assinado">
                        <p>
                            Aqui é o motivo de encerramento "fechado"; no LexPre é o status "Assinado" com data de
                            assinatura.
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>
        </DocPage>
    )
}
