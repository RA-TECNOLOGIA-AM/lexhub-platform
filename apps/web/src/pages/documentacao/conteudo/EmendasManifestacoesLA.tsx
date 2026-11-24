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

// Guia trazido da v1: LexHub/src/pages/documentacao/EmendasManifestacoes_LA.tsx (convertido para as peças da V2).

const TOC: TocItem[] = [
    { id: 'como-funciona', label: 'Como funciona' },
    { id: 'indicadores', label: 'Indicadores do período' },
    { id: 'atividades', label: 'Classificação de atividades' },
    { id: 'comissao', label: 'Comissionamento' },
    { id: 'graficos', label: 'Gráficos e histórico' },
    { id: 'filtros', label: 'Filtros' },
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
        >
            <DocSection
                id="como-funciona"
                title="Como o dashboard funciona"
                subtitle="O setor INTERMEDIÁRIAS e as duas visões da tela"
            >
                <InfoBox>
                    Cada linha é uma tarefa (agendamento) do setor "INTERMEDIÁRIAS" — o mais amplo dos quatro dashboards
                    desta família, com 18 atividades diferentes. O responsável exibido é sempre quem{' '}
                    <strong>encerrou</strong>a tarefa; se ainda estiver aberta, é quem está <strong>atribuído</strong> a
                    ela no momento.
                </InfoBox>
                <DocCard title="Duas visões da mesma tela">
                    <DocGrid>
                        <DocCard title="Concluídas (padrão)">
                            <p>
                                Total/Em andamento usam a data de <strong>criação</strong>; Concluídas usa a data de
                                <strong> encerramento</strong>.
                            </p>
                        </DocCard>
                        <DocCard title="Por prazo">
                            <p>
                                Todos os cartões passam a olhar para o <strong>prazo</strong> da tarefa — é também o
                                eixo usado pelo comissionamento.
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
                id="atividades"
                title="Classificação de atividades"
                subtitle="Quais atividades geram peça remunerada"
            >
                <DocCard>
                    <div>
                        <div className="card tblwrap">
                            <table className="tbl">
                                <thead>
                                    <tr>
                                        <th>Categoria</th>
                                        <th>Atividades</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td>Manifestação</td>
                                        <td>
                                            Emenda à Inicial · Manifestação (5D/10D/15D) · Manifestação Custas de
                                            Citação · Manifestação Remessa 2 Grau · Man Hipo Recurso · Man
                                            Hipossuficiência · Man Desnecessidade de Audiência · Man Interposição Agravo
                                            · Pedido de Celeridade · Pedido Sustentação Oral
                                        </td>
                                    </tr>
                                    <tr>
                                        <td>Dilação</td>
                                        <td>Dilação de Prazo</td>
                                    </tr>
                                    <tr>
                                        <td>Não comissionável</td>
                                        <td>
                                            Avaliar Manifestação (Int) · Confecção (Int) · Provas a Produzir · Verificar
                                            Não Cumprimento (Intermediárias) · Alegações Finais
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </DocCard>
                <p>
                    Atividades não comissionáveis ainda contam para a agenda do funcionário quando encerradas — só não
                    geram peça paga.
                </p>
            </DocSection>

            <DocSection id="comissao" title="Comissionamento" subtitle="Faixas por percentual de agenda cumprida">
                <InfoBox>
                    A comissão depende de quanto da <strong>agenda do mês</strong> o funcionário fechou — não é por peça
                    isolada. Agenda do mês = tarefas do funcionário com prazo no período (Cancelado e Concluído não
                    entram). Uma tarefa conta como "finalizada" se foi encerrada como Cumprido <em>ou</em> Não Cumprido.
                </InfoBox>

                <DocCard>
                    <div>
                        <h3 className="doc-h3">Faixas de comissão</h3>
                    </div>
                    <div>
                        <div className="card tblwrap">
                            <table className="tbl">
                                <thead>
                                    <tr>
                                        <th>Faixa</th>
                                        <th>% de agenda cumprida</th>
                                        <th>R$ / Manifestação</th>
                                        <th>R$ / Dilação</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td>Inelegível</td>
                                        <td>abaixo de 85%</td>
                                        <td>R$ 0,00</td>
                                        <td>R$ 0,00</td>
                                    </tr>
                                    <tr>
                                        <td>Faixa 1</td>
                                        <td>85% a 96,9%</td>
                                        <td>R$ 1,00</td>
                                        <td>R$ 0,25</td>
                                    </tr>
                                    <tr>
                                        <td>Faixa 2</td>
                                        <td>97% ou mais</td>
                                        <td>R$ 1,50</td>
                                        <td>R$ 0,50</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </DocCard>

                <p>
                    A faixa alcançada vale para <strong>todas</strong> as peças do funcionário no período — não é
                    progressivo peça a peça. Só conta como peça paga a tarefa com status "Encerrado Cumprido" e prazo no
                    período (mesmo eixo da agenda); "Encerrado Não Cumprido" soma na agenda, mas não gera pagamento.
                </p>

                <DiffBox>
                    Validado contra a produção real de uma funcionária em jun/2026: 484 manifestações + 29 dilações = R$
                    740,50 (484 × 1,50 + 29 × 0,50), confirmando Faixa 2. A implementação original usava a data de
                    encerramento e contava Não Cumprido como peça paga — dava valores errados; a regra correta usa o
                    prazo e só conta "Encerrado Cumprido".
                </DiffBox>
            </DocSection>

            <DocSection
                id="graficos"
                title="Gráficos e histórico"
                subtitle="Distribuição do trabalho e evolução no tempo"
            >
                <DocGrid>
                    <DocCard>
                        <p>Encerradas por atividade</p>
                        <p>
                            Tarefas encerradas (Cumprido ou Não Cumprido) no período, agrupadas por atividade — usa a
                            mesma base do KPI "Concluídas", para os números baterem entre si.
                        </p>
                    </DocCard>
                    <DocCard>
                        <p>Demandas por funcionário</p>
                        <p>Tarefas encerradas no período por funcionário, separadas em Cumprido e Não Cumprido.</p>
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
                <p>
                    Clicar numa barra dos gráficos "por atividade" ou "por funcionário" aplica o filtro correspondente
                    em toda a página, inclusive nos KPIs e no comissionamento.
                </p>
            </DocSection>

            <DocSection id="filtros" title="Filtros disponíveis" subtitle="Como personalizar a lista de tarefas">
                <DocGrid>
                    {[
                        { name: 'Funcionário', desc: 'Restringe às tarefas de um ou mais funcionários.' },
                        { name: 'Atividade', desc: 'Filtra por uma ou mais das 18 atividades do setor.' },
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
                <p>A tabela de tarefas também mostra o número do processo (formato CNJ) quando disponível.</p>
            </DocSection>
        </DocPage>
    )
}
