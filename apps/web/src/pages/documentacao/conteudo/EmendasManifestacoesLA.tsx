import {
    DocCallout,
    DocFeature,
    DocGrid,
    DocMini,
    DocPage,
    DocSection,
    Formula,
    Hl,
    MetricCard,
    type TocItem,
} from '../components/DocParts.tsx'

// Guia trazido da v1: LexHub/src/pages/documentacao/EmendasManifestacoes_LA.tsx (convertido para as peças da V2).

const TOC: TocItem[] = [
    { id: 'como-funciona', label: 'Como funciona' },
    { id: 'indicadores', label: 'Indicadores do período' },
    { id: 'atividades', label: 'Classificação de atividades' },
    { id: 'comissao', label: 'Comissionamento' },
    { id: 'graficos', label: 'Gráficos e histórico' },
    { id: 'filtros', label: 'Filtros' },
]

const FILTERS = [
    {
        name: 'Funcionários',
        badge: 'Pessoas',
        desc: 'Restringe às tarefas de um ou mais funcionários. Também é aplicado clicando em "Demandas por funcionário" ou na média diária.',
    },
    {
        name: 'Atividade',
        badge: 'Clique no gráfico',
        desc: 'Filtra por uma ou mais atividades do setor. É aplicado clicando no gráfico "Por atividade" e aparece nas etiquetas de filtro.',
    },
    {
        name: 'Situação do processo',
        badge: 'Processo',
        desc: 'Ativo, Suspenso / Sobrestado ou Arquivado — é a situação do processo, não da tarefa. Sem escolha, entram todas.',
    },
]

export function EmendasManifestacoesLADoc() {
    return (
        <DocPage
            title="Emendas e Manifestações — LA"
            tags={['LA']}
            toc={TOC}
            intro={
                <>
                    Este guia explica cada número, gráfico e regra de comissão do dashboard de Emendas e Manifestações —
                    as tarefas do setor <strong>INTERMEDIÁRIAS</strong> da unidade LA (emendas, manifestações, dilação
                    de prazo e afins).
                </>
            }
            header={
                <DocCallout caps title="Uma linha, uma tarefa do setor INTERMEDIÁRIAS" badge="18 atividades">
                    <p>
                        Cada linha é uma tarefa (agendamento) do setor "INTERMEDIÁRIAS" — o mais amplo dos três
                        dashboards desta família, com 18 atividades diferentes. O responsável exibido depende de a
                        tarefa estar encerrada ou não:
                    </p>
                    <DocGrid cols={2}>
                        <DocMini label="Tarefa encerrada">
                            O responsável é sempre quem <Hl>encerrou</Hl> a tarefa.
                        </DocMini>
                        <DocMini label="Tarefa ainda aberta">
                            O responsável é quem está <Hl tone="info">atribuído</Hl> a ela no momento.
                        </DocMini>
                    </DocGrid>
                </DocCallout>
            }
        >
            <DocSection
                id="como-funciona"
                title="01 — Como o dashboard funciona"
                subtitle="O setor INTERMEDIÁRIAS e as duas visões da tela"
            >
                <h3 className="doc-h3">Duas visões da mesma tela</h3>
                <DocGrid cols={2}>
                    <DocFeature title="Por prazo (padrão)" tone="info" icon="calendar" badge="Padrão" framed>
                        <p>
                            A página abre nesta visão. Todos os cartões olham para o <strong>prazo</strong> da tarefa —
                            é também o eixo usado pelo comissionamento.
                        </p>
                    </DocFeature>
                    <DocFeature title="Concluídas" tone="ok" icon="check-circle" badge="Conclusão" framed>
                        <p>
                            Total/Em andamento usam a data de <strong>criação</strong>; Concluídas usa a data de
                            <strong> encerramento</strong>.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="indicadores"
                title="02 — Indicadores do período"
                subtitle="Os cartões de resumo no topo do dashboard"
            >
                <DocGrid>
                    <MetricCard
                        icon="fileText"
                        name="Total"
                        what="Volume de tarefas ativas do setor abertas no período."
                        counts='Tarefas que não estão em "Encerrado Cumprido", "Encerrado Não Cumprido", "Cancelado" nem "Concluído".'
                        calc="Contagem das tarefas ativas cuja data de criação cai dentro do período selecionado."
                        interpret="Mostra o volume de entrada de trabalho no setor durante o período."
                    />
                    <MetricCard
                        icon="clock"
                        name="Em andamento"
                        what="Das tarefas do Total, quantas estão em algum status ativo."
                        counts='Qualquer status ativo: "Recebido", "Visualizado", "Iniciado", "Reaberto" ou "Encaminhado".'
                        calc="Como o Total já exclui as encerradas/canceladas, este número normalmente coincide com o Total."
                        interpret="Não é um alerta de atraso — é só a confirmação de que a tarefa segue ativa."
                        caveat='Diferente de Pendências Intermediárias: aqui todos os status ativos contam, por isso "Em andamento" tende a ser igual ao Total.'
                    />
                    <MetricCard
                        icon="alert"
                        name="Vencidas"
                        what="Tarefas ativas cujo prazo já passou, hoje."
                        counts="Tarefas ativas com prazo anterior à data de hoje, independente de quando foram criadas."
                        calc="Na visão Concluídas, é comparação direta com a data de hoje e não depende do período filtrado. Na visão Por prazo, conta só as tarefas com prazo dentro do período."
                        interpret="Indicador de urgência: qualquer valor acima de zero merece atenção."
                    />
                    <MetricCard
                        icon="clock"
                        name="Vencem hoje"
                        what="Tarefas ativas cujo prazo é exatamente hoje."
                        counts="Tarefas ativas com prazo igual à data de hoje."
                        calc="Mesma lógica de Vencidas (inclusive a diferença entre as visões), comparando prazo = hoje."
                        interpret="Ajuda a priorizar o que precisa ser resolvido ainda no dia."
                    />
                    <MetricCard
                        icon="check"
                        name="Concluídas"
                        what="Tarefas encerradas no período — contagem separada do Total."
                        counts='Status "Encerrado Cumprido" ou "Encerrado Não Cumprido" com data de encerramento no período.'
                        calc="Contagem direta dos registros encerrados no período."
                        interpret="Mede a produção efetiva de fechamento do setor."
                    />
                </DocGrid>
            </DocSection>

            <DocSection
                id="atividades"
                title="03 — Classificação de atividades"
                subtitle="Quais atividades geram peça remunerada"
            >
                <DocGrid cols={3}>
                    <DocFeature title="Manifestação" tone="ok" icon="fileText" badge="Comissiona" framed>
                        <p>
                            Emenda à Inicial · Manifestação (5D/10D/15D) · Manifestação Custas de Citação · Manifestação
                            Remessa 2 Grau · Man Hipo Recurso · Man Hipossuficiência · Man Desnecessidade de Audiência ·
                            Man Interposição Agravo · Pedido de Celeridade · Pedido Sustentação Oral
                        </p>
                    </DocFeature>
                    <DocFeature title="Dilação" tone="info" icon="clock" badge="Comissiona" framed>
                        <p>Dilação de Prazo</p>
                    </DocFeature>
                    <DocFeature title="Não comissionável" tone="neutral" icon="ban" badge="Sem comissão" framed>
                        <p>
                            Avaliar Manifestação (Int) · Confecção (Int) · Provas a Produzir · Verificar Não Cumprimento
                            (Intermediárias) · Alegações Finais
                        </p>
                    </DocFeature>
                </DocGrid>
                <DocCallout tone="neutral" title="Não comissionável ainda conta na agenda">
                    <p>
                        Atividades não comissionáveis ainda contam para a agenda do funcionário quando encerradas — só
                        não geram peça paga.
                    </p>
                </DocCallout>
            </DocSection>

            <DocSection
                id="comissao"
                title="04 — Comissionamento"
                subtitle="Faixas por percentual de agenda cumprida"
                tone="ok"
                badge="3 faixas"
            >
                <DocCallout tone="info" title="A faixa vem da agenda do mês" badge="Agenda cumprida">
                    <p>
                        A comissão depende de quanto da <strong>agenda do mês</strong> o funcionário fechou — não é por
                        peça isolada. Agenda do mês = tarefas do funcionário com prazo no período (Cancelado e Concluído
                        não entram). Uma tarefa conta como "finalizada" se foi encerrada como Cumprido <em>ou</em> Não
                        Cumprido.
                    </p>
                </DocCallout>

                <h3 className="doc-h3">Faixas de comissão</h3>
                <DocGrid cols={3}>
                    <DocFeature title="Inelegível" tone="danger" icon="ban" badge="abaixo de 85%" framed>
                        <p>
                            <Hl tone="danger" mono>
                                R$ 0,00
                            </Hl>{' '}
                            por Manifestação ·{' '}
                            <Hl tone="danger" mono>
                                R$ 0,00
                            </Hl>{' '}
                            por Dilação
                        </p>
                    </DocFeature>
                    <DocFeature title="Faixa 1" tone="warn" icon="target" badge="85% a 96,9%" framed>
                        <p>
                            <Hl tone="warn" mono>
                                R$ 1,00
                            </Hl>{' '}
                            por Manifestação ·{' '}
                            <Hl tone="warn" mono>
                                R$ 0,25
                            </Hl>{' '}
                            por Dilação
                        </p>
                    </DocFeature>
                    <DocFeature title="Faixa 2" tone="ok" icon="star" badge="97% ou mais" framed>
                        <p>
                            <Hl tone="ok" mono>
                                R$ 1,50
                            </Hl>{' '}
                            por Manifestação ·{' '}
                            <Hl tone="ok" mono>
                                R$ 0,50
                            </Hl>{' '}
                            por Dilação
                        </p>
                    </DocFeature>
                </DocGrid>

                <p>
                    A faixa alcançada vale para <strong>todas</strong> as peças do funcionário no período — não é
                    progressivo peça a peça. Só conta como peça paga a tarefa com status "Encerrado Cumprido" e prazo no
                    período (mesmo eixo da agenda); "Encerrado Não Cumprido" soma na agenda, mas não gera pagamento.
                </p>

                <DocCallout tone="violet" icon="check-circle" title="Validado contra a produção real" badge="jun/2026">
                    <p>Validado contra a produção real de uma funcionária em jun/2026, confirmando Faixa 2:</p>
                    <Formula>484 manifestações × 1,50 + 29 dilações × 0,50 = R$ 740,50</Formula>
                    <p>
                        A implementação original usava a data de encerramento e contava Não Cumprido como peça paga —
                        dava valores errados; a regra correta usa o prazo e só conta "Encerrado Cumprido".
                    </p>
                </DocCallout>
                <DocCallout tone="info" icon="lock" title="Quem vê">
                    <p>
                        O relatório de comissão (PDF) só aparece para quem tem acesso total à unidade ou à organização.
                    </p>
                </DocCallout>
            </DocSection>

            <DocSection
                id="graficos"
                title="05 — Gráficos e histórico"
                subtitle="Distribuição do trabalho e evolução no tempo"
            >
                <DocGrid cols={2}>
                    <DocFeature title="Encerradas por atividade" icon="barChart" badge="Clicável" badgeTone="ok">
                        <p>
                            Tarefas encerradas (Cumprido ou Não Cumprido) no período, agrupadas por atividade — usa a
                            mesma base do KPI "Concluídas", para os números baterem entre si.
                        </p>
                    </DocFeature>
                    <DocFeature title="Demandas por funcionário" icon="users" badge="Clicável" badgeTone="ok">
                        <p>Tarefas encerradas no período por funcionário, separadas em Cumprido e Não Cumprido.</p>
                    </DocFeature>
                    <DocFeature
                        title="Concluídas por mês / por dia"
                        icon="calendar"
                        badge="Drill-down"
                        badgeTone="info"
                    >
                        <p>
                            Histórico de encerramentos ao longo do tempo, com detalhamento por funcionário no
                            drill-down.
                        </p>
                    </DocFeature>
                    <DocFeature title="Média diária por funcionário" icon="trendingUp">
                        <p>
                            Total encerrado por funcionário dividido pelos dias distintos (com prazo ou conclusão) em
                            que ele encerrou algo, <strong>dentro do período</strong>.
                        </p>
                    </DocFeature>
                </DocGrid>
                <DocCallout tone="ok" icon="filter" title="Clique para filtrar a página">
                    <p>
                        Clicar numa barra dos gráficos "por atividade" ou "por funcionário" aplica o filtro
                        correspondente em toda a página, inclusive nos KPIs e no comissionamento.
                    </p>
                </DocCallout>
            </DocSection>

            <DocSection
                id="filtros"
                title="06 — Filtros disponíveis"
                subtitle="Como personalizar a lista de tarefas"
                tone="info"
            >
                <DocGrid cols={2}>
                    {FILTERS.map((f) => (
                        <DocFeature key={f.name} title={f.name} badge={f.badge} badgeTone="info">
                            <p>{f.desc}</p>
                        </DocFeature>
                    ))}
                </DocGrid>
                <p>A tabela de tarefas também mostra o número do processo (formato CNJ) quando disponível.</p>
            </DocSection>
        </DocPage>
    )
}
