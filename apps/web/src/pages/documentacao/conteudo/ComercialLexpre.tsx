import { useParams } from 'react-router'
import { rememberedUnit } from '../../../lib/activeUnit.ts'
import {
    Code,
    DashLink,
    DocCallout,
    DocChange,
    DocChips,
    DocFeature,
    DocGrid,
    DocLink,
    DocMini,
    DocNote,
    DocPage,
    DocPanel,
    DocRelation,
    DocSection,
    Hl,
    MetricCard,
    type DocChip,
    type TocItem,
} from '../components/DocParts.tsx'

// Guia do Comercial (LexPre). Texto da v1: LexHub/src/pages/documentacao/Comercial_Lexpre.tsx.

const TOC: TocItem[] = [
    { id: 'como-funciona', label: 'Como funciona' },
    { id: 'meta-anual', label: 'Meta Anual' },
    { id: 'captacao', label: 'Captação por Origem' },
    { id: 'performance', label: 'Leads e performance' },
    { id: 'protocolos', label: 'Protocolos & Rubricas' },
    { id: 'meta-atendente', label: 'Meta por Atendente' },
    { id: 'filtros', label: 'Filtros' },
    { id: 'limitacoes', label: 'Diferenças para o legado' },
]

// Meta trimestral por atendente de cada escritório (a única diferença de negócio entre NG e LA).
const META_TRIMESTRE: Record<string, string> = { NG: 'R$ 12 mi', LA: 'R$ 15 mi' }

const CANAIS: DocChip[] = [
    { label: 'Campanha', tone: 'accent' },
    { label: 'Redes Sociais' },
    { label: 'Retorno' },
    { label: 'Resgate' },
    { label: 'Indicação' },
    { label: 'Site' },
    { label: 'Parceiros', tone: 'info' },
    { label: 'Externos', tone: 'violet' },
]

export function ComercialLexpreDoc() {
    const { org = '' } = useParams()
    const unit = rememberedUnit(org)?.toUpperCase() ?? null
    const meta = unit ? META_TRIMESTRE[unit] : undefined

    return (
        <DocPage
            title="Comercial (LexPre)"
            tags={['NG', 'LA']}
            note={
                <>
                    Banco <Code>lexpre</Code> — base nova, em construção
                </>
            }
            toc={TOC}
            intro={
                <>
                    Este guia explica cada número e gráfico do dashboard Comercial a partir da nova base de dados (banco{' '}
                    <Code>lexpre</Code>), partindo diretamente das tabelas <Code>public.atendimento</Code> e{' '}
                    <Code>public.demandas</Code> — diferente dos demais dashboards lexpre (Pendências, Organização de
                    Documentos, Peticionamento, Protocolo), que leem o log de movimentação de setor.{' '}
                    <strong>Nenhum conhecimento técnico é necessário.</strong>
                </>
            }
            header={
                <DocCallout
                    caps
                    title="Escopo multi-unidade & fórmula compartilhada"
                    badge={meta && `Unidade ativa: ${unit} · Meta ${meta}/trimestre`}
                >
                    <p>
                        Este guia vale para o <DashLink dashboard="comercial-lexpre">Comercial (LexPre)</DashLink> em
                        todas as unidades (troque a unidade no seletor da barra lateral). Ele utiliza a{' '}
                        <strong>mesma query e a mesma fórmula de comissão</strong> documentada no dashboard irmão{' '}
                        <DocLink to="comissao-lexpre">Comissão Comercial</DocLink>.
                    </p>
                    <DocGrid>
                        <DocMini label="Única diferença de negócio">
                            A <strong>Meta por Atendente</strong> varia por escritório: <Hl mono>R$ 12 mi/trimestre</Hl>{' '}
                            no <strong>NG</strong> vs.{' '}
                            <Hl tone="info" mono>
                                R$ 15 mi/trimestre
                            </Hl>{' '}
                            no <strong>LA</strong>.
                        </DocMini>
                        <DocMini label="Filtragem por escritório">
                            Não depende dos blocos de <Code>setor_id</Code> do log de movimentação; o filtro vem direto
                            da coluna <Code>atendimento.escritorio_id</Code>.
                        </DocMini>
                    </DocGrid>
                </DocCallout>
            }
        >
            <DocSection
                id="como-funciona"
                title="01 — Como o dashboard funciona"
                subtitle="Origem dos dados, modelo relacional e regra de datas entre assinatura e protocolo"
            >
                <DocPanel>
                    <DocRelation
                        cardinality="1 : N"
                        caption="ações vinculadas"
                        left={{
                            name: 'public.atendimento',
                            badge: '1 por cliente',
                            tone: 'info',
                            keyLabel: 'Chave temporal (Seção 03):',
                            keyValue: 'Data de Assinatura',
                            children: (
                                <>
                                    Representa o atendimento comercial do cliente. Armazena{' '}
                                    <strong>data de assinatura</strong>, canal de origem, escritório (
                                    <Code>escritorio_id</Code>) e UF.
                                </>
                            ),
                        }}
                        right={{
                            name: 'public.demandas',
                            badge: 'N por cliente',
                            tone: 'ok',
                            keyLabel: 'Chave temporal (Seção 05):',
                            keyValue: 'Data de Protocolo',
                            children: (
                                <>
                                    Cada demanda (ação judicial) vinculada ao atendimento. Guarda{' '}
                                    <strong>rubrica</strong>, <strong>valor de causa</strong>, status de protocolo e
                                    cancelamento.
                                </>
                            ),
                        }}
                    />
                    <DocCallout
                        tone="warn"
                        icon="clock"
                        title="Por que os totais de Contratos e Protocolados podem divergir no mesmo mês?"
                    >
                        <p>
                            A maioria dos cards filtra pela <strong>data de assinatura</strong> do atendimento, mas os
                            cards de protocolo (Seção 05) usam a <strong>data de protocolo</strong> da demanda. Por isso
                            um cliente pode aparecer em "Total Contratos" num mês e só entrar em "Protocolados" num mês
                            diferente.
                        </p>
                    </DocCallout>
                    <DocFeature
                        title='Comissão vem "de brinde" nessa mesma consulta'
                        tone="ok"
                        badge="Sem chamada extra"
                    >
                        <p>
                            O endpoint que alimenta este dashboard já calcula, junto com as métricas comerciais, todos
                            os campos de comissão (comissão base, Fator Multiplicador, proporcionais por estado,
                            desconto de cancelamento tardio) — é a mesma resposta consumida pelo dashboard{' '}
                            <DocLink to="comissao-lexpre">Comissão Comercial (LexPre)</DocLink>, que só exibe esses
                            campos numa página separada. Não há chamada nem cálculo duplicado entre os dois.
                        </p>
                    </DocFeature>
                </DocPanel>
            </DocSection>

            <DocSection
                id="meta-anual"
                title="02 — Meta Anual"
                subtitle="Progresso do valor de causa protocolado contra a meta anual da empresa"
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
                <DocNote date="21/09/2026">
                    Adicionado em <strong>21/09/2026</strong> (Meta Anual) e ampliado no mesmo dia para a{' '}
                    <a className="doc-link" href="#meta-atendente">
                        Meta por Atendente
                    </a>
                    . O card <strong>não quebra a soma</strong> em <Code>"R$ X lexpre + R$ Y legado"</Code> — exibe
                    diretamente o <Hl tone="ok">total combinado</Hl> para refletir o progresso real de 2026.
                </DocNote>
            </DocSection>

            <DocSection
                id="captacao"
                title="03 — Captação por Origem"
                subtitle="Clientes que assinaram contrato no período, segmentados por canal de aquisição"
                badge="Cards clicáveis (filtro cruzado)"
            >
                <DocPanel>
                    <DocChips label="8 canais rastreados:" items={CANAIS} />
                    <p>
                        Clicar em qualquer card de canal filtra a página inteira por aquele segmento (clicar novamente
                        remove o filtro). Diferente do legado: <strong>"Campanha"</strong> unifica RA e NG (a Campanha
                        RA está sendo descontinuada), e <strong>"Externos"</strong> tem card próprio, separado de{' '}
                        <strong>"Parceiros"</strong> — não são mais somados juntos.
                    </p>
                </DocPanel>
                <DocGrid>
                    <MetricCard
                        name="Total Contratos"
                        icon="trendingUp"
                        what="Soma de todos os contratos assinados no período, de todas as origens."
                        counts="Contagem de atendimentos com data de assinatura dentro do período, somando Campanha + Indicação + Retorno + Resgate + Redes Sociais + Site + Parceiros + Externos."
                        calc="Contagem direta, sem filtro de canal."
                        interpret="Visão consolidada da captação comercial no período."
                    />
                    <MetricCard
                        name="Ações Fechadas"
                        icon="trendingUp"
                        what="Total de demandas (ações) fechadas no período, de clientes que assinaram contrato."
                        counts="Demandas de atendimentos assinados no período, excluindo as canceladas. O subtítulo mostra quantas dessas são 'rubricas reunidas' (pacotes que agrupam várias rubricas associadas, ex.: RUBRICAS_BRADESCO)."
                        calc="Contagem direta das demandas não canceladas."
                        interpret="Quanto maior, mais volume de trabalho jurídico gerado pela captação do período."
                        caveat="O lexpre ainda não modela reajuizamento — diferente do dashboard Comercial NG legado, este card não desconta reajuizamentos."
                    />
                    <MetricCard
                        name="Cancelados"
                        icon="trendingUp"
                        what="Demandas canceladas no período, de clientes que assinaram contrato."
                        counts="Contagem de demandas (não de atendimentos) com status de cancelamento, dentro do período."
                        calc="Contagem direta — um mesmo cliente pode ter mais de uma demanda, e só uma ser cancelada."
                        interpret="Ajuda a identificar concentração de cancelamento em algum período ou canal."
                    />
                    <MetricCard
                        name="Aproveitamento"
                        icon="trendingUp"
                        what="Quantas ações fecham, em média, por cliente assinado no período."
                        counts="Razão entre Ações Fechadas e Total Contratos do período."
                        calc="Ações Fechadas ÷ Total Contratos — não é percentual, é uma razão (ex.: 1,4 ações por cliente)."
                        interpret="Quanto maior, mais demandas em média cada cliente novo está gerando."
                    />
                </DocGrid>
            </DocSection>

            <DocSection
                id="performance"
                title="04 — Leads e performance"
                subtitle="Funil de conversão e produtividade diária da equipe comercial"
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
                <DocGrid cols={2}>
                    <DocFeature title="Ranking de Ações Fechadas" tone="accent" badge="Race Chart · Clicável">
                        <p>
                            Gráfico de corrida ordenado por atendente. Clicar em um colaborador filtra{' '}
                            <strong>a página inteira</strong> pelo atendente selecionado.
                        </p>
                    </DocFeature>
                    <DocFeature title="Ações / Contratos Diários" tone="info" badge="Mapas de Calor">
                        <p>
                            Mapas de calor diários destacando a intensidade de produção e os{' '}
                            <strong>3 atendentes mais ativos</strong> de cada dia, atualizados em tempo real (sem filtro
                            de período).
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="protocolos"
                title="05 — Protocolos & Distribuição por Rubrica"
                subtitle="Indicadores baseados na data de protocolo da demanda e composição por matéria"
                tone="ok"
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
                        icon="dollar"
                        what="Volume financeiro (em valor de causa) protocolado no período, e a média por demanda."
                        counts="Soma do valor de causa das demandas protocoladas no período; o Ticket Médio divide essa soma pela quantidade de Protocolados."
                        calc="Soma direta / divisão simples."
                        interpret="Mede o volume financeiro que entrou em protocolo, não só a quantidade de processos."
                    />
                    <MetricCard
                        name="Tempo Médio até o Protocolo"
                        icon="clock"
                        what="Quantos dias/horas, em média, uma demanda leva da assinatura até o protocolo."
                        counts="Diferença entre a data de assinatura do atendimento e a data de protocolo da demanda, para as demandas protocoladas no período."
                        calc="Média simples das diferenças, em horas (exibido formatado)."
                        interpret="Indicador de velocidade do fluxo pré-protocolo — quanto menor, mais rápido o cliente sai da assinatura e entra no processo."
                        caveat="A demanda não tem data própria de criação no lexpre, então a base de início usada é sempre a data de assinatura do atendimento."
                    />
                    <MetricCard
                        name="Fila de Demandas no Pré-Protocolo / Valor de Causa por Atendente"
                        icon="layers"
                        what="Onde estão hoje as demandas não canceladas que ainda não foram protocoladas, por atendente e estágio do fluxo."
                        counts="Demandas não canceladas cujo status de protocolo ainda não foi atingido, classificadas em um bucket (Pendências, Triagem, Não Confeccionado, Não Protocolado, Não Organizado) — mesma lógica reaproveitada do dashboard Protocolo (LexPre)."
                        calc="Gráfico empilhado por atendente e bucket; o segundo gráfico soma o valor de causa dessas mesmas demandas, separando Protocolado x Não Protocolado."
                        interpret="Mostra onde o trabalho pendente está represado no funil — e para quem."
                    />
                    <MetricCard
                        name="Total de Rubricas (gráfico de pizza)"
                        icon="pieChart"
                        what="Como as ações fechadas do período se distribuem entre as diferentes rubricas."
                        counts="Ações fechadas no período, agrupadas por rubrica — o seletor 'Origem' no cabeçalho do card restringe a mesma pizza a um canal específico (Campanha, Site, etc.) em vez do total."
                        calc="Contagem por rubrica, dentro do recorte de canal escolhido."
                        interpret="Ajuda a identificar quais tipos de ação dominam a captação, e se isso muda por canal."
                        caveat="Clicar numa fatia filtra a PÁGINA INTEIRA por aquela rubrica (não só o gráfico) — o mesmo mecanismo de clique usado nos cards 'por atendente'. Clicar de novo na mesma fatia remove o filtro."
                    />
                </DocGrid>
            </DocSection>

            <DocSection
                id="meta-atendente"
                title="06 — Meta por Atendente"
                subtitle="Desempenho individual contra a meta do trimestre ou semestre selecionado"
                badge={meta && `Meta ${unit}: ${meta} / trimestre`}
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
                <DocGrid cols={2}>
                    <DocFeature
                        title="Merge por primeiro nome (risco conhecido)"
                        tone="danger"
                        icon="alert"
                        badge="LexPre + Legado"
                        framed
                    >
                        <p>
                            Como não há id compartilhado entre as tabelas de funcionário do <Code>lexpre</Code> e do
                            banco legado, a soma por atendente é feita cruzando o <strong>primeiro nome</strong>.
                            Homônimos (dois atendentes com o mesmo primeiro nome, num banco ou nos dois) têm seus
                            valores somados — critério já adotado internamente em cada banco.
                        </p>
                    </DocFeature>
                    <DocFeature
                        title="Meta Inteligente (card separado)"
                        tone="ok"
                        icon="target"
                        badge="Stretch Goal"
                        framed
                    >
                        <p>
                            Calcula uma <strong>meta sugerida individual</strong> a partir do histórico de meses
                            anteriores (com <em>stretch goal</em> configurável), distribuindo proporcionalmente a meta
                            global do período entre os colaboradores ativos.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="filtros"
                title="07 — Filtros disponíveis"
                subtitle="Como personalizar e cruzar a visão do dashboard"
                tone="info"
            >
                <DocGrid cols={3}>
                    <DocFeature title="Período" badge="Duplo eixo" badgeTone="accent">
                        <p>
                            Filtra a maioria dos cards pela <strong>data de assinatura</strong> do atendimento — os
                            cards de Protocolo usam a <Hl tone="ok">data de protocolo</Hl> da demanda.
                        </p>
                    </DocFeature>
                    <DocFeature title="Funcionários" badge="Topo + Clique" badgeTone="info">
                        <p>
                            Restringe a visão a um ou mais atendentes pelo seletor superior ou clicando em gráficos{' '}
                            <em>"por atendente"</em> (Ranking, Fila de Pré-Protocolo, Valor de Causa).
                        </p>
                    </DocFeature>
                    <DocFeature title="Área de atuação" badge="public.area_atuacao" badgeTone="neutral">
                        <p>
                            Filtra pela área vinculada à rubrica da demanda. Hoje opera com <strong>CONSUMIDOR</strong>;{' '}
                            <strong>ADMINISTRATIVO</strong> aparecerá conforme novas operações forem cadastradas.
                        </p>
                    </DocFeature>
                    <DocFeature title="UF" badge="customer.uf" badgeTone="neutral">
                        <p>
                            Filtra pelo estado do cliente a partir do catálogo único de endereçamento (
                            <Code>customer.uf</Code>), reaproveitado por todos os dashboards lexpre.
                        </p>
                    </DocFeature>
                    <DocFeature title="Rubrica" badge="Cross-filter Donut" badgeTone="accent" wide>
                        <p>
                            Clicar em uma fatia do gráfico <strong>"Distribuição por Rubrica"</strong> filtra
                            instantaneamente toda a página pela matéria selecionada.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="limitacoes"
                title="08 — Diferenças para o dashboard legado (banco ng)"
                subtitle="O que já existe, o que ainda não existe e o motivo de cada decisão"
                tone="danger"
            >
                <DocGrid cols={3}>
                    <DocChange status="Em evolução" area="Demandas" title="Sem reajuizamento">
                        <p>
                            O <Code>lexpre</Code> ainda não modela o conceito de reajuizamento nas demandas — por isso,
                            o card <strong>"Ações Fechadas"</strong> não desconta reajuizamentos como o dashboard
                            Comercial NG legado fazia.
                        </p>
                    </DocChange>
                    <DocChange status="Simplificado" tone="info" area="Canais" title="Campanha RA descontinuada">
                        <p>
                            O legado distinguia <em>Campanha RA</em> de <em>Campanha NG</em>; essa distinção está sendo
                            descontinuada e o <Code>lexpre</Code> já trata ambos como um único canal{' '}
                            <strong>"Campanha"</strong>.
                        </p>
                    </DocChange>
                    <DocChange
                        status="Híbrido 2026"
                        tone="ok"
                        area="Metas"
                        title="Meta Anual e por Atendente somam com o legado"
                        framed
                    >
                        <p>
                            Como os dados de 2026 estão divididos entre o <Code>lexpre</Code> e o banco legado (migração
                            gradual), os dois cards de meta <strong>somam ambas as bases</strong> para não exibir apenas
                            uma fração do progresso real.
                        </p>
                    </DocChange>
                </DocGrid>
            </DocSection>
        </DocPage>
    )
}
