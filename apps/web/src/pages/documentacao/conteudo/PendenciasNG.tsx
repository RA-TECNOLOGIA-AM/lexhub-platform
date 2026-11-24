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

// Guia trazido da v1: LexHub/src/pages/documentacao/Pendencias_NG.tsx (convertido para as peças da V2).

const TOC: TocItem[] = [
    { id: 'como-funciona', label: 'Como funciona' },
    { id: 'indicadores', label: 'Indicadores do período' },
    { id: 'taxas', label: 'Taxas' },
    { id: 'rankings', label: 'Rankings' },
    { id: 'tendencia', label: 'Tendência' },
    { id: 'reajuizamento', label: 'Reajuizamento' },
    { id: 'comissao', label: 'Comissionamento' },
    { id: 'filtros', label: 'Filtros' },
]

export function PendenciasNGDoc() {
    return (
        <DocPage
            title="Pendências — NG e LARJ"
            tags={['NG', 'LARJ']}
            note="Mesma lógica nas duas unidades"
            toc={TOC}
            intro={
                <>
                    Este guia explica cada número e gráfico do dashboard de Pendências das unidades NG e LARJ. Você vai
                    entender de onde vem cada informação, o que ela mede e como usá-la no dia a dia. Nenhum conhecimento
                    técnico é necessário.
                </>
            }
        >
            <DocSection
                id="como-funciona"
                title="Como o dashboard funciona"
                subtitle="O ciclo de vida de uma pendência no sistema"
            >
                <InfoBox>
                    O setor de Pendências cuida de demandas que precisam de alguma ação antes de seguir em frente. Cada
                    processo percorre etapas bem definidas, e o dashboard mostra exatamente quantos estão em cada etapa
                    dentro do período selecionado.
                </InfoBox>

                <DocCard title="Ciclo de vida de uma pendência">
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                        <div className="stack">
                            <WatchBox title="TRIAGEM">
                                <p>Aguardando avaliação</p>
                            </WatchBox>
                        </div>
                        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>→</div>
                        <div className="stack">
                            <DocCard title="EM ANDAMENTO / PENDÊNCIA">
                                <p>Sendo trabalhada</p>
                            </DocCard>
                        </div>
                        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>→</div>
                        <div className="stack">
                            <DocCard title="RESOLVIDO">
                                <p>Concluída com sucesso</p>
                            </DocCard>
                        </div>
                        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>ou</div>
                        <div className="stack">
                            <WatchBox title="CANCELADO">
                                <p>Encerrada sem resolução</p>
                            </WatchBox>
                        </div>
                    </div>

                    <div className="stack">
                        <p>
                            <strong>Filtro de datas:</strong> o dashboard filtra pela coluna <Code>ENTRADA</Code> — a
                            data em que a pendência entrou no setor.
                        </p>
                        <p>
                            <strong>Cancelados excluídos:</strong> pendências com motivo <em>DUPLICADO</em> ou{' '}
                            <em>AÇÃO INEXISTENTE</em> não entram em nenhum contador — são consideradas registros sem
                            validade.
                        </p>
                        <p>
                            <strong>Triagem não entra no total:</strong> processos em triagem são contados separadamente
                            e não compõem o total usado para calcular taxas percentuais.
                        </p>
                    </div>
                </DocCard>
            </DocSection>

            <DocSection
                id="indicadores"
                title="Indicadores do período"
                subtitle="Os cartões de resumo no topo do dashboard"
            >
                <DocGrid>
                    <MetricCard
                        icon="alert"
                        name="Não Resolvidas"
                        what="Quantidade de pendências que ainda estão abertas e precisam de ação."
                        counts='Processos com STATUS = "EM ANDAMENTO" ou "PENDÊNCIA", sem flag de reajuizamento.'
                        calc="Contagem direta dos registros que se enquadram nos status acima dentro do período filtrado."
                        interpret="Quanto menor, melhor. Um número alto significa acúmulo de trabalho em aberto. Acompanhe diariamente para evitar que processos fiquem parados."
                    />
                    <MetricCard
                        icon="alert"
                        name="Não Resolvidas com Atraso"
                        what="Das pendências ainda abertas, quantas já ultrapassaram 5 dias sem resolução."
                        counts='Processos com STATUS = "EM ANDAMENTO" ou "PENDÊNCIA" em que (data de hoje − data de entrada) > 5 dias.'
                        calc="Para cada pendência não resolvida, o sistema calcula (hoje − ENTRADA) em dias. Se o resultado for maior que 5, ela entra nesse contador."
                        interpret="Este é o indicador de urgência. Qualquer número acima de zero merece atenção imediata — esses processos estão atrasados."
                        caveat="O cálculo usa sempre a data de hoje como referência, então o número pode variar ao longo do dia."
                    />
                    <MetricCard
                        icon="check"
                        name="Resolvidas"
                        what="Quantidade de pendências que foram concluídas com sucesso no período."
                        counts='Processos com STATUS = "RESOLVIDO", sem flag de reajuizamento.'
                        calc="Contagem dos registros com status RESOLVIDO dentro da data de entrada selecionada."
                        interpret="Quanto maior, melhor. Representa a produção efetiva do setor. Compare com períodos anteriores para ver a tendência de evolução."
                    />
                    <MetricCard
                        icon="xCircle"
                        name="Canceladas"
                        what="Pendências que foram encerradas sem resolução por motivo legítimo."
                        counts='Processos com STATUS = "CANCELADO", sem flag de reajuizamento, e cujo motivo de cancelamento NÃO seja "DUPLICADO" nem "AÇÃO INEXISTENTE".'
                        calc="Contagem dos cancelamentos válidos. Duplicados e ações inexistentes são descartados para não distorcer o indicador."
                        interpret="Um número elevado pode indicar problemas na triagem inicial — se muitas pendências chegam com informações incorretas, elas acabam canceladas."
                    />
                    <MetricCard
                        icon="clock"
                        name="Em Triagem"
                        what="Processos que chegaram ao setor mas ainda não foram avaliados e direcionados."
                        counts='Processos com STATUS = "TRIAGEM" (qualquer flag de reajuizamento).'
                        calc="Contagem simples dos registros em triagem. Este número não entra no total usado para calcular taxas."
                        interpret="Processos em triagem precisam de avaliação. Se o número crescer muito, pode haver gargalo na entrada de demandas."
                    />
                    <MetricCard
                        icon="fileText"
                        name="Total"
                        what="Volume total de pendências válidas no período — a base para calcular todas as taxas percentuais."
                        counts="Não Resolvidas + Resolvidas + Canceladas. Triagem não entra neste total."
                        calc="Total = Não Resolvidas + Resolvidas + Canceladas."
                        interpret="Use o total para entender o volume de trabalho do período. Taxas percentuais são sempre calculadas sobre este número."
                    />
                </DocGrid>
            </DocSection>

            <DocSection
                id="taxas"
                title="Taxas percentuais"
                subtitle="Gauges que mostram a proporção de cada status em relação ao total"
            >
                <InfoBox>
                    As taxas são calculadas dividindo cada categoria pelo total (Não Resolvidas + Resolvidas +
                    Canceladas). Elas mostram, em percentual, como o trabalho do período se distribuiu.
                </InfoBox>
                <DocGrid>
                    <DocCard title="Taxa de Resolvidos">
                        <p>
                            <strong>Fórmula:</strong> (Resolvidas ÷ Total) × 100
                            <br />
                            <strong>Ideal:</strong> quanto mais alto, melhor. Indica que a maior parte das pendências do
                            período foi concluída com sucesso.
                        </p>
                    </DocCard>
                    <DocCard title="Taxa de Não Resolvidos">
                        <p>
                            <strong>Fórmula:</strong> (Não Resolvidas ÷ Total) × 100
                            <br />
                            <strong>Ideal:</strong> quanto mais baixo, melhor. Um percentual alto indica acúmulo de
                            trabalho em aberto.
                        </p>
                    </DocCard>
                    <DocCard title="Taxa de Cancelados">
                        <p>
                            <strong>Fórmula:</strong> (Canceladas ÷ Total) × 100
                            <br />
                            <strong>Ideal:</strong> quanto mais baixo, melhor. Se passar de 5%, o comissionamento é
                            zerado.
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>

            <DocSection
                id="rankings"
                title="Rankings"
                subtitle="Distribuição do trabalho por funcionário, atendente e origem"
            >
                <DocGrid>
                    <DocCard title="Média de resolvidas por funcionário (por dia)">
                        <p>
                            Mostra quantas pendências cada funcionário resolve por dia em média. Calculado dividindo o
                            total de resolvidas pelo número de dias distintos em que o funcionário teve saídas. Útil
                            para comparar produtividade entre membros da equipe.
                        </p>
                    </DocCard>
                    <DocCard title="Não resolvidas por atendente comercial">
                        <p>
                            Mostra quantas pendências abertas estão associadas a cada atendente do comercial. Ajuda a
                            identificar qual atendente gerou mais demandas ainda em aberto.
                        </p>
                    </DocCard>
                    <DocCard title="Não resolvidas por origem">
                        <p>
                            Agrupa as pendências abertas pelo campo ORIGEM, mostrando de onde vêm as demandas não
                            resolvidas. Útil para identificar fontes com maior volume de problemas.
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>

            <DocSection id="tendencia" title="Tendência" subtitle="Evolução ao longo do tempo">
                <DocGrid>
                    <DocCard title="Resolvidas por dia">
                        <p>
                            Gráfico de linha mostrando quantas pendências foram resolvidas em cada dia do período
                            selecionado. A data usada é a data de saída (SAIDA). Picos indicam dias mais produtivos;
                            vales podem revelar ausências ou acúmulo de trabalho.
                        </p>
                    </DocCard>
                    <DocCard title="Resolvidas por mês">
                        <p>
                            Visão mensal das resoluções. Permite comparar meses diferentes e identificar sazonalidade ou
                            crescimento no volume de trabalho processado.
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>

            <DocSection
                id="reajuizamento"
                title="Reajuizamento"
                subtitle="Processos com flag de reajuizamento são tratados separadamente"
            >
                <InfoBox>
                    Processos de reajuizamento são aqueles que voltam ao sistema após uma ação anterior. O sistema
                    separa automaticamente esses processos dos demais, exibindo contadores paralelos.
                </InfoBox>
                <DocGrid>
                    <DocCard title="Não Resolvidas (Reajuizamento)">
                        <p>
                            Mesmo critério das Não Resolvidas normais, mas restringe aos processos com flag{' '}
                            <Code>REAJUIZAMENTO = TRUE</Code>. Status aceitos: "EM ANDAMENTO" ou "PENDÊNCIA".
                        </p>
                    </DocCard>
                    <DocCard title="Resolvidas (Reajuizamento)">
                        <p>
                            Mesmo critério das Resolvidas normais, mas restringe aos processos com flag{' '}
                            <Code>REAJUIZAMENTO = TRUE</Code>. Status aceito: "RESOLVIDO".
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>

            <DocSection
                id="comissao"
                title="Comissionamento"
                subtitle="Como o sistema calcula a comissão de cada funcionário"
            >
                <InfoBox>
                    O comissionamento é calculado individualmente para cada funcionário, com base nos processos que ele
                    resolveu. A lógica considera primeiro a taxa de cancelamento — se for muito alta, o funcionário não
                    recebe comissão, independente de tudo mais.
                </InfoBox>

                <DocCard>
                    <div>
                        <h3 className="doc-h3">Regras de comissão</h3>
                    </div>
                    <div>
                        <div className="card tblwrap">
                            <table className="tbl">
                                <thead>
                                    <tr>
                                        <th>Condição</th>
                                        <th>Valor por resolvida</th>
                                        <th>Explicação</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td>Taxa de cancelamento ≥ 5%</td>
                                        <td>R$ 0,00</td>
                                        <td>
                                            Muitos cancelamentos indicam problema na qualidade do trabalho. Comissão
                                            bloqueada.
                                        </td>
                                    </tr>
                                    <tr>
                                        <td>Taxa de resolvidos ≥ 97%</td>
                                        <td>R$ 3,00</td>
                                        <td>Desempenho excelente. Quase todas as pendências foram resolvidas.</td>
                                    </tr>
                                    <tr>
                                        <td>Taxa de resolvidos ≥ 85%</td>
                                        <td>R$ 1,00</td>
                                        <td>Bom desempenho, mas ainda há espaço para melhoria.</td>
                                    </tr>
                                    <tr>
                                        <td>Taxa de resolvidos &lt; 85%</td>
                                        <td>R$ 0,00</td>
                                        <td>Volume de resoluções insuficiente para gerar comissão.</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </DocCard>

                <DocCard title="Exemplo prático">
                    <p>
                        Um funcionário resolveu 100 pendências. Delas, 98 foram resolvidas (98%) e 2 canceladas (2%).
                        Como a taxa de cancelamento está abaixo de 5% e a de resolvidos está acima de 97%, ele recebe R$
                        3,00 × 98 = <strong>R$ 294,00</strong>.
                    </p>
                    <p>
                        Se esse mesmo funcionário tivesse 6 cancelamentos (6%), a taxa de cancelamento ultrapassaria 5%
                        e a comissão seria zerada, mesmo com boa taxa de resolução.
                    </p>
                </DocCard>
            </DocSection>

            <DocSection id="filtros" title="Filtros disponíveis" subtitle="Como personalizar a visão do dashboard">
                <DocGrid>
                    {[
                        {
                            name: 'Período (data de entrada)',
                            desc: 'Filtra os processos pela data em que entraram no setor (coluna ENTRADA). Todos os contadores refletem apenas o intervalo selecionado.',
                        },
                        {
                            name: 'Funcionário',
                            desc: 'Restringe a visão a um ou mais funcionários específicos, usando as duas primeiras palavras do nome para comparação.',
                        },
                        {
                            name: 'UF (Estado)',
                            desc: 'Filtra os processos por unidade federativa, permitindo comparar o desempenho entre estados.',
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
