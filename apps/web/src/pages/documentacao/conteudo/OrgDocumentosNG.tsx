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

// Guia trazido da v1: LexHub/src/pages/documentacao/OrgDoc_NG.tsx (convertido para as peças da V2).

const TOC: TocItem[] = [
    { id: 'como-funciona', label: 'Como funciona' },
    { id: 'represados', label: 'Represados (acumulado)' },
    { id: 'periodo', label: 'Indicadores do período' },
    { id: 'rankings', label: 'Rankings' },
    { id: 'tendencia', label: 'Tendência' },
    { id: 'materias', label: 'Por matéria' },
    { id: 'comissao', label: 'Comissionamento' },
    { id: 'filtros', label: 'Filtros' },
]

export function OrgDocumentosNGDoc() {
    return (
        <DocPage
            title="Organização de Documentos — NG e LARJ"
            tags={['NG', 'LARJ']}
            note="Mesma lógica nas duas unidades"
            toc={TOC}
            intro={
                <>
                    Este guia explica cada número e gráfico do dashboard de Organização de Documentos das unidades NG e
                    LARJ. Você vai entender a diferença entre o que é acumulado (represado) e o que foi processado no
                    período, como funciona a comissão e o que cada gráfico representa. Nenhum conhecimento técnico é
                    necessário.
                </>
            }
        >
            <DocSection
                id="como-funciona"
                title="Como o dashboard funciona"
                subtitle="O ciclo de vida de um processo na Organização de Documentos"
            >
                <InfoBox>
                    O setor de Organização de Documentos (Org Doc) recebe processos vindos de outros setores e os
                    organiza para seguir em frente. O dashboard mostra dois recortes distintos: os processos acumulados
                    (represados, que existem independente de datas) e os processos movimentados no período selecionado.
                </InfoBox>

                <DocCard title="Ciclo de vida — Org Doc NG/LARJ">
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                        <DocCard title="NÃO INICIADO / EM ANDAMENTO">
                            <p>Represado no setor</p>
                        </DocCard>
                        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>ou</div>
                        <WatchBox title="RETORNO / RETORNO PET">
                            <p>Voltou de outro setor</p>
                        </WatchBox>
                        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>→</div>
                        <DocCard title="RESOLVIDO">
                            <p>Organizado manualmente</p>
                        </DocCard>
                        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>ou</div>
                        <DocCard title="PROTOCOLAR">
                            <p>Organizado e peticionado automaticamente</p>
                        </DocCard>
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
                            <strong>Represados (não filtrados por data):</strong> os contadores de processos ainda em
                            aberto (NÃO INICIADO, EM ANDAMENTO, RETORNO, RETORNO PET) mostram o acumulado total — não
                            são afetados pelo filtro de datas.
                        </p>
                    </div>
                </DocCard>
            </DocSection>

            <DocSection
                id="represados"
                title="Represados (acumulado total)"
                subtitle="Processos em aberto — não dependem do filtro de datas"
            >
                <InfoBox>
                    Esses contadores mostram o estoque atual de processos que ainda precisam de ação. Eles não mudam com
                    o filtro de datas — refletem sempre o total acumulado que o setor tem pendente.
                </InfoBox>

                <DocGrid>
                    <MetricCard
                        icon="fileText"
                        name="Não Organizados (represados)"
                        what="Total de processos que estão no setor aguardando organização."
                        counts='Processos com STATUS = "NÃO INICIADO", "EM ANDAMENTO", "RETORNO PET" ou "RETORNO", sem flag de reajuizamento.'
                        calc="Contagem direta de todos os processos nesses status. Este contador NÃO é filtrado por data."
                        interpret="Quanto menor, melhor. Representa o estoque de trabalho acumulado. Monitorar esse número ajuda a evitar gargalos."
                        caveat="Este é o único indicador que não é afetado pelo filtro de período — mostra sempre o total atual."
                    />
                    <MetricCard
                        icon="refresh"
                        name="Retorno Pendência"
                        what="Processos que foram ao setor de Pendências e voltaram para Org Doc."
                        counts='Processos com STATUS = "RETORNO".'
                        calc="Contagem dos retornos vindos de Pendências. Faz parte do total represado."
                        interpret="Retornos frequentes podem indicar que os processos chegam incompletos para Org Doc, gerando retrabalho."
                    />
                    <MetricCard
                        icon="refresh"
                        name="Retorno Confecção PET"
                        what="Processos que foram ao setor de Peticionamento e voltaram para Org Doc."
                        counts='Processos com STATUS = "RETORNO PET".'
                        calc="Contagem dos retornos vindos de Peticionamento. Faz parte do total represado."
                        interpret="Um número alto pode indicar que os documentos não estavam prontos para peticionamento quando foram enviados."
                    />
                </DocGrid>
            </DocSection>

            <DocSection
                id="periodo"
                title="Indicadores do período"
                subtitle="O que foi processado dentro do intervalo de datas selecionado"
            >
                <InfoBox>
                    Estes contadores usam a data de saída (SAIDA) para filtrar — mostram apenas os processos que saíram
                    do setor dentro do período selecionado no dashboard.
                </InfoBox>

                <DocGrid>
                    <MetricCard
                        icon="check"
                        name="Resolvido Manualmente"
                        what="Processos organizados por um funcionário de forma manual."
                        counts='Processos com STATUS = "RESOLVIDO", sem flag de reajuizamento, com data de saída no período.'
                        calc="Contagem dos processos com status RESOLVIDO dentro do período filtrado."
                        interpret="Representa o trabalho manual do setor. Um bom número aqui indica alta produtividade da equipe."
                    />
                    <MetricCard
                        icon="check"
                        name="Organizado e Peticionado Automaticamente"
                        what="Processos que foram organizados e já encaminhados para peticionamento de forma automática pelo sistema."
                        counts='Processos com STATUS = "PROTOCOLAR", sem flag de reajuizamento, com data de saída no período.'
                        calc="Contagem dos processos com status PROTOCOLAR dentro do período filtrado."
                        interpret="Automações ajudam a aumentar o volume processado sem sobrecarregar a equipe. Quanto maior, mais eficiente o fluxo automatizado."
                    />
                    <MetricCard
                        icon="xCircle"
                        name="Cancelados"
                        what="Processos que foram encerrados sem organização."
                        counts='Processos com STATUS = "CANCELADO", com data de saída no período.'
                        calc="Contagem dos cancelamentos dentro do período. Diferente das Pendências, aqui não há filtro de motivo."
                        interpret="Cancelamentos podem indicar processos inviáveis ou com erros. Monitore para identificar padrões."
                    />
                    <MetricCard
                        icon="fileText"
                        name="Total Resolvidos"
                        what="Soma de todos os processos concluídos no período — tanto manuais quanto automáticos."
                        counts='Processos com STATUS = "RESOLVIDO" ou "PROTOCOLAR", sem flag de reajuizamento.'
                        calc="Resolvidos Manualmente + Organizados e Peticionados Automaticamente."
                        interpret="Indica o volume total produzido no período. Use para comparar períodos e medir a capacidade do setor."
                    />
                    <MetricCard
                        icon="fileText"
                        name="Resolvidos Reajuizamento"
                        what="Processos de reajuizamento concluídos no período."
                        counts='Processos com STATUS = "RESOLVIDO" ou "PROTOCOLAR" e flag REAJUIZAMENTO = TRUE, com data de saída no período.'
                        calc="Contagem dos processos resolvidos com flag de reajuizamento."
                        interpret="Rastreia a produção específica de processos que voltaram ao sistema após uma ação anterior."
                    />
                </DocGrid>
            </DocSection>

            <DocSection id="rankings" title="Rankings" subtitle="Distribuição do trabalho por funcionário e atendente">
                <DocGrid>
                    <DocCard title="Resolvidos por funcionário">
                        <p>
                            Total de processos resolvidos (RESOLVIDO + PROTOCOLAR) agrupados por funcionário. Mostra a
                            distribuição absoluta do trabalho entre os membros da equipe.
                        </p>
                    </DocCard>
                    <DocCard title="Média de resolvidos por funcionário (por dia)">
                        <p>
                            Divide o total de resolvidos pelo número de dias distintos com saídas. Permite comparar
                            produtividade levando em conta dias trabalhados.
                        </p>
                    </DocCard>
                    <DocCard title="Não organizados por atendente comercial">
                        <p>
                            Mostra quantos processos represados estão associados a cada atendente do comercial. Usa o
                            campo ATENDENTE_COMERCIAL.
                        </p>
                    </DocCard>
                    <DocCard title="Não organizados por funcionário">
                        <p>
                            Mostra quantos processos em aberto estão atribuídos a cada funcionário. Ajuda a identificar
                            quem está sobrecarregado.
                        </p>
                    </DocCard>
                    <DocCard title="Valor de causa por funcionário">
                        <p>
                            Soma o valor das causas dos processos resolvidos por cada funcionário. Para matéria ANP usa
                            o campo DANO_MORAL; para as demais usa VALOR_DA_CAUSA.
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>

            <DocSection id="tendencia" title="Tendência" subtitle="Evolução ao longo do tempo">
                <DocGrid>
                    <DocCard title="Resolvidos por dia">
                        <p>
                            Gráfico de linha com os processos resolvidos (RESOLVIDO + PROTOCOLAR) agrupados por dia de
                            saída (SAIDA). Útil para identificar picos e vales de produtividade.
                        </p>
                    </DocCard>
                    <DocCard title="Resolvidos por mês">
                        <p>
                            Visão mensal da produção. Permite comparar meses e identificar sazonalidade ou crescimento.
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>

            <DocSection
                id="materias"
                title="Por matéria"
                subtitle="Distribuição dos processos por tipo de matéria jurídica"
            >
                <InfoBox>
                    A matéria é o tipo jurídico do processo. O sistema extrai apenas a parte antes do traço (" - ") do
                    campo MATERIA. Por exemplo, "BX_ANT_FIN - BANCO BRADESCO" vira simplesmente "BX_ANT_FIN". Isso
                    garante que variantes do mesmo tipo sejam agrupadas corretamente.
                </InfoBox>
                <DocGrid>
                    <DocCard title="Resolvidos por matéria">
                        <p>
                            Agrupa os processos resolvidos pelo tipo de matéria. Mostra quais tipos de demanda tiveram
                            maior volume de resolução no período.
                        </p>
                    </DocCard>
                    <DocCard title="Não organizados por matéria">
                        <p>
                            Agrupa os processos represados pelo tipo de matéria. Útil para priorizar quais tipos de
                            demanda têm maior acúmulo.
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
                    A comissão em Org Doc é calculada de forma diferente das Pendências. Aqui, o valor depende tanto da
                    quantidade de processos resolvidos quanto do valor das causas desses processos. Não há classificação
                    por taxa de resolução — a fórmula é proporcional ao valor movimentado.
                </InfoBox>

                <DocCard title="Fórmula de comissão">
                    <DocCard>Comissão = R$ 0,60 × Qtd de resolvidos × (Valor de causa / 1.000.000)</DocCard>
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
                            <strong>Base:</strong> apenas processos com REAJUIZAMENTO=FALSE e STATUS = RESOLVIDO ou
                            PROTOCOLAR.
                        </p>
                    </div>
                </DocCard>

                <DocCard title="Exemplo prático">
                    <p>
                        Um funcionário resolveu 50 processos com valor de causa total de R$ 5.000.000,00. Comissão = R$
                        0,60 × 50 × (5.000.000 ÷ 1.000.000) = R$ 0,60 × 50 × 5 = <strong>R$ 150,00</strong>.
                    </p>
                    <p>
                        Note que quanto maior o valor das causas resolvidas, maior a comissão. Processos de alto valor
                        de causa têm mais impacto no cálculo.
                    </p>
                </DocCard>
            </DocSection>

            <DocSection id="filtros" title="Filtros disponíveis" subtitle="Como personalizar a visão do dashboard">
                <DocGrid>
                    {[
                        {
                            name: 'Período (data de saída)',
                            desc: 'Filtra os processos resolvidos pela data de saída do setor (coluna SAIDA). Os represados não são afetados por este filtro.',
                        },
                        { name: 'Funcionário', desc: 'Restringe a visão a um ou mais funcionários específicos.' },
                        {
                            name: 'Matéria',
                            desc: "Filtra por tipo de matéria jurídica. A normalização extrai apenas a parte antes do ' - ' no campo MATERIA.",
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
