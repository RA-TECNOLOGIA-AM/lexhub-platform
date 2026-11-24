import { DocCard, DocGrid, DocPage, DocSection, InfoBox, MetricCard, type TocItem } from '../components/DocParts.tsx'

// Guia trazido da v1: LexHub/src/pages/documentacao/Replicas_LA.tsx (convertido para as peças da V2).

const TOC: TocItem[] = [
    { id: 'como-funciona', label: 'Como funciona' },
    { id: 'indicadores', label: 'Indicadores do período' },
    { id: 'procedencia', label: 'Taxa de Procedência (1G)' },
    { id: 'comissao', label: 'Comissionamento' },
    { id: 'graficos', label: 'Gráficos e histórico' },
    { id: 'filtros', label: 'Filtros' },
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
                    <strong> RÉPLICAS</strong> da unidade LA, com uma única atividade e o comissionamento mais simples
                    da família "Intermediárias".
                </>
            }
        >
            <DocSection
                id="como-funciona"
                title="Como o dashboard funciona"
                subtitle="Um setor com uma única atividade"
            >
                <InfoBox>
                    O setor "RÉPLICAS" tem uma única atividade — "Elaborar Réplica" — cerca de 900 tarefas por mês. Cada
                    linha do dashboard é uma dessas tarefas; o responsável exibido é sempre quem{' '}
                    <strong>encerrou</strong>a tarefa, ou quem está <strong>atribuído</strong> a ela se ainda estiver
                    aberta.
                </InfoBox>
                <DocCard title="Duas visões da mesma tela">
                    <DocGrid>
                        <DocCard title="Concluídas (padrão)">
                            <p>
                                Total/Em andamento usam a data de <strong>criação</strong>; Concluídas usa a data de
                                <strong> encerramento</strong> — é também o eixo usado pelo comissionamento.
                            </p>
                        </DocCard>
                        <DocCard title="Por prazo">
                            <p>
                                Todos os cartões passam a olhar para o <strong>prazo</strong> da tarefa. O
                                comissionamento não muda com este alternador — sempre usa a base de criação/conclusão.
                            </p>
                        </DocCard>
                    </DocGrid>
                </DocCard>
            </DocSection>

            <DocSection
                id="indicadores"
                title="Indicadores do período"
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
                        calc="Comparação direta com a data de hoje — não depende do período filtrado."
                        interpret="Indicador de urgência: qualquer valor acima de zero merece atenção."
                    />
                    <MetricCard
                        icon="clock"
                        name="Vencem hoje"
                        what="Tarefas ativas cujo prazo é exatamente hoje."
                        counts="Tarefas ativas com prazo igual à data de hoje."
                        calc="Mesma lógica de Vencidas, comparando prazo = hoje."
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
                title="Taxa de Procedência (1G)"
                subtitle="Um sinal de qualidade, não de comissão"
            >
                <InfoBox>
                    Mede, dos processos que tiveram réplica apresentada no período, quantos já ganharam a causa em
                    primeiro grau. Não influencia o comissionamento — é só um indicador indireto de qualidade da peça.
                </InfoBox>
                <DocCard>
                    <p>
                        <strong>Universo:</strong> processos distintos com réplica apresentada (data de criação da
                        tarefa) dentro do período selecionado.
                    </p>
                    <p>
                        <strong>Denominador:</strong> desses processos, só os que já têm decisão de 1º grau — processos
                        ainda sem decisão contam como "pendentes" e ficam fora da taxa.
                    </p>
                    <p>
                        <strong>Numerador:</strong> subconjunto com decisão de procedência — total ou parcial, com ou
                        sem proveito econômico.
                    </p>
                </DocCard>
                <p>
                    Validado com dados reais: de 875 processos distintos com réplica, 309 já tinham decisão de 1º grau e
                    72 foram procedentes — taxa de 23,3%. Não há faixas coloridas (ouro/prata/bronze) aqui — só
                    percentual e contadores.
                </p>
            </DocSection>

            <DocSection id="comissao" title="Comissionamento" subtitle="Valor fixo por peça concluída">
                <InfoBox>
                    O mais simples dos quatro dashboards: sem faixas, sem gatilho de agenda. Toda réplica encerrada como
                    "Encerrado Cumprido" no período vale <strong>R$ 1,50</strong> — "Encerrado Não Cumprido" conta como
                    produção, mas não gera peça paga.
                </InfoBox>
                <p>
                    A data usada para contar a peça é a de <strong>conclusão</strong> da tarefa, não o prazo — a regra é
                    literalmente "peça concluída". Esse cálculo sempre usa a base de Criação/Conclusão, mesmo que a tela
                    esteja no alternador "Por prazo".
                </p>
            </DocSection>

            <DocSection
                id="graficos"
                title="Gráficos e histórico"
                subtitle="Distribuição do trabalho e evolução no tempo"
            >
                <DocGrid>
                    <DocCard>
                        <p>Demandas por funcionário</p>
                        <p>
                            Tarefas encerradas no período por funcionário, separadas em Cumprido e Não Cumprido — é
                            também a base usada para calcular a comissão.
                        </p>
                    </DocCard>
                    <DocCard title="Concluídas por mês / por dia">
                        <p>
                            Histórico de encerramentos ao longo do tempo, com detalhamento por funcionário no
                            drill-down.
                        </p>
                    </DocCard>
                    <DocCard title="Média diária por funcionário">
                        <p>Total encerrado por funcionário dividido pelos dias distintos em que ele encerrou algo.</p>
                    </DocCard>
                </DocGrid>
            </DocSection>

            <DocSection id="filtros" title="Filtros disponíveis" subtitle="Como personalizar a lista de tarefas">
                <DocGrid>
                    {[
                        { name: 'Funcionário', desc: 'Restringe às tarefas de um ou mais funcionários.' },
                        {
                            name: 'Atividade',
                            desc: 'Existe por consistência com os outros dashboards, mas o setor só tem uma atividade.',
                        },
                        { name: 'Status', desc: 'Filtra pelo status bruto da tarefa.' },
                        {
                            name: 'Situação',
                            desc: 'Filtra pelas categorias calculadas: em andamento, vencidas, vencem hoje, concluídas.',
                        },
                    ].map((f) => (
                        <DocCard>
                            <p>{f.name}</p>
                            <p>{f.desc}</p>
                        </DocCard>
                    ))}
                </DocGrid>
            </DocSection>
        </DocPage>
    )
}
