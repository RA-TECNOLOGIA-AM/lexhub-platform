import {
    DiffBox,
    DocCard,
    DocGrid,
    DocPage,
    DocSection,
    InfoBox,
    MetricCard,
    type TocItem,
} from '../components/DocParts.tsx'

// Guia trazido da v1: LexHub/src/pages/documentacao/PendenciasIntermediarias_NG.tsx (convertido para as peças da V2).

const TOC: TocItem[] = [
    { id: 'como-funciona', label: 'Como funciona' },
    { id: 'indicadores', label: 'Indicadores do período' },
    { id: 'dilacao', label: 'Taxa de Dilação' },
    { id: 'graficos', label: 'Gráficos e histórico' },
    { id: 'filtros', label: 'Filtros' },
]

export function PendenciasIntermediariasNGDoc() {
    return (
        <DocPage
            title="Pendências Intermediárias — NG"
            tags={['NG']}
            toc={TOC}
            intro={
                <>
                    Este guia explica cada número e gráfico do dashboard de Pendências Intermediárias — as tarefas do
                    setor <strong>PENDÊNCIA</strong> da unidade NG, responsável por pedir documentos ao cliente e
                    decidir se um processo segue ou entra em dilação de prazo.
                </>
            }
        >
            <DocSection
                id="como-funciona"
                title="Como o dashboard funciona"
                subtitle="A base comum das telas de 'Atividades no período'"
            >
                <InfoBox>
                    Cada linha do dashboard é um agendamento (uma tarefa) do setor "PENDÊNCIA" da NG — não o processo
                    inteiro. Um mesmo processo pode ter várias tarefas ao longo do tempo (pedir documento, avaliar
                    retorno, decidir dilação). O responsável exibido é sempre quem <strong>encerrou</strong> a tarefa;
                    se ela ainda está aberta, é quem está atualmente <strong>atribuído</strong> a ela.
                </InfoBox>

                <DocCard title="Duas visões da mesma tela">
                    <p>O alternador no topo do dashboard troca o eixo de data usado nos cálculos:</p>
                    <DocGrid>
                        <DocCard title="Concluídas (padrão)">
                            <p>
                                Total/Em andamento usam a data de <strong>criação</strong> da tarefa; Concluídas usa a
                                data em que ela foi <strong>encerrada</strong>.
                            </p>
                        </DocCard>
                        <DocCard title="Por prazo">
                            <p>
                                Todos os cartões passam a olhar para o <strong>prazo</strong> da tarefa, não para quando
                                ela foi criada ou concluída.
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
                        interpret="Mostra o volume de entrada de trabalho no setor durante o período."
                    />
                    <MetricCard
                        icon="clock"
                        name="Em andamento"
                        what="Das tarefas do Total, quantas já foram assumidas por alguém e estão sendo trabalhadas."
                        counts='Apenas os status "Iniciado", "Reaberto" e "Encaminhado" — note que "Recebido" e "Visualizado" NÃO contam aqui.'
                        calc="Subconjunto do Total nesses três status específicos."
                        interpret='Por ser um subconjunto restrito do Total (diferente de outros dashboards da família, onde "Em andamento" cobre todo status ativo), este número é normalmente menor que o Total.'
                        caveat='Diferente de Emendas e Manifestações e de Réplicas: aqui "Recebido" e "Visualizado" ficam fora de "Em andamento".'
                    />
                    <MetricCard
                        icon="alert"
                        name="Vencidas"
                        what="Tarefas ativas cujo prazo já passou, hoje."
                        counts="Tarefas ativas com prazo anterior à data de hoje."
                        calc="Não depende do período filtrado nem de quando a tarefa foi criada — é sempre relativo ao dia de hoje."
                        interpret="Indicador de urgência: qualquer valor acima de zero merece atenção."
                    />
                    <MetricCard
                        icon="clock"
                        name="Vencem hoje"
                        what="Tarefas ativas cujo prazo é exatamente hoje."
                        counts="Tarefas ativas com prazo igual à data de hoje."
                        calc="Mesma lógica de Vencidas, mas comparando prazo = hoje."
                        interpret="Ajuda a priorizar o que precisa ser resolvido ainda no dia."
                    />
                    <MetricCard
                        icon="check"
                        name="Concluídas"
                        what="Tarefas do setor que foram encerradas no período — contagem separada do Total."
                        counts='Status "Encerrado Cumprido" ou "Encerrado Não Cumprido" com data de encerramento no período.'
                        calc="Contagem direta dos registros encerrados no período, independente de quando foram criados."
                        interpret="Mede a produção efetiva de fechamento do setor no período — é o denominador da Taxa de Dilação."
                    />
                </DocGrid>
            </DocSection>

            <DocSection
                id="dilacao"
                title="Taxa de Dilação"
                subtitle="A régua de qualidade do setor — não é comissão em reais"
            >
                <InfoBox>
                    Este é o único dashboard da família "Intermediárias" sem comissionamento em R$. Em vez disso, mede a
                    <strong> taxa de dilação</strong>: de tudo que o setor encerrou, quanto acabou virando um pedido de
                    dilação de prazo por falta de documento do cliente. Quanto menor essa taxa, melhor a qualidade do
                    trabalho.
                </InfoBox>

                <DocCard title="Como o numerador é encontrado">
                    <p>
                        O NG não tem um setor dedicado de "Dilação de Prazo" como a LA — conta-se, em vez disso, um
                        agendamento "MANIFESTAÇÃO - ELABORAR DILAÇÃO" criado no período <em>somente</em> quando ele pode
                        ser rastreado a uma tarefa "SOLICITAR DOCS COM CLIENTE" deste mesmo setor, no mesmo processo,
                        que foi encerrada como
                        <strong> "Encerrado Não Cumprido"</strong> com o motivo "Cliente não respondeu/enviou docs". Um
                        "Encerrado Não Cumprido" sem esse motivo não gera esse agendamento e fica de fora da conta.
                    </p>
                    <p>
                        O denominador é <strong>todo</strong> o volume encerrado do setor no período — o mesmo número do
                        cartão "Concluídas" acima.
                    </p>
                </DocCard>

                <DocCard>
                    <div>
                        <h3 className="doc-h3">Faixas</h3>
                    </div>
                    <div>
                        <div className="card tblwrap">
                            <table className="tbl">
                                <thead>
                                    <tr>
                                        <th>Faixa</th>
                                        <th>Taxa de dilação</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td>Ouro</td>
                                        <td>≤ 5%</td>
                                    </tr>
                                    <tr>
                                        <td>Prata</td>
                                        <td>6% a 10%</td>
                                    </tr>
                                    <tr>
                                        <td>Bronze</td>
                                        <td>11% a 15%</td>
                                    </tr>
                                    <tr>
                                        <td>Sem faixa</td>
                                        <td>acima de 15%, ou sem base para calcular</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </DocCard>

                <DiffBox>
                    A quebra por funcionário só lista quem encerrou pelo menos uma tarefa "SOLICITAR DOCS COM CLIENTE"
                    no período — quem trabalha só na outra atividade do setor ("Sanar Pendência 1G") entra nos KPIs
                    gerais, mas fica fora desta régua específica.
                </DiffBox>
            </DocSection>

            <DocSection
                id="graficos"
                title="Gráficos e histórico"
                subtitle="Distribuição do trabalho e evolução no tempo"
            >
                <DocGrid>
                    <DocCard>
                        <p>Processos por atividade</p>
                        <p>
                            Quantos processos distintos passaram por cada atividade do setor no período — conta
                            processos, não tarefas, então um processo com duas tarefas da mesma atividade só aparece uma
                            vez.
                        </p>
                    </DocCard>
                    <DocCard>
                        <p>Demandas por funcionário</p>
                        <p>
                            Tarefas encerradas no período por funcionário, separadas em "Encerrado Cumprido" e
                            "Encerrado Não Cumprido" — mostra volume e qualidade lado a lado.
                        </p>
                    </DocCard>
                    <DocCard title="Concluídas por mês / por dia">
                        <p>
                            Histórico de encerramentos ao longo do tempo, com detalhamento por funcionário disponível no
                            drill-down.
                        </p>
                    </DocCard>
                    <DocCard title="Média diária por funcionário">
                        <p>
                            Total de tarefas encerradas por funcionário dividido pelo número de dias distintos em que
                            ele encerrou algo — compara ritmo de produção, não só volume total.
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>

            <DocSection id="filtros" title="Filtros disponíveis" subtitle="Como personalizar a lista de tarefas">
                <DocGrid>
                    {[
                        {
                            name: 'Funcionário',
                            desc: 'Restringe às tarefas de um ou mais funcionários (quem encerrou, ou quem está atribuído se ainda aberta).',
                        },
                        {
                            name: 'Atividade',
                            desc: 'Filtra por uma ou mais atividades específicas do setor PENDÊNCIA.',
                        },
                        {
                            name: 'Status',
                            desc: 'Filtra pelo status bruto da tarefa (Recebido, Iniciado, Encerrado Cumprido, etc.).',
                        },
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
                <p>
                    Os quatro filtros se combinam em "E" (um registro só aparece se atender a todos os filtros ativos).
                    Clicar numa barra dos gráficos acima aplica o filtro correspondente na página inteira.
                </p>
            </DocSection>
        </DocPage>
    )
}
