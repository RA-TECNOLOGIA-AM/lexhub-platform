import {
    Code,
    DiffBox,
    DocCard,
    DocGrid,
    DocPage,
    DocSection,
    InfoBox,
    MetricCard,
    WatchBox,
    type TocItem,
} from '../components/DocParts.tsx'

// Guia trazido da v1: LexHub/src/pages/documentacao/Pendencias_LA.tsx (convertido para as peças da V2).

const TOC: TocItem[] = [
    { id: 'como-funciona', label: 'Como funciona' },
    { id: 'indicadores', label: 'Indicadores do período' },
    { id: 'taxas', label: 'Taxas' },
    { id: 'rankings', label: 'Rankings' },
    { id: 'tendencia', label: 'Tendência' },
    { id: 'comissao', label: 'Comissionamento' },
    { id: 'filtros', label: 'Filtros' },
]

export function PendenciasLADoc() {
    return (
        <DocPage
            title="Pendências — LA"
            tags={['LA']}
            toc={TOC}
            intro={<>Este guia explica cada número e gráfico do dashboard de Pendências da unidade LA.</>}
        >
            <DocSection
                id="como-funciona"
                title="Como o dashboard funciona"
                subtitle="O ciclo de vida de uma pendência no sistema LA"
            >
                <InfoBox>
                    O setor de Pendências da LA cuida de demandas que precisam de alguma ação antes de seguir em frente,
                    seja ela algum documento do cliente ou extrato bancário. Cada processo percorre etapas bem
                    definidas, e o dashboard mostra exatamente quantos estão em cada etapa dentro do período
                    selecionado.
                </InfoBox>

                <DocCard title="Ciclo de vida de uma pendência (LA)">
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                        <div className="stack">
                            <WatchBox title="TRIAGEM">
                                <p>Aguardando avaliação</p>
                            </WatchBox>
                        </div>
                        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>→</div>
                        <div className="stack">
                            <DocCard title="PENDENCIA">
                                <p>Sendo trabalhada</p>
                            </DocCard>
                        </div>
                        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>→</div>
                        <div className="stack">
                            <DocCard title="ORG DOC">
                                <p>Enviado para Org. Documentos</p>
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
                            <em>AÇÃO INEXISTENTE</em> não entram em nenhum contador.
                        </p>
                        <p>
                            <strong>Triagem não entra no total:</strong> processos em triagem são contados separadamente
                            e não compõem o total usado para calcular taxas.
                        </p>
                    </div>
                </DocCard>
            </DocSection>

            <DocSection
                id="conceitos-la"
                title="Conceitos de status na LA"
                subtitle="Como cada status é entendido no fluxo da unidade"
            >
                <DiffBox>
                    Resolvido na LA significa que a pendência foi encaminhada para o setor de Organização de Documentos
                    (status "ORG DOC"), e os Represados são os processos que ainda estão no setor aguardando ser
                    resolvido.
                </DiffBox>

                <DocCard>
                    <div>
                        <h3 className="doc-h3">Status na LA</h3>
                    </div>
                    <div>
                        <div className="card tblwrap">
                            <table className="tbl">
                                <thead>
                                    <tr>
                                        <th>Conceito</th>
                                        <th>Status na LA</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td>Não resolvida</td>
                                        <td>"PENDENCIA" (sem acento)</td>
                                    </tr>
                                    <tr>
                                        <td>Resolvida</td>
                                        <td>"ORG DOC" (encaminhado para Org. Documentos)</td>
                                    </tr>
                                    <tr>
                                        <td>Cancelada</td>
                                        <td>"CANCELADO" (exceto duplicado/ação inexistente)</td>
                                    </tr>
                                    <tr>
                                        <td>Triagem</td>
                                        <td>"TRIAGEM"</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
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
                        counts='Processos com STATUS = "PENDENCIA" (sem acento), sem flag de reajuizamento.'
                        calc="Contagem direta dos registros com esse status dentro do período filtrado."
                        interpret="Quanto menor, melhor. Um número alto significa acúmulo de trabalho em aberto. Acompanhe diariamente."
                        caveat='O status é "PENDENCIA" (sem acento).'
                    />
                    <MetricCard
                        icon="alert"
                        name="Não Resolvidas com Atraso"
                        what="Das pendências ainda abertas, quantas já ultrapassaram 5 dias sem resolução."
                        counts='Processos com STATUS = "PENDENCIA" em que (data de hoje − data de entrada) > 5 dias.'
                        calc="Para cada pendência não resolvida, o sistema calcula (hoje − ENTRADA) em dias. Se o resultado for maior que 5, ela entra nesse contador."
                        interpret="Este é o indicador de urgência. Qualquer número acima de zero merece atenção imediata."
                        caveat="O cálculo usa sempre a data de hoje como referência, então o número pode variar ao longo do dia."
                    />
                    <MetricCard
                        icon="check"
                        name="Resolvidas"
                        what='Quantidade de pendências que foram encaminhadas para Organização de Documentos — o que representa "resolvida" no fluxo da LA.'
                        counts='Processos com STATUS = "ORG DOC", sem flag de reajuizamento.'
                        calc='Contagem dos registros com status "ORG DOC" dentro da data de entrada selecionada.'
                        interpret="Quanto maior, melhor. Representa a produção efetiva do setor. Na LA, resolver uma pendência significa enviá-la para Org. Documentos."
                        caveat='"Resolvido" na LA é identificado pelo status "ORG DOC".'
                    />
                    <MetricCard
                        icon="xCircle"
                        name="Canceladas"
                        what="Pendências que foram encerradas sem resolução por motivo legítimo."
                        counts='Processos com STATUS = "CANCELADO", sem flag de reajuizamento, e cujo motivo NÃO seja "DUPLICADO" nem "AÇÃO INEXISTENTE".'
                        calc="Contagem dos cancelamentos válidos. Duplicados e ações inexistentes são descartados."
                        interpret="Um número elevado pode indicar problemas na triagem inicial."
                    />
                    <MetricCard
                        icon="clock"
                        name="Em Triagem"
                        what="Processos que chegaram ao setor mas ainda não foram avaliados e direcionados."
                        counts='Processos com STATUS = "TRIAGEM".'
                        calc="Contagem simples dos registros em triagem. Este número não entra no total usado para calcular taxas."
                        interpret="Processos em triagem precisam de avaliação. Número crescente indica gargalo na entrada."
                    />
                    <MetricCard
                        icon="fileText"
                        name="Total"
                        what="Volume total de pendências válidas — base para calcular todas as taxas percentuais."
                        counts="Não Resolvidas + Resolvidas + Canceladas. Triagem não entra neste total."
                        calc="Total = Não Resolvidas + Resolvidas + Canceladas."
                        interpret="Use o total para entender o volume de trabalho do período."
                    />
                </DocGrid>
            </DocSection>

            <DocSection id="taxas" title="Taxas percentuais" subtitle="Proporção de cada status em relação ao total">
                <InfoBox>
                    As taxas são calculadas dividindo cada categoria pelo total (Não Resolvidas + Resolvidas +
                    Canceladas). Resolvidas correspondem ao status "ORG DOC" e não resolvidas ao status "PENDENCIA".
                </InfoBox>
                <DocGrid>
                    <DocCard title="Taxa de Resolvidos">
                        <p>
                            <strong>Fórmula:</strong> (Resolvidas ÷ Total) × 100
                            <br />
                            <strong>Resolvidas = STATUS "ORG DOC"</strong>
                            <br />
                            Quanto mais alto, melhor.
                        </p>
                    </DocCard>
                    <DocCard title="Taxa de Não Resolvidos">
                        <p>
                            <strong>Fórmula:</strong> (Não Resolvidas ÷ Total) × 100
                            <br />
                            <strong>Não Resolvidas = STATUS "PENDENCIA"</strong>
                            <br />
                            Quanto mais baixo, melhor.
                        </p>
                    </DocCard>
                    <DocCard title="Taxa de Cancelados">
                        <p>
                            <strong>Fórmula:</strong> (Canceladas ÷ Total) × 100
                            <br />
                            Quanto mais baixo, melhor. Se passar de 5%, o comissionamento é zerado.
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
                            Quantas pendências cada funcionário resolve por dia em média. Calculado dividindo o total de
                            resolvidas (status "ORG DOC") pelo número de dias distintos em que houve saídas. Útil para
                            comparar produtividade.
                        </p>
                    </DocCard>
                    <DocCard title="Não resolvidas por atendente comercial">
                        <p>
                            Quantas pendências abertas (status "PENDENCIA") estão associadas a cada atendente do
                            comercial.
                        </p>
                    </DocCard>
                    <DocCard title="Não resolvidas por origem">
                        <p>
                            Agrupa as pendências abertas pelo campo ORIGEM. Útil para identificar fontes com maior
                            volume de problemas.
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>

            <DocSection id="tendencia" title="Tendência" subtitle="Evolução ao longo do tempo">
                <DocGrid>
                    <DocCard title="Resolvidas por dia">
                        <p>
                            Gráfico de linha com as pendências resolvidas (status "ORG DOC") por dia. A data usada é a
                            data de saída (SAIDA).
                        </p>
                    </DocCard>
                    <DocCard title="Resolvidas por mês">
                        <p>
                            Visão mensal das resoluções. Permite comparar meses diferentes e identificar crescimento no
                            volume processado.
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>

            <DocSection
                id="comissao"
                title="Comissionamento"
                subtitle="Como o sistema calcula a comissão de cada funcionário na LA"
            >
                <InfoBox>
                    A comissão segue percentuais por taxa de resolvidos, com bloqueio quando a taxa de cancelamento
                    atinge 5% ou mais. "Resolvido" na LA é o status "ORG DOC", e "não resolvido" é "PENDENCIA".
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
                                        <td>Muitos cancelamentos indicam problema na qualidade. Comissão bloqueada.</td>
                                    </tr>
                                    <tr>
                                        <td>Taxa de resolvidos ≥ 97%</td>
                                        <td>R$ 3,00</td>
                                        <td>
                                            Desempenho excelente. Quase todas as pendências foram encaminhadas para Org.
                                            Documentos.
                                        </td>
                                    </tr>
                                    <tr>
                                        <td>Taxa de resolvidos ≥ 85%</td>
                                        <td>R$ 1,00</td>
                                        <td>Bom desempenho, mas ainda há espaço para melhoria.</td>
                                    </tr>
                                    <tr>
                                        <td>Taxa de resolvidos &lt; 85%</td>
                                        <td>R$ 0,00</td>
                                        <td>Volume insuficiente para gerar comissão.</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
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
