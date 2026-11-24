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

// Guia trazido da v1: LexHub/src/pages/documentacao/OrgDoc_LA.tsx (convertido para as peças da V2).

const TOC: TocItem[] = [
    { id: 'como-funciona', label: 'Como funciona' },
    { id: 'diferenca-la', label: 'Diferença LA × NG' },
    { id: 'represados', label: 'Represados (acumulado)' },
    { id: 'periodo', label: 'Indicadores do período' },
    { id: 'rankings', label: 'Rankings' },
    { id: 'tendencia', label: 'Tendência' },
    { id: 'comissao', label: 'Comissionamento' },
    { id: 'filtros', label: 'Filtros' },
]

export function OrgDocumentosLADoc() {
    return (
        <DocPage
            title="Organização de Documentos — LA"
            tags={['LA']}
            note="Lógica diferente do NG"
            toc={TOC}
            intro={
                <>
                    Este guia explica cada número e gráfico do dashboard de Organização de Documentos da unidade LA. A
                    LA tem diferenças importantes no fluxo: os status são diferentes, e a distinção entre organização
                    manual e automática é feita por um campo específico (PET_AUTO), não pelo status. Nenhum conhecimento
                    técnico é necessário.
                </>
            }
        >
            <DocSection
                id="como-funciona"
                title="Como o dashboard funciona"
                subtitle="O ciclo de vida de um processo na Organização de Documentos LA"
            >
                <InfoBox>
                    O setor de Organização de Documentos da LA recebe processos vindos das Pendências (os processos com
                    status "ORG DOC" nas Pendências chegam aqui). O setor então organiza e encaminha esses processos. O
                    dashboard mostra dois recortes: os represados (acumulado) e os movimentados no período.
                </InfoBox>

                <DocCard title="Ciclo de vida — Org Doc LA">
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                        <DocCard title="ORG DOC">
                            <p>Represado (veio das Pendências)</p>
                        </DocCard>
                        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>→</div>
                        <DocCard title="PETICIONAMENTO / PROTOCOLO / CONCLUIDO">
                            <p>Processo organizado e encaminhado</p>
                        </DocCard>
                        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>ou</div>
                        <WatchBox title="PENDENCIA">
                            <p>Voltou para Pendências</p>
                        </WatchBox>
                        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>ou</div>
                        <WatchBox title="CANCELADO">
                            <p>Encerrado</p>
                        </WatchBox>
                    </div>

                    <div className="stack">
                        <p>
                            <strong>Filtro de datas (resolvidos):</strong> usa a coluna <Code>SAIDA</Code> — a data em
                            que o processo saiu do setor.
                        </p>
                        <p>
                            <strong>Represados (não filtrados):</strong> os processos com STATUS="ORG DOC" representam o
                            estoque acumulado — não são afetados pelo filtro de datas.
                        </p>
                    </div>
                </DocCard>
            </DocSection>

            <DocSection
                id="diferenca-la"
                title="Como a LA difere do NG"
                subtitle="Diferenças importantes nos status e na distinção entre manual e automático"
            >
                <DiffBox>
                    Na LA, os status de "organizado" são diferentes do NG: em vez de "RESOLVIDO" (manual) e "PROTOCOLAR"
                    (automático), a LA usa "PETICIONAMENTO", "PROTOCOLO" e "CONCLUIDO" para indicar que o processo foi
                    organizado. A distinção entre manual e automático é feita pelo campo PET_AUTO (verdadeiro/falso),
                    não pelo status.
                </DiffBox>

                <DocCard>
                    <div>
                        <h3 className="doc-h3">Comparativo LA × NG</h3>
                    </div>
                    <div>
                        <div className="card tblwrap">
                            <table className="tbl">
                                <thead>
                                    <tr>
                                        <th>Conceito</th>
                                        <th>NG / LARJ</th>
                                        <th>LA</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td>Represado (em aberto)</td>
                                        <td>"NÃO INICIADO", "EM ANDAMENTO", "RETORNO PET", "RETORNO"</td>
                                        <td>"ORG DOC" (veio das Pendências)</td>
                                    </tr>
                                    <tr>
                                        <td>Organizado (concluído)</td>
                                        <td>"RESOLVIDO" ou "PROTOCOLAR"</td>
                                        <td>"PETICIONAMENTO", "PROTOCOLO" ou "CONCLUIDO"</td>
                                    </tr>
                                    <tr>
                                        <td>Manual vs. automático</td>
                                        <td>Status: "RESOLVIDO" = manual; "PROTOCOLAR" = automático</td>
                                        <td>Campo PET_AUTO: FALSE = manual; TRUE = automático</td>
                                    </tr>
                                    <tr>
                                        <td>Retorno para Pendências</td>
                                        <td>STATUS = "RETORNO"</td>
                                        <td>STATUS = "PENDENCIA"</td>
                                    </tr>
                                    <tr>
                                        <td>Retorno de Peticionamento</td>
                                        <td>STATUS = "RETORNO PET"</td>
                                        <td>Não existe na LA</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </DocCard>
            </DocSection>

            <DocSection
                id="represados"
                title="Represados (acumulado total)"
                subtitle="Processos em aberto — não dependem do filtro de datas"
            >
                <InfoBox>
                    Na LA, os processos represados são os que têm status "ORG DOC" — são os que vieram das Pendências e
                    ainda estão aguardando organização. Este contador não é afetado pelo filtro de datas.
                </InfoBox>

                <DocGrid>
                    <MetricCard
                        icon="fileText"
                        name="Não Organizados (represados)"
                        what="Total de processos no setor aguardando organização."
                        counts='Processos com STATUS = "ORG DOC", sem flag de reajuizamento.'
                        calc="Contagem direta dos processos com status ORG DOC. Este contador NÃO é filtrado por data."
                        interpret="Quanto menor, melhor. Representa o estoque de trabalho acumulado que veio do setor de Pendências."
                        caveat='Na LA, "ORG DOC" é o status de trabalho em aberto (represado), não de resolvido como pode parecer pelo nome.'
                    />
                    <MetricCard
                        icon="refresh"
                        name="Retorno Pendência"
                        what="Processos que voltaram para o setor de Pendências após passarem por Org Doc."
                        counts='Processos com STATUS = "PENDENCIA" (lidos pelo setor de Org Doc).'
                        calc="Contagem dos processos com status PENDENCIA dentro do contexto de Org Doc."
                        interpret="Retornos frequentes indicam que os processos precisavam de mais informações antes de serem organizados."
                    />
                </DocGrid>
            </DocSection>

            <DocSection
                id="periodo"
                title="Indicadores do período"
                subtitle="O que foi processado dentro do intervalo de datas selecionado"
            >
                <InfoBox>
                    Estes contadores usam a data de saída (SAIDA) para filtrar. Mostram apenas os processos que saíram
                    do setor dentro do período selecionado no dashboard.
                </InfoBox>

                <DocGrid>
                    <MetricCard
                        icon="check"
                        name="Total Organizados"
                        what="Total de processos concluídos no período, independente de como foram organizados."
                        counts='Processos com STATUS = "PETICIONAMENTO", "PROTOCOLO" ou "CONCLUIDO", sem flag de reajuizamento, com data de saída no período.'
                        calc="Contagem dos processos com qualquer um dos três status de conclusão."
                        interpret="Representa o volume total processado pelo setor no período. Quanto maior, melhor."
                    />
                    <MetricCard
                        icon="check"
                        name="Organizados Manualmente"
                        what="Processos que foram organizados por um funcionário de forma manual."
                        counts='Processos com STATUS = "PETICIONAMENTO", "PROTOCOLO" ou "CONCLUIDO" E campo PET_AUTO = FALSE, com data de saída no período.'
                        calc="Do total organizado, filtra apenas os que têm PET_AUTO = FALSE (manual)."
                        interpret="Representa o esforço manual da equipe no período."
                        caveat="Na LA, a distinção manual/automático é feita pelo campo PET_AUTO, não pelo status como no NG."
                    />
                    <MetricCard
                        icon="trendingUp"
                        name="Organizados Automaticamente"
                        what="Processos organizados pelo sistema de forma automática (sem intervenção humana)."
                        counts='Processos com STATUS = "PETICIONAMENTO", "PROTOCOLO" ou "CONCLUIDO" E campo PET_AUTO = TRUE, com data de saída no período.'
                        calc="Do total organizado, filtra apenas os que têm PET_AUTO = TRUE (automático)."
                        interpret="Quanto maior, mais eficiente o fluxo automatizado. Automações reduzem a carga manual da equipe."
                    />
                    <MetricCard
                        icon="xCircle"
                        name="Cancelados"
                        what="Processos que foram encerrados sem organização."
                        counts='Processos com STATUS = "CANCELADO", com data de saída no período.'
                        calc="Contagem dos cancelamentos dentro do período."
                        interpret="Monitore para identificar padrões. Cancelamentos frequentes podem indicar problemas na qualidade dos processos recebidos."
                    />
                </DocGrid>
            </DocSection>

            <DocSection id="rankings" title="Rankings" subtitle="Distribuição do trabalho por funcionário e atendente">
                <DocGrid>
                    <DocCard title="Organizados por funcionário">
                        <p>
                            Total de processos organizados (PETICIONAMENTO + PROTOCOLO + CONCLUIDO) agrupados por
                            funcionário. Mostra a distribuição absoluta do trabalho.
                        </p>
                    </DocCard>
                    <DocCard title="Média de organizados por funcionário (por dia)">
                        <p>
                            Divide o total de organizados pelo número de dias distintos com saídas. Permite comparar
                            produtividade levando em conta dias trabalhados.
                        </p>
                    </DocCard>
                    <DocCard title="Não organizados por atendente comercial">
                        <p>
                            Quantos processos represados (STATUS="ORG DOC") estão associados a cada atendente do
                            comercial.
                        </p>
                    </DocCard>
                    <DocCard title="Não organizados por funcionário">
                        <p>
                            Quantos processos represados estão atribuídos a cada funcionário. Ajuda a identificar quem
                            está sobrecarregado.
                        </p>
                    </DocCard>
                    <DocCard title="Valor de causa por funcionário">
                        <p>
                            Soma o valor das causas dos processos organizados por cada funcionário. Para matéria ANP usa
                            DANO_MORAL; para as demais usa VALOR_DA_CAUSA.
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>

            <DocSection id="tendencia" title="Tendência" subtitle="Evolução ao longo do tempo">
                <DocGrid>
                    <DocCard title="Organizados por dia">
                        <p>
                            Gráfico de linha com os processos organizados agrupados por dia de saída (SAIDA). Útil para
                            identificar picos e vales de produtividade.
                        </p>
                    </DocCard>
                    <DocCard title="Organizados por mês">
                        <p>
                            Visão mensal da produção. Permite comparar meses e identificar sazonalidade ou crescimento.
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
                    A comissão na LA usa a mesma fórmula do NG — proporcional ao valor de causa dos processos
                    organizados. A única diferença é que os status de "organizado" são diferentes (PETICIONAMENTO,
                    PROTOCOLO, CONCLUIDO em vez de RESOLVIDO/PROTOCOLAR).
                </InfoBox>

                <DocCard title="Fórmula de comissão">
                    <WatchBox>Comissão = R$ 0,60 × Qtd de organizados × (Valor de causa / 1.000.000)</WatchBox>
                    <div className="stack">
                        <p>
                            <strong>Valor de causa:</strong> para processos com matéria ANP, usa o campo{' '}
                            <Code>DANO_MORAL</Code>. Para todas as demais matérias, usa o campo{' '}
                            <Code>VALOR_DA_CAUSA</Code>.
                        </p>
                        <p>
                            <strong>Processos sem valor de causa</strong> não contribuem para o cálculo.
                        </p>
                        <p>
                            <strong>Base:</strong> apenas processos com REAJUIZAMENTO=FALSE e STATUS = PETICIONAMENTO,
                            PROTOCOLO ou CONCLUIDO.
                        </p>
                    </div>
                </DocCard>

                <DocCard title="Exemplo prático">
                    <p>
                        Um funcionário organizou 40 processos com valor de causa total de R$ 3.000.000,00. Comissão = R$
                        0,60 × 40 × (3.000.000 ÷ 1.000.000) = R$ 0,60 × 40 × 3 = <strong>R$ 72,00</strong>.
                    </p>
                </DocCard>
            </DocSection>

            <DocSection id="filtros" title="Filtros disponíveis" subtitle="Como personalizar a visão do dashboard">
                <DocGrid>
                    {[
                        {
                            name: 'Período (data de saída)',
                            desc: 'Filtra os processos organizados pela data de saída do setor (coluna SAIDA). Os represados não são afetados por este filtro.',
                        },
                        { name: 'Funcionário', desc: 'Restringe a visão a um ou mais funcionários específicos.' },
                        {
                            name: 'Matéria',
                            desc: "Filtra por tipo de matéria jurídica. O sistema extrai apenas a parte antes do ' - ' no campo MATERIA.",
                        },
                        { name: 'UF (Estado)', desc: 'Filtra os processos por unidade federativa.' },
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
