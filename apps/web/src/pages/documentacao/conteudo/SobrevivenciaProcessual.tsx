import {
    Code,
    DocCard,
    DocGrid,
    DocPage,
    DocSection,
    InfoBox,
    MetricCard,
    WatchBox,
    type TocItem,
} from '../components/DocParts.tsx'

// Guia trazido da v1: LexHub/src/pages/documentacao/TccSobrevivenciaProcessual.tsx (convertido para as peças da V2).

const DIAGRAM_NEUTRAL = 'var(--text-muted)'

const DIAGRAM_ACCENT = 'var(--accent)'

const DIAGRAM_FAVORAVEL = 'var(--ok-dot)'

const DIAGRAM_ENCERRA = 'var(--border-strong)'

const FluxoEstagiosDiagram = () => (
    <DocCard>
        <svg
            style={{ width: '100%', height: 'auto', display: 'block' }}
            viewBox="0 0 920 660"
            role="img"
            aria-labelledby="fluxo-titulo fluxo-desc"
        >
            <title id="fluxo-titulo">Fluxo do Estágio 1 e Estágio 2</title>
            <desc id="fluxo-desc">
                Da distribuição do processo, quatro desfechos possíveis no Estágio 1: Acordo, Mérito Favorável com
                Proveito, Mérito Sem Proveito ou Desfavorável, e Censurado. Acordo e Mérito Favorável seguem para o
                Estágio 2 (um novo relógio até o pagamento efetivo). Os outros dois terminam ali, sem Estágio 2.
            </desc>
            <defs>
                <marker id="seta" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
                    <path d="M0,0 L6,3 L0,6 Z" fill={DIAGRAM_NEUTRAL} />
                </marker>
            </defs>

            <rect
                x="370"
                y="14"
                width="180"
                height="46"
                rx="10"
                fill="var(--surface-2)"
                stroke={DIAGRAM_ACCENT}
                strokeWidth="1.5"
            />
            <text x="460" y="42" textAnchor="middle" fontSize="13.5" fontWeight="700" fill="var(--text)">
                Distribuição (t = 0)
            </text>
            <line x1="460" y1="60" x2="460" y2="88" stroke={DIAGRAM_NEUTRAL} strokeWidth="1.5" markerEnd="url(#seta)" />

            <rect
                x="210"
                y="90"
                width="500"
                height="64"
                rx="10"
                fill={DIAGRAM_ACCENT}
                fillOpacity="0.12"
                stroke={DIAGRAM_ACCENT}
                strokeWidth="1.5"
            />
            <text x="460" y="114" textAnchor="middle" fontSize="14.5" fontWeight="700" fill="var(--text)">
                ESTÁGIO 1 — qual desfecho acontece primeiro?
            </text>
            <text x="460" y="134" textAnchor="middle" fontSize="11" fill="var(--text-muted)">
                Acordo e mérito competem entre si; sentença/acórdão não (são sequenciais — ver nota abaixo)
            </text>
            <text x="460" y="149" textAnchor="middle" fontSize="11" fill="var(--text-muted)">
                4 desfechos possíveis:
            </text>

            <line x1="460" y1="154" x2="460" y2="178" stroke={DIAGRAM_NEUTRAL} strokeWidth="1.5" />
            <line x1="130" y1="178" x2="790" y2="178" stroke={DIAGRAM_NEUTRAL} strokeWidth="1.5" />
            <line
                x1="130"
                y1="178"
                x2="130"
                y2="200"
                stroke={DIAGRAM_NEUTRAL}
                strokeWidth="1.5"
                markerEnd="url(#seta)"
            />
            <line
                x1="350"
                y1="178"
                x2="350"
                y2="200"
                stroke={DIAGRAM_NEUTRAL}
                strokeWidth="1.5"
                markerEnd="url(#seta)"
            />
            <line
                x1="570"
                y1="178"
                x2="570"
                y2="200"
                stroke={DIAGRAM_NEUTRAL}
                strokeWidth="1.5"
                markerEnd="url(#seta)"
            />
            <line
                x1="790"
                y1="178"
                x2="790"
                y2="200"
                stroke={DIAGRAM_NEUTRAL}
                strokeWidth="1.5"
                markerEnd="url(#seta)"
            />

            <rect
                x="30"
                y="202"
                width="200"
                height="92"
                rx="10"
                fill="var(--surface-2)"
                stroke={DIAGRAM_FAVORAVEL}
                strokeWidth="1.5"
            />
            <text x="130" y="228" textAnchor="middle" fontSize="13" fontWeight="700" fill="var(--text)">
                Acordo
            </text>
            <text x="130" y="248" textAnchor="middle" fontSize="10.5" fill="var(--text-muted)">
                <tspan x="130" dy="0">
                    fechado antes (ou no
                </tspan>
                <tspan x="130" dy="13">
                    mesmo dia) de qualquer
                </tspan>
                <tspan x="130" dy="13">
                    decisão de mérito
                </tspan>
            </text>

            <rect
                x="250"
                y="202"
                width="200"
                height="92"
                rx="10"
                fill="var(--surface-2)"
                stroke={DIAGRAM_FAVORAVEL}
                strokeWidth="1.5"
            />
            <text x="350" y="222" textAnchor="middle" fontSize="12.5" fontWeight="700" fill="var(--text)">
                <tspan x="350" dy="0">
                    Mérito Favorável
                </tspan>
                <tspan x="350" dy="15">
                    c/ Proveito
                </tspan>
            </text>
            <text x="350" y="261" textAnchor="middle" fontSize="10.5" fill="var(--text-muted)">
                <tspan x="350" dy="0">
                    procedente/parcial,
                </tspan>
                <tspan x="350" dy="13">
                    com valor a receber
                </tspan>
            </text>

            <rect
                x="470"
                y="202"
                width="200"
                height="92"
                rx="10"
                fill="var(--surface-2)"
                stroke={DIAGRAM_ENCERRA}
                strokeWidth="1.5"
            />
            <text x="570" y="222" textAnchor="middle" fontSize="12.5" fontWeight="700" fill="var(--text)">
                <tspan x="570" dy="0">
                    Mérito Sem Proveito
                </tspan>
                <tspan x="570" dy="15">
                    ou Desfavorável
                </tspan>
            </text>
            <text x="570" y="261" textAnchor="middle" fontSize="10.5" fill="var(--text-muted)">
                <tspan x="570" dy="0">
                    julgado, mas sem
                </tspan>
                <tspan x="570" dy="13">
                    dinheiro a cobrar
                </tspan>
            </text>

            <rect
                x="690"
                y="202"
                width="200"
                height="92"
                rx="10"
                fill="var(--surface-2)"
                stroke={DIAGRAM_NEUTRAL}
                strokeWidth="1.5"
                strokeDasharray="5 4"
            />
            <text x="790" y="228" textAnchor="middle" fontSize="13" fontWeight="700" fill="var(--text)">
                Censurado
            </text>
            <text x="790" y="248" textAnchor="middle" fontSize="10.5" fill="var(--text-muted)">
                <tspan x="790" dy="0">
                    nenhum dos três acima
                </tspan>
                <tspan x="790" dy="13">
                    aconteceu ainda (até a
                </tspan>
                <tspan x="790" dy="13">
                    última movimentação)
                </tspan>
            </text>

            <line x1="130" y1="294" x2="130" y2="320" stroke={DIAGRAM_FAVORAVEL} strokeWidth="1.5" />
            <line x1="350" y1="294" x2="350" y2="320" stroke={DIAGRAM_FAVORAVEL} strokeWidth="1.5" />
            <line x1="130" y1="320" x2="350" y2="320" stroke={DIAGRAM_FAVORAVEL} strokeWidth="1.5" />
            <line
                x1="240"
                y1="320"
                x2="240"
                y2="345"
                stroke={DIAGRAM_FAVORAVEL}
                strokeWidth="1.5"
                markerEnd="url(#seta)"
            />

            <line
                x1="570"
                y1="294"
                x2="570"
                y2="330"
                stroke={DIAGRAM_NEUTRAL}
                strokeWidth="1.5"
                markerEnd="url(#seta)"
            />
            <rect
                x="470"
                y="332"
                width="200"
                height="46"
                rx="8"
                fill="var(--surface-2)"
                stroke={DIAGRAM_ENCERRA}
                strokeWidth="1.5"
            />
            <text x="570" y="360" textAnchor="middle" fontSize="11.5" fontWeight="600" fill="var(--text-muted)">
                Fim — sem Estágio 2
            </text>

            <line
                x1="790"
                y1="294"
                x2="790"
                y2="330"
                stroke={DIAGRAM_NEUTRAL}
                strokeWidth="1.5"
                markerEnd="url(#seta)"
            />
            <rect
                x="690"
                y="332"
                width="200"
                height="46"
                rx="8"
                fill="var(--surface-2)"
                stroke={DIAGRAM_NEUTRAL}
                strokeWidth="1.5"
                strokeDasharray="5 4"
            />
            <text x="790" y="360" textAnchor="middle" fontSize="11.5" fontWeight="600" fill="var(--text-muted)">
                Ainda em tramitação
            </text>

            <rect
                x="100"
                y="347"
                width="280"
                height="64"
                rx="10"
                fill={DIAGRAM_ACCENT}
                fillOpacity="0.12"
                stroke={DIAGRAM_ACCENT}
                strokeWidth="1.5"
            />
            <text x="240" y="371" textAnchor="middle" fontSize="14.5" fontWeight="700" fill="var(--text)">
                ESTÁGIO 2
            </text>
            <text x="240" y="390" textAnchor="middle" fontSize="10.5" fill="var(--text-muted)">
                <tspan x="240" dy="0">
                    novo relógio: conta a partir da data do
                </tspan>
                <tspan x="240" dy="13">
                    desfecho acima, não da distribuição
                </tspan>
            </text>

            <line x1="240" y1="411" x2="240" y2="432" stroke={DIAGRAM_NEUTRAL} strokeWidth="1.5" />
            <line x1="165" y1="432" x2="385" y2="432" stroke={DIAGRAM_NEUTRAL} strokeWidth="1.5" />
            <line
                x1="165"
                y1="432"
                x2="165"
                y2="454"
                stroke={DIAGRAM_NEUTRAL}
                strokeWidth="1.5"
                markerEnd="url(#seta)"
            />
            <line
                x1="385"
                y1="432"
                x2="385"
                y2="454"
                stroke={DIAGRAM_NEUTRAL}
                strokeWidth="1.5"
                markerEnd="url(#seta)"
            />

            <rect
                x="65"
                y="456"
                width="200"
                height="78"
                rx="10"
                fill="var(--surface-2)"
                stroke={DIAGRAM_FAVORAVEL}
                strokeWidth="1.5"
            />
            <text x="165" y="486" textAnchor="middle" fontSize="13" fontWeight="700" fill="var(--text)">
                Pago
            </text>
            <text x="165" y="506" textAnchor="middle" fontSize="10.5" fill="var(--text-muted)">
                <tspan x="165" dy="0">
                    alvará compensado ou
                </tspan>
                <tspan x="165" dy="13">
                    acordo pago
                </tspan>
            </text>

            <rect
                x="285"
                y="456"
                width="200"
                height="78"
                rx="10"
                fill="var(--surface-2)"
                stroke={DIAGRAM_NEUTRAL}
                strokeWidth="1.5"
                strokeDasharray="5 4"
            />
            <text x="385" y="480" textAnchor="middle" fontSize="12.5" fontWeight="700" fill="var(--text)">
                <tspan x="385" dy="0">
                    Censurado
                </tspan>
                <tspan x="385" dy="15">
                    (pagamento)
                </tspan>
            </text>
            <text x="385" y="519" textAnchor="middle" fontSize="10.5" fill="var(--text-muted)">
                ainda não pago
            </text>

            <g transform="translate(30, 560)">
                <rect
                    x="0"
                    y="0"
                    width="860"
                    height="80"
                    rx="10"
                    fill="var(--surface-2)"
                    fillOpacity="0.5"
                    stroke="var(--border-strong)"
                    strokeWidth="1"
                />
                <text x="16" y="20" fontSize="10.5" fontWeight="700" fill="var(--text-muted)">
                    LEGENDA
                </text>
                <line x1="16" y1="38" x2="46" y2="38" stroke={DIAGRAM_FAVORAVEL} strokeWidth="2.5" />
                <text x="54" y="42" fontSize="11" fill="var(--text-muted)">
                    segue para a próxima etapa (há dinheiro envolvido)
                </text>
                <line x1="16" y1="58" x2="46" y2="58" stroke={DIAGRAM_ENCERRA} strokeWidth="2.5" />
                <text x="54" y="62" fontSize="11" fill="var(--text-muted)">
                    encerra ali, sem próxima etapa
                </text>
                <line
                    x1="440"
                    y1="38"
                    x2="470"
                    y2="38"
                    stroke={DIAGRAM_NEUTRAL}
                    strokeWidth="2.5"
                    strokeDasharray="5 4"
                />
                <text x="478" y="42" fontSize="11" fill="var(--text-muted)">
                    censurado — ainda sem desfecho conhecido
                </text>
            </g>
        </svg>
        <p>
            A sequência sentença (1G) → acórdão (2G) e a exceção da "sentença anulada" — que ficaram de fora deste
            diagrama para não poluir a visão geral — estão detalhadas no card{' '}
            <strong>"A regra de precedência sentença → acórdão"</strong> logo abaixo.
        </p>
    </DocCard>
)

const TOC: TocItem[] = [
    { id: 'como-funciona', label: 'Como funciona' },
    { id: 'conceitos', label: 'Conceitos (Kaplan-Meier)' },
    { id: 'fluxo', label: 'Fluxo Estágio 1 → 2 (diagrama)' },
    { id: 'estagio1', label: 'Estágio 1 — eventos' },
    { id: 'estagio2', label: 'Estágio 2 — pagamento' },
    { id: 'indicadores', label: 'Indicadores' },
    { id: 'graficos', label: 'Gráficos' },
    { id: 'limitacoes', label: 'Limitações' },
]

export function SobrevivenciaProcessualDoc() {
    return (
        <DocPage
            title="Sobrevivência Processual"
            tags={['NG', 'LA']}
            note="Dado de pesquisa — direto do LexFlow, com cache"
            toc={TOC}
            intro={
                <>
                    Este guia explica, em detalhe, como cada número desta página é calculado. Diferente dos demais
                    dashboards do LexHub, aqui a base conceitual não é uma regra de negócio simples — é um modelo
                    estatístico de <strong>análise de sobrevivência</strong> (o mesmo ferramental usado em engenharia de
                    confiabilidade para estimar tempo até falha de componentes), aplicado ao tempo de tramitação de
                    processos judiciais.
                </>
            }
        >
            <DocSection
                id="como-funciona"
                title="Como esta página funciona"
                subtitle="De onde vêm os dados e onde o cálculo acontece"
            >
                <InfoBox>
                    A base em si vem de um recorte do LexFlow (processos com data de distribuição preenchida, excluindo
                    os que estão sob segredo de justiça), consultada pela API de dashboards como os demais painéis, com
                    cache de poucos minutos. Os <strong>dados</strong> refletem a base do momento (a data aparece no
                    aviso no topo da página). Já o <strong>cálculo</strong> das curvas de Kaplan-Meier, medianas e
                    rankings roda ao vivo, no seu navegador, toda vez que você muda um filtro — por isso dá pra clicar
                    numa categoria e ver a página inteira recalcular na hora, sem esperar o próximo refresh.
                </InfoBox>
                <DocCard title="Por que existe uma página assim">
                    <p>
                        Esta página é a Fase 2 (exploratória) de um trabalho de pesquisa maior: prever, para um processo
                        recém-contratado, quanto tempo ele deve levar e qual a chance de terminar bem. As fases
                        seguintes (ainda não publicadas aqui) trazem um modelo preditivo de verdade — esta página mostra
                        o que já se sabe hoje, de forma descritiva, sobre a base histórica.
                    </p>
                </DocCard>
            </DocSection>

            <DocSection
                id="conceitos"
                title="Dois conceitos que mudam a leitura de todo o resto"
                subtitle="Censura e mediana de Kaplan-Meier"
            >
                <DocGrid>
                    <DocCard title={'O que é um processo "censurado"'}>
                        <p>
                            "Censurado" não quer dizer erro ou dado faltando — quer dizer que o processo ainda não
                            chegou a nenhum desfecho até a última movimentação registrada. Ele continua contando na
                            análise (sabemos que, até aquela data, ainda estava em andamento), só não sabemos quando nem
                            como vai terminar. Na coorte atual, mais de 40% dos processos estão nessa situação — é por
                            isso que a análise não pode simplesmente "tirar a média" do tempo dos que já terminaram,
                            isso enviesaria o resultado para os casos mais rápidos.
                        </p>
                    </DocCard>
                    <DocCard title="Por que mediana de Kaplan-Meier, não média simples">
                        <p>
                            O estimador de Kaplan-Meier calcula a probabilidade de "ainda estar em tramitação" a cada
                            dia, atualizando essa probabilidade sempre que um evento ou uma censura acontece. A mediana
                            reportada nesta página é o dia em que essa probabilidade cruza 50% — ou seja, o tempo que
                            metade da coorte (contando quem já terminou e ajustando por quem ainda não terminou) leva
                            para ser resolvida. Isso é diferente, e mais correto, do que tirar a média bruta de dias só
                            dos processos que já têm uma data de fim.
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>

            <DocSection
                id="fluxo"
                title="Visão geral: como um processo flui pelos dois estágios"
                subtitle="O mesmo resumo, em forma de diagrama"
            >
                <InfoBox>
                    Antes do detalhe de cada regra (próximas seções), aqui está o mapa inteiro: da distribuição, quatro
                    desfechos possíveis no Estágio 1; só dois deles (Acordo e Mérito Favorável com Proveito) abrem um
                    segundo relógio, o Estágio 2, até o pagamento de fato.
                </InfoBox>
                <FluxoEstagiosDiagram />
            </DocSection>

            <DocSection
                id="estagio1"
                title="Estágio 1 — como um evento é definido"
                subtitle="Distribuição → Acordo, Mérito favorável ou Mérito sem proveito/desfavorável"
            >
                <InfoBox>
                    A partir da data de distribuição (o "dia zero" de cada processo), quatro desfechos são possíveis.
                    Acordo e mérito <strong>não são tratados como uma corrida simples</strong> — existe uma regra de
                    precedência, explicada abaixo.
                </InfoBox>
                <DocGrid>
                    <DocCard title="Acordo">
                        <p>
                            O réu fecha acordo com o escritório antes (ou no mesmo dia) de qualquer decisão de mérito
                            sair. É o único desfecho que compete de verdade pelo "primeiro lugar" — pode interromper a
                            tramitação a qualquer momento, inclusive bem no início.
                        </p>
                    </DocCard>
                    <DocCard title="Mérito favorável com proveito econômico">
                        <p>
                            Sentença (1ª instância) ou acórdão (2ª instância) classificado como <em>"Procedente"</em> ou
                            <em> "Parcialmente procedente"</em>, <strong>com proveito econômico</strong> — ou seja, há
                            valor a receber. Só este grupo segue para o Estágio 2 (pagamento).
                        </p>
                    </DocCard>
                    <DocCard title="Mérito sem proveito ou desfavorável">
                        <p>
                            Sentença/acórdão "Improcedente", "Extinto sem mérito", "Sentença anulada", ou mesmo um
                            resultado "Procedente" <strong>sem proveito econômico</strong> (ganhou a causa, mas não há
                            valor a cobrar — ex.: obrigação de fazer). O processo termina aqui, não há fase de pagamento
                            a acompanhar.
                        </p>
                    </DocCard>
                    <DocCard title="Censurado">
                        <p>
                            Nenhum dos três desfechos acima aconteceu até a data da última movimentação conhecida. O
                            processo segue em tramitação.
                        </p>
                    </DocCard>
                </DocGrid>
                <DocCard title="A regra de precedência sentença → acórdão">
                    <p>
                        Sentença e acórdão não competem entre si — são sequenciais (o acórdão só existe se a sentença
                        foi recorrida). Quando um processo tem acórdão, ele é sempre tratado como o desfecho de mérito
                        válido (substitui a sentença), mesmo que a data cadastrada do acórdão apareça, por erro de
                        registro, anterior à da sentença — isso acontece em cerca de 2% dos processos com acórdão na
                        base atual. Para não distorcer o tempo medido por causa desse erro de cadastro, a data usada é
                        sempre a mais tardia entre as duas (sentença e acórdão), ainda que o tipo do evento seja sempre
                        "acórdão" quando ele existe.
                    </p>
                </DocCard>
            </DocSection>

            <DocSection
                id="estagio2"
                title="Estágio 2 — do mérito favorável ao pagamento"
                subtitle="Ganhar a causa não é o fim: o fim de verdade é o dinheiro entrar"
            >
                <InfoBox>
                    Processos que chegaram em <strong>Acordo</strong> ou{' '}
                    <strong>Mérito favorável com proveito econômico</strong> entram num segundo relógio, que começa a
                    contar a partir da data daquele desfecho (não da distribuição).
                </InfoBox>
                <DocGrid>
                    <DocCard title="Pago">
                        <p>
                            A primeira data preenchida entre: compensação do alvará, compensação do alvará incontroverso
                            (pagamento parcial já liberado mesmo com parte do valor ainda em disputa) ou pagamento do
                            acordo.
                        </p>
                    </DocCard>
                    <DocCard title="Censurado (pagamento)">
                        <p>
                            O processo venceu (ou fechou acordo), mas nenhuma das datas de pagamento acima está
                            preenchida ainda. Está represado na fase de execução/cumprimento.
                        </p>
                    </DocCard>
                </DocGrid>
                <DocCard title={'A seção "04 · Estágio 2" da página'}>
                    <p>
                        Essa seção repete, para o Estágio 2, a mesma profundidade de análise do Estágio 1 — mas o
                        relógio começa a contar a partir da data do mérito favorável/acordo, não da distribuição. Ela
                        mostra 4 cards (elegíveis ao pagamento, mediana até o pagamento, quantos já foram pagos, taxa de
                        pagamento), a curva de Kaplan-Meier de "tempo até pagamento", e dois rankings de gargalo (por
                        tipo de ação e por matéria) com o mesmo teste de log-rank do Estágio 1. Ela também respeita os
                        filtros de escritório/tipo de ação/matéria aplicados mais acima na página — filtrar por uma
                        matéria, por exemplo, restringe tanto o Estágio 1 quanto o Estágio 2 ao mesmo recorte.
                    </p>
                </DocCard>
            </DocSection>

            <DocSection id="indicadores" title="Indicadores (cards)" subtitle="Os 4 números do topo da página">
                <DocGrid>
                    <MetricCard
                        icon="scale"
                        name="Coorte Analisada"
                        what="Quantos processos entraram na análise."
                        counts="Todos os processos com data de distribuição válida, excluindo segredo de justiça e exclusões de limpeza de dados (ver seção Limitações)."
                        calc="Contagem direta, após a limpeza de datas inválidas (sentinelas) e exclusão dos processos sem âncora de tempo (t=0) válida."
                        interpret="É o universo-base de todos os outros números desta página — toda mediana e todo ranking é calculado sobre este grupo."
                    />
                    <MetricCard
                        icon="clock"
                        name="Mediana até Mérito/Acordo"
                        what="Tempo típico, em dias, da distribuição até o primeiro desfecho (qualquer um dos três: acordo, mérito favorável ou mérito sem proveito/desfavorável)."
                        counts="Toda a coorte, incluindo os processos ainda censurados (ainda em tramitação)."
                        calc="Mediana do estimador de Kaplan-Meier — não é a média aritmética dos processos já concluídos."
                        interpret="Quanto menor, mais rápida a esteira está, em média, resolvendo os casos — favoráveis e desfavoráveis juntos."
                    />
                    <MetricCard
                        icon="trendingUp"
                        name="Mérito Favorável c/ Proveito"
                        what="Proporção da coorte que já terminou (ou vai terminar, no caso dos que seguem o mesmo padrão histórico) em mérito favorável com dinheiro a receber."
                        counts="Processos classificados como MÉRITO_FAVORAVEL_COM_PROVEITO, sobre o total da coorte."
                        calc="Contagem simples dividida pelo total da coorte — não é ajustada por Kaplan-Meier, é uma proporção direta no momento do snapshot."
                        interpret="Dá uma ideia do 'batting average' da carteira de processos: de cada 100 casos, quantos já resultaram (ou resultam até aqui) em ganho com valor a cobrar."
                    />
                    <MetricCard
                        icon="dollar"
                        name="Taxa de Pagamento Efetivo"
                        what="Dos processos que já venceram (mérito favorável ou acordo), quantos já foram de fato pagos."
                        counts="Processos com tipo_evento de Estágio 2 igual a PAGO, sobre o total de processos que entraram no Estágio 2 (venceram)."
                        calc="PAGO ÷ (PAGO + CENSURADO_PAGAMENTO)."
                        interpret="Separa 'ganhar a causa' de 'receber o dinheiro'. Uma taxa baixa aqui não significa que o escritório está perdendo processos — significa que a fase de execução/cumprimento ainda está represada para boa parte de quem já venceu."
                        caveat="Esta taxa tende a crescer com o tempo conforme processos recém-vencedores avançam na execução — ela não é uma 'taxa de sucesso final', é uma fotografia do que já foi pago até a data deste snapshot."
                    />
                </DocGrid>
            </DocSection>

            <DocSection id="graficos" title="Gráficos" subtitle="Curvas de sobrevivência e rankings de gargalo">
                <DocGrid>
                    <DocCard title="Curva Geral">
                        <p>
                            Curva de Kaplan-Meier: no eixo X, dias desde a distribuição; no eixo Y, a porcentagem da
                            coorte que ainda está em tramitação (ainda não teve nenhum desfecho) naquele dia. Começa em
                            100% (dia zero, nenhum processo terminou ainda) e cai conforme os processos vão sendo
                            resolvidos. Não distingue desfecho favorável de desfavorável — mede só "ainda em andamento"
                            vs. "já terminou, de qualquer jeito".
                        </p>
                    </DocCard>
                    <DocCard title="Por Tipo de Ação / Matéria / Comarca / Competência (top 6 por volume)">
                        <p>
                            A mesma curva da Curva Geral, uma linha por categoria — 4 dimensões, cada uma mostrando as 6
                            categorias com mais processos no recorte atual: tipo de ação, matéria, comarca (onde o
                            processo tramita) e competência (Juizado Especial, Vara Cível, Turma Recursal etc). Curvas
                            que caem mais rápido (mais perto do canto inferior esquerdo) representam categorias
                            resolvidas mais rapidamente; curvas que demoram a cair são mais lentas. O botão "N ▾" no
                            canto do gráfico liga/desliga linhas individualmente, útil quando muitas categorias deixam o
                            gráfico poluído.
                        </p>
                    </DocCard>
                    <DocCard title="Ranking de gargalos — Tipo de Ação / Matéria / Comarca / Competência">
                        <p>
                            Barras com a mediana de Kaplan-Meier de dias até o desfecho, uma barra por categoria,
                            ordenadas da mais lenta para a mais rápida. Categorias com barra maior são as que mais
                            "engargalam" a esteira — onde vale investir esforço de triagem, priorização ou automação. Só
                            entram no ranking categorias com pelo menos 30 processos (para evitar medianas instáveis com
                            amostra pequena) e com mediana calculável (categorias onde menos de 50% dos casos já teve
                            desfecho não entram, pois a mediana ainda não existe estatisticamente).
                        </p>
                    </DocCard>
                    <DocCard title="Clicar numa barra filtra a página inteira">
                        <p>
                            Clicar numa categoria de Tipo de Ação, Matéria, Comarca ou Competência recalcula{' '}
                            <strong>todos os outros</strong> números da página (os 4 cards, a Curva Geral e as demais
                            comparações) só para os processos daquela categoria — dá pra combinar os quatro filtros ao
                            mesmo tempo (ex.: "MORA" + "Procedimento Comum Cível" + "MANAUS"). Uma regra importante
                            evita um efeito confuso: o próprio gráfico de onde você clicou <strong>não</strong> se
                            autofiltra pela sua própria seleção — ele sempre mostra todas as categorias (respeitando os
                            outros filtros ativos), só destacando a escolhida, justamente para você poder clicar numa
                            categoria diferente em seguida sem precisar limpar o filtro primeiro. Clique de novo na
                            mesma barra (ou no X do aviso abaixo dos gráficos) para remover aquele filtro.
                        </p>
                    </DocCard>
                    <DocCard title="Seção 05 — Fase, Subfase, Juiz (1G) e Relator (2G): exploratório, não clicável">
                        <p>
                            Essas 4 dimensões aparecem como ranking descritivo no fim da página, mas{' '}
                            <strong>não</strong> viram filtro de página e não entram como covariável do Cox/Fine-Gray
                            (Fase 3). O motivo: fase e subfase (status processual) refletem o estado <em>atual</em> do
                            processo — não um atributo fixado na distribuição — e juiz (1G)/relator (2G) só são
                            preenchidos depois que a sentença/acórdão já aconteceu naquela instância. Usar esses campos
                            como se fossem conhecidos desde o início introduziria viés de causalidade reversa
                            (lookahead). O ranking de juiz, por exemplo, só considera processos já decididos por
                            sentença em 1º grau — é descritivo daquele subgrupo, não do universo todo.
                        </p>
                    </DocCard>
                    <DocCard title="Teste de log-rank — a barra verde embaixo dos rankings">
                        <p>
                            Olhar duas barras com medianas diferentes não prova, por si só, que a diferença é real —
                            poderia ser coincidência da amostra. O <strong>teste de log-rank</strong> (o mesmo usado em{' '}
                            <Code>lifelines.statistics.multivariate_logrank_test</Code> em Python e no{' '}
                            <Code>survdiff()</Code> do R) compara as curvas de sobrevivência de todas as categorias do
                            ranking ao mesmo tempo e devolve três números: um <strong>χ² (qui-quadrado)</strong>, os{' '}
                            <strong>graus de liberdade</strong> (sempre número de categorias − 1) e um{' '}
                            <strong>p-valor</strong>. Quando o p-valor é menor que 0,05, a diferença entre as categorias
                            é considerada estatisticamente significativa — ou seja, não é só ruído de amostra. Esse
                            teste é recalculado no navegador a cada filtro aplicado, sobre exatamente as mesmas
                            categorias e processos mostrados no ranking acima dele (por isso o resultado muda quando
                            você aplica um filtro de Matéria ou Tipo de Ação).
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>

            <DocSection
                id="limitacoes"
                title="Limitações e tratamento de dados"
                subtitle="O que foi corrigido na extração, e o que ainda não dá para concluir"
            >
                <WatchBox>
                    Durante a extração desta coorte, foram encontrados e corrigidos dois bugs reais de dados: (1) um
                    "timestamp zero" (31/12/1969, o epoch Unix convertido para o fuso de Manaus) em algumas datas de
                    contratação (campo que não é mais o "dia zero" — a distribuição em si não tem nenhum caso desse
                    sentinela específico, e só 2 processos fora da janela de validade no total, vs. 19 em contratação),
                    e (2) datas com ano de 5 dígitos (ex.: "20263") em algumas sentenças/acórdãos, por bug de
                    formulário. Qualquer data fora da janela plausível (1971 até hoje + 2 anos) é tratada como inválida
                    nesta extração de pesquisa, em qualquer um dos campos de data; processos sem data de distribuição
                    válida são excluídos da coorte por completo, pois não têm "dia zero" confiável. Isso não corrige o
                    dado na origem (LexFlow) — só evita que o erro contamine esta análise.
                </WatchBox>
                <DocGrid>
                    <DocCard title="UF não aparece nesta página">
                        <p>
                            Cerca de 98,5% da coorte é do Amazonas. As demais UFs têm volume baixo demais para uma
                            mediana confiável (algumas nem chegam a ter metade dos casos resolvidos, o que torna a
                            mediana de Kaplan-Meier matematicamente indefinida) — por isso essa quebra não é exibida
                            aqui, para não sugerir uma conclusão que os dados não sustentam.
                        </p>
                    </DocCard>
                    <DocCard title="Correlação, não causa">
                        <p>
                            Um tipo de ação aparecer como "mais lento" no ranking não prova, por si só, que o tipo de
                            ação em si causa a demora — pode refletir, por exemplo, a comarca ou a competência onde
                            esses casos tramitam com mais frequência. Desde 13/10/2026, o Cox/Fine-Gray da Fase 3 (fora
                            desta página) já controla por comarca e competência junto com tipo de ação, matéria, valor
                            de causa e escritório — mas fase, subfase, juiz e relator ficam de fora do modelo formal
                            (ver seção 05 acima) por serem estado pós-desfecho do processo, não um atributo fixo na
                            distribuição.
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>
        </DocPage>
    )
}
