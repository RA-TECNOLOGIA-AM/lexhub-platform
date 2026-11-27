import {
    DocCallout,
    DocChips,
    DocFeature,
    DocGrid,
    DocMini,
    DocPage,
    DocSection,
    Formula,
    Hl,
    MetricCard,
    type Tone,
    type TocItem,
} from '../components/DocParts.tsx'

// Guia trazido da v1: LexHub/src/pages/documentacao/Replicas_LA.tsx (convertido para as peças da V2).

const TOC: TocItem[] = [
    { id: 'como-funciona', label: 'Como funciona' },
    { id: 'indicadores', label: 'Indicadores do período' },
    { id: 'procedencia', label: 'Taxa de Procedência (1G)' },
    { id: 'comissao', label: 'Comissionamento' },
    { id: 'graficos', label: 'Gráficos e histórico' },
    { id: 'filtros', label: 'Filtros' },
]

const FILTERS: { name: string; desc: string; badge: string; tone: Tone }[] = [
    {
        name: 'Funcionários',
        desc: 'Restringe às tarefas de um ou mais funcionários. Também é aplicado clicando em "Demandas por funcionário" ou na média diária.',
        badge: 'Pessoa',
        tone: 'info',
    },
    {
        name: 'Atividade',
        desc: 'Filtra por uma ou mais atividades do setor. É aplicado clicando no gráfico "Por atividade" e aparece nas etiquetas de filtro.',
        badge: 'Clique no gráfico',
        tone: 'neutral',
    },
    {
        name: 'Situação do processo',
        desc: 'Ativo, Suspenso / Sobrestado ou Arquivado — é a situação do processo, não da tarefa. Sem escolha, entram todas.',
        badge: 'Processo',
        tone: 'accent',
    },
]

export function ReplicasLADoc() {
    return (
        <DocPage
            title="Réplicas — LA"
            tags={['LA']}
            toc={TOC}
            intro={
                <>
                    Este guia explica cada número e gráfico do dashboard de Réplicas — o setor
                    <strong> RÉPLICAS</strong> da unidade LA, com o comissionamento mais simples da família
                    "Intermediárias".
                </>
            }
            header={
                <DocCallout caps title="Um setor, uma tarefa por linha" badge='Setor "RÉPLICAS"'>
                    <p>
                        O dashboard pega todas as atividades <Hl mono>RÉPLICAS - …</Hl> da LA — na prática, quase tudo é
                        "Elaborar Réplica". Cada linha do dashboard é uma dessas tarefas.
                    </p>
                    <DocGrid cols={2}>
                        <DocMini label="Responsável exibido">
                            Sempre quem <strong>encerrou</strong> a tarefa, ou quem está <strong>atribuído</strong> a
                            ela se ainda estiver aberta.
                        </DocMini>
                        <DocMini label="Comissão">
                            <Hl tone="ok" mono>
                                R$ 1,50
                            </Hl>{' '}
                            por réplica "Encerrado Cumprido" no período (Seção 04).
                        </DocMini>
                    </DocGrid>
                </DocCallout>
            }
        >
            <DocSection id="como-funciona" title="01 — Como o dashboard funciona" subtitle="Duas visões da mesma tela">
                <DocGrid cols={2}>
                    <DocFeature title="Por prazo (padrão)" tone="info" icon="calendar" badge="Padrão" framed>
                        <p>
                            A página abre nesta visão. Todos os cartões olham para o <strong>prazo</strong> da tarefa. O
                            comissionamento não muda com este alternador — sempre usa a base de criação/conclusão.
                        </p>
                    </DocFeature>
                    <DocFeature title="Concluídas" tone="accent" icon="check-circle" badge="Conclusão" framed>
                        <p>
                            Total/Em andamento usam a data de <strong>criação</strong>; Concluídas usa a data de
                            <strong> encerramento</strong> — é também o eixo usado pelo comissionamento.
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
                        interpret="Mostra o volume de réplicas distribuídas para elaboração no período."
                    />
                    <MetricCard
                        icon="clock"
                        name="Em andamento"
                        what="Das tarefas do Total, quantas estão em algum status ativo."
                        counts='Qualquer status ativo: "Recebido", "Visualizado", "Iniciado", "Reaberto" ou "Encaminhado".'
                        calc="Como o Total já exclui as encerradas/canceladas, este número normalmente coincide com o Total."
                        interpret="Não é um alerta de atraso — é só a confirmação de que a tarefa segue ativa."
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
                id="procedencia"
                title="03 — Taxa de Procedência (1G)"
                subtitle="Um sinal de qualidade, não de comissão"
                tone="info"
                badge="Fora da comissão"
            >
                <DocCallout tone="info" title="O que a taxa mede">
                    <p>
                        Mede, dos processos que tiveram réplica apresentada no período, quantos já ganharam a causa em
                        primeiro grau. Não influencia o comissionamento — é só um indicador indireto de qualidade da
                        peça.
                    </p>
                </DocCallout>
                <DocGrid cols={3}>
                    <DocFeature title="Universo" tone="neutral" icon="layers">
                        <p>
                            Processos distintos com qualquer tarefa do setor criada dentro do período, com os filtros da
                            página — de qualquer atividade e status, inclusive Cancelado.
                        </p>
                    </DocFeature>
                    <DocFeature title="Denominador" tone="info" icon="scale">
                        <p>
                            Desses processos, só os que já têm status de 1º grau preenchido — é o status{' '}
                            <strong>atual</strong> do processo, não o da época da réplica. Os sem status contam como
                            "sem decisão" e ficam fora da taxa.
                        </p>
                    </DocFeature>
                    <DocFeature title="Numerador" tone="ok" icon="check-circle">
                        <p>Subconjunto com decisão de procedência — total ou parcial, com ou sem proveito econômico.</p>
                    </DocFeature>
                </DocGrid>
                <DocCallout tone="ok" icon="check-circle" title="Validado com dados reais" badge="23,3%">
                    <p>
                        De 875 processos distintos com réplica, 309 já tinham decisão de 1º grau e 72 foram procedentes
                        — taxa de 23,3%. Não há faixas coloridas (ouro/prata/bronze) aqui — só percentual e contadores.
                    </p>
                </DocCallout>
            </DocSection>

            <DocSection
                id="comissao"
                title="04 — Comissionamento"
                subtitle="Valor fixo por peça concluída"
                tone="ok"
                badge="R$ 1,50 por peça"
            >
                <Formula>Comissão = réplicas "Encerrado Cumprido" no período × R$ 1,50</Formula>
                <p>
                    O mais simples dos três dashboards da família: sem faixas, sem gatilho de agenda. Toda réplica
                    encerrada como "Encerrado Cumprido" no período vale <strong>R$ 1,50</strong> — "Encerrado Não
                    Cumprido" conta como produção, mas não gera peça paga.
                </p>
                <DocChips
                    label="Status de encerramento:"
                    items={[
                        { label: 'Encerrado Cumprido · paga', tone: 'ok' },
                        { label: 'Encerrado Não Cumprido · só produção', tone: 'warn' },
                    ]}
                />
                <DocCallout tone="warn" icon="calendar" title="Sempre pela data de conclusão">
                    <p>
                        A data usada para contar a peça é a de <strong>conclusão</strong> da tarefa, não o prazo — a
                        regra é literalmente "peça concluída". Esse cálculo sempre usa a base de Criação/Conclusão,
                        mesmo que a tela esteja no alternador "Por prazo".
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
                    <DocFeature title="Por atividade" tone="accent" icon="barChart" badge="Clicável" framed>
                        <p>
                            Tarefas encerradas por atividade, com prazo (ou conclusão, na visão Concluídas) no período.
                            Clicar filtra a página.
                        </p>
                    </DocFeature>
                    <DocFeature title="Demandas por funcionário" tone="ok" icon="users" badge="Base da comissão" framed>
                        <p>
                            Tarefas encerradas no período por funcionário, separadas em Cumprido e Não Cumprido — é
                            também a base usada para calcular a comissão.
                        </p>
                    </DocFeature>
                    <DocFeature title="Concluídas por mês / por dia" tone="info" icon="barChart" badge="Drill-down">
                        <p>
                            Histórico de encerramentos ao longo do tempo, com detalhamento por funcionário no
                            drill-down.
                        </p>
                    </DocFeature>
                    <DocFeature title="Média diária por funcionário" tone="violet" icon="trendingUp">
                        <p>
                            Total encerrado por funcionário dividido pelos dias distintos em que ele encerrou algo,
                            sobre o <strong>histórico todo</strong> (não segue o período).
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection id="filtros" title="06 — Filtros disponíveis" subtitle="Como personalizar a lista de tarefas">
                <DocGrid cols={2}>
                    {FILTERS.map((f) => (
                        <DocFeature key={f.name} title={f.name} tone={f.tone} icon="filter" badge={f.badge}>
                            <p>{f.desc}</p>
                        </DocFeature>
                    ))}
                </DocGrid>
            </DocSection>
        </DocPage>
    )
}
