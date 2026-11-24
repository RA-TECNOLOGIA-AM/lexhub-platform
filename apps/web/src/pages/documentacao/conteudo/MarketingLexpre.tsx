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

// Guia trazido da v1: LexHub/src/pages/documentacao/Marketing_Lexpre.tsx (convertido para as peças da V2).

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
            note="Banco lexpre — base nova, em construção"
            toc={TOC}
            intro={
                <>
                    Este guia explica cada número e gráfico do dashboard de Marketing a partir da nova base de dados
                    (banco <Code>lexpre</Code>): perfil dos clientes, triagem, investimento em anúncios, fechamento das
                    campanhas, rastreio de aquisição e indicadores dos canais pago e orgânico. Nenhum conhecimento
                    técnico é necessário.
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
                            desc: 'Atendimentos assinados do lexpre (public.atendimento), com os dados do cliente e as respostas da pesquisa socioeconômica (triagem).',
                        },
                        {
                            name: 'Comercial (Seções 03 a 07)',
                            desc: 'Atendimentos e demandas do lexpre — a mesma consulta do dashboard Comercial (LexPre). Traz canal de aquisição, campanha, posicionamento, conjunto, criativo, rubrica e valor de causa.',
                        },
                        {
                            name: 'Protocolados (Seções 04, 06 e 07)',
                            desc: 'Log de movimentação de setor do lexpre — a mesma fonte e as mesmas regras do dashboard Protocolo (LexPre), para os números baterem entre as duas páginas.',
                        },
                        {
                            name: 'Anúncios (Seções 03 e 06)',
                            desc: 'Tabela de Facebook Ads do banco legado (metrics_ads.facebook_ads): valor gasto, cliques, pageview e leads do anúncio, por dia.',
                        },
                    ].map((f) => (
                        <DocCard>
                            <p>{f.name}</p>
                            <p>{f.desc}</p>
                        </DocCard>
                    ))}
                </DocGrid>
                <InfoBox>
                    <strong>Cliente assinado</strong> é o atendimento com status "Assinado" e data de assinatura
                    preenchida — a mesma regra do Comercial (LexPre). O motivo de encerramento <strong>não</strong> é
                    usado: ele só é preenchido quando o atendimento é encerrado, bem depois da assinatura (em set/2026,
                    só 14 de 172 assinados do NGAM tinham esse campo preenchido). <strong>Campanha</strong> é o canal de
                    aquisição "anúncio" — no lexpre não existe mais a separação Campanha RA x Campanha NG do legado.
                </InfoBox>
            </DocSection>

            <DocSection
                id="perfil"
                title="01 · Perfil de Clientes"
                subtitle="Quem são os clientes assinados que entraram no período"
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

            <DocSection id="triados" title="02 · Triados" subtitle="Clientes que responderam a pesquisa socioeconômica">
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
                title="03 · Facebook Ads"
                subtitle="Investimento, funil do anúncio e origem dos leads"
            >
                <DocGrid>
                    <MetricCard
                        icon="trendingUp"
                        name="Valor Gasto"
                        what="Quanto foi investido em anúncios no período."
                        counts="Soma do valor gasto na tabela de Facebook Ads, pela data do anúncio."
                        calc="Soma direta."
                        interpret="Base de todos os indicadores de custo (CAC, CPL) e retorno (ROAS)."
                        caveat="A tabela de anúncios não informa o escritório. No NG entra a tabela inteira; no LA entram só campanhas com prefixo “[LA]”, que ainda não existem nessa tabela (a conta de anúncios do LA não está integrada). Por isso o LA mostra valor gasto, cliques, pageview, CAC, ROAS e CPL zerados."
                    />
                    <MetricCard
                        icon="trendingUp"
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
                        icon="trendingUp"
                        name="Funil Anúncio"
                        what="Do clique no anúncio até o cliente assinado."
                        counts="Cliques, pageview e leads vêm da tabela de Facebook Ads; Clientes é o total de clientes da Seção 01."
                        calc="Barras proporcionais ao primeiro degrau (Cliques = 100%)."
                        interpret="Mostra onde o funil perde mais gente."
                        caveat="O degrau CLIENTES conta clientes de todos os canais (igual ao legado), não só os vindos do anúncio — para os de campanha, veja o card Clientes de Campanha."
                    />
                    <MetricCard
                        icon="trendingUp"
                        name="Clientes de Campanha, Leads, Indicação e Retorno (Ativa/Passiva)"
                        what="Quantos clientes vieram do anúncio e quantos leads entraram por cada origem."
                        counts="Clientes de Campanha: assinados via anúncio pela data de assinatura. Leads: atendimentos pela data de entrada. Indicação/Retorno: leads desses canais, separados pela prospecção (ativa ou passiva)."
                        calc="Contagem de atendimentos distintos."
                        interpret="Compara o volume do canal pago com o das indicações e retornos."
                    />
                    <MetricCard
                        icon="trendingUp"
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
                title="04 · Fechamento Campanhas"
                subtitle="Resultado da campanha comparado ao total do escritório"
            >
                <InfoBox>
                    No legado esta seção comparava Campanha RA x Campanha NG. No lexpre a campanha é um canal só, então
                    a seção compara <strong>Campanha x Total</strong>: os cards mostram a campanha, e as roscas mostram
                    a fatia da campanha ao lado do total do escritório.
                </InfoBox>
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
                        icon="check"
                        name="Protocolados / Valor de Causa / Ticket Médio"
                        what="O que a campanha já virou em processo protocolado."
                        counts="Demandas protocoladas no período cujo atendimento veio de campanha. Uma demanda conta uma vez, mesmo que seja um pacote de rubricas reunidas."
                        calc="Mesmas regras do dashboard Protocolo (LexPre): a última saída da demanda do setor Protocolo com status “Aguardando Despacho Inicial”, pela data dessa saída. Ticket Médio = Valor de Causa ÷ Protocolados."
                        interpret="Mede o retorno jurídico real da campanha, não só os contratos."
                        caveat="O Total das roscas bate com os cards do dashboard Protocolo (LexPre) no mesmo período (validado em set/2026). Demandas que voltaram ao setor Protocolo depois de protocoladas não contam."
                    />
                    <MetricCard
                        icon="check"
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
                title="05 · Análise de Aquisição"
                subtitle="Rastreio dos leads e dos que fecharam contrato"
            >
                <InfoBox>
                    No lexpre não existe uma tabela de trackeamento separada: os dados de rastreio do anúncio (campanha,
                    posicionamento, conjunto e criativo) ficam no próprio atendimento. Por isso{' '}
                    <strong>Trackeamento</strong> são os atendimentos que entraram no período, e{' '}
                    <strong>Fechamento</strong> são os desses que assinaram — a mesma turma de entrada, como no legado.
                </InfoBox>
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
                title="06 · Ind. Performance de MKT"
                subtitle="Indicadores consolidados só da campanha (anúncio)"
            >
                <InfoBox>
                    Como no legado, esta seção reúne numa só vista números que já aparecem nas seções anteriores: Valor
                    Gasto, CAC e ROAS vêm da 03; Clientes, % Taxa Fechamento, Valor de Causa e Ticket Médio vêm da 04;
                    os gráficos de rastreio são os da 05, só com o canal anúncio; Rubricas é o mesmo dado de “Rubrica —
                    Campanha”.
                </InfoBox>
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
                title="07 · Ind. Orgânico de MKT"
                subtitle="Os mesmos indicadores, para os canais orgânicos"
            >
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

            <DocSection id="filtros" title="Filtros disponíveis" subtitle="Como personalizar a visão do dashboard">
                <DocGrid>
                    {[
                        {
                            name: 'Período',
                            desc: 'Cada seção usa a data que faz sentido para ela: entrada do atendimento (perfil, leads, rastreio), assinatura (clientes, ações), protocolo (protocolados) e data do anúncio (Facebook Ads).',
                        },
                        {
                            name: 'Perfil (Seções 01 e 02)',
                            desc: 'Clicar em faixa etária, gênero, origem, tipo de tráfego, ocupação, prospecção, tipo de residência ou pessoas dependentes filtra os gráficos de perfil.',
                        },
                        {
                            name: 'Rubrica (Seções 04, 06 e 07)',
                            desc: 'Clicar numa rubrica recorta os números de campanha e orgânico — não mexe no perfil, nos anúncios nem em Valor Gasto/CAC/ROAS, igual ao legado.',
                        },
                        {
                            name: 'Rastreio (Seções 05, 06 e 07)',
                            desc: 'Clicar em categoria, posicionamento, canal, campanha, conjunto ou criativo filtra os gráficos de rastreio. O filtro de canal também vale para a Origem da Seção 01.',
                        },
                        {
                            name: 'Combinação',
                            desc: 'Vários valores na mesma dimensão somam (OU); dimensões diferentes se combinam (E). Os filtros ativos aparecem como chips na barra do topo.',
                        },
                    ].map((f) => (
                        <DocCard>
                            <p>{f.name}</p>
                            <p>{f.desc}</p>
                        </DocCard>
                    ))}
                </DocGrid>
            </DocSection>

            <DocSection
                id="limitacoes"
                title="Diferenças para o dashboard legado (Marketing NG)"
                subtitle="O que mudou, o que ainda não existe, e por quê"
            >
                <DocGrid>
                    <DocCard title="Campanha única">
                        <p>
                            A separação Campanha RA x Campanha NG foi descontinuada — a Seção 04 compara Campanha x
                            Total.
                        </p>
                    </DocCard>
                    <DocCard title="Sem dispositivo">
                        <p>
                            O lexpre não registra o dispositivo do lead, então os gráficos de dispositivo do legado não
                            existem aqui.
                        </p>
                    </DocCard>
                    <DocCard title="Ticket médio por protocolado">
                        <p>
                            O legado dividia o valor de causa pelas ações fechadas; aqui divide pelos protocolados, a
                            regra dos dashboards lexpre.
                        </p>
                    </DocCard>
                    <DocCard title="Anúncios do LA ainda não integrados">
                        <p>
                            A tabela de Facebook Ads só tem as contas do NG. Os indicadores de anúncio do LA passam a
                            aparecer quando a conta de anúncios do LA for integrada.
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>
        </DocPage>
    )
}
