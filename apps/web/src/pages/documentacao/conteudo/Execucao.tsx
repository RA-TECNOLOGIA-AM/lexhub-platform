import { DocCard, DocGrid, DocPage, DocSection, InfoBox, MetricCard, type TocItem } from '../components/DocParts.tsx'

// Guia da Execução Condenação. Texto da v1: LexHub/src/pages/documentacao/Execucao.tsx.

const TOC: TocItem[] = [
    { id: 'como-funciona', label: 'Como funciona' },
    { id: 'indicadores', label: 'Indicadores' },
    { id: 'subfases', label: 'Matérias e subfases' },
    { id: 'entradas-mes', label: 'Entradas por mês' },
    { id: 'evolucao', label: 'Evolução mensal' },
    { id: 'atividades', label: 'Atividades' },
    { id: 'filtros', label: 'Filtros' },
]

const FILTERS = [
    {
        name: 'Período (calendário)',
        desc: "Afeta os cards de 'entrada/saída no período' e os KPIs de Atividades. Não afeta os cards e gráficos marcados como 'histórico completo'.",
    },
    {
        name: 'Matéria / Subfase',
        desc: 'Clique em uma fatia ou barra dos gráficos de Matérias e Subfases para filtrar o restante da página.',
    },
    {
        name: 'Mês (gráfico de Entradas)',
        desc: "Clique em um mês no gráfico 'Entradas na Execução por Mês' para aplicar o período daquele mês inteiro ao filtro de calendário.",
    },
    {
        name: 'Funcionário / Atividade / Situação',
        desc: 'Na seção Atividades, clique em uma barra, nome de funcionário ou card de KPI para filtrar a lista de tarefas.',
    },
    {
        name: 'Concluídas / Por prazo',
        desc: 'Alterna o eixo temporal (data de conclusão vs. data de prazo) de toda a seção Atividades.',
    },
]

export function ExecucaoDoc() {
    return (
        <DocPage
            title="Execução Condenação"
            tags={['NG', 'LA']}
            note="Mesma lógica nas duas unidades"
            toc={TOC}
            intro={
                <>
                    Este guia explica cada número e gráfico do dashboard de Execução. Você vai entender a diferença
                    entre "processos ainda em execução" e "processos que entraram/saíram no período", como funciona o
                    filtro por prazo das atividades e o que cada gráfico representa. Nenhum conhecimento técnico é
                    necessário.
                </>
            }
        >
            <DocSection
                id="como-funciona"
                title="Como o dashboard funciona"
                subtitle="Duas perguntas diferentes: 'o que está em execução hoje' e 'o que entrou/saiu no período'"
                icon="fileText"
            >
                <InfoBox>
                    Um processo entra na fase de Execução (ID_FASE = 12) quando o campo DATA_EXECUCAO é preenchido no
                    LEXFLOW. A saída é medida pela data de compensação do alvará (DATA_COMPENSACAO_ALVARA), independente
                    da fase atual — processos já compensados (pagos) deixam a fase Financeiro e ficam arquivados
                    (situação Arquivado, fase "Arquivado por Procedência", motivo "Valor Compensado"), mas continuam
                    contando no histórico de saídas. O dashboard combina dois recortes: (1) o que está atualmente na
                    fase de Execução, e (2) o que entrou ou saiu dela dentro do período selecionado no calendário.
                </InfoBox>

                <DocCard title="Dois recortes que parecem iguais, mas não são">
                    <DocGrid>
                        <div className="stack" style={{ gap: 6 }}>
                            <span>
                                <span className="badge ok">"AINDA EM EXECUÇÃO HOJE"</span>
                            </span>
                            <p className="muted small">
                                Total em Execução, Valor Total, Valor de Honorários, Quantidade/Valor de entrada e saída
                                (cards da seção Indicadores)
                            </p>
                        </div>
                        <div className="stack" style={{ gap: 6 }}>
                            <span>
                                <span className="badge info">≠ "ENTROU/SAIU NO PERÍODO"</span>
                            </span>
                            <p className="muted small">
                                Gráfico "Entradas na Execução por Mês" e "Valor Saída Execução Mês a Mês" — olham só a
                                data, sem exigir que o processo continue em Execução hoje
                            </p>
                        </div>
                    </DocGrid>
                    <p>
                        <strong>Exemplo prático:</strong> um processo que entrou em Execução em março e já saiu para o
                        Financeiro em abril aparece no gráfico "Entradas na Execução por Mês" (março), mas{' '}
                        <strong>não</strong> conta no card "Quantidade de entrada na Execução" nem no "Total em
                        Execução" — porque esses cards só contam processos que ainda estão na fase Execução hoje.
                    </p>
                    <p>
                        Essa diferença é intencional: os cards da seção Indicadores respondem "quanto ainda temos em
                        aberto", enquanto os gráficos de tendência respondem "quanto entrou/saiu historicamente" — são
                        duas perguntas diferentes, propositalmente calculadas de formas diferentes.
                    </p>
                </DocCard>

                <DocCard title="Cada processo conta uma única vez">
                    <p>
                        Um mesmo processo pode ter mais de uma parte adversa cadastrada no LEXFLOW. Todos os cálculos do
                        dashboard deduplicam por NUMERO_PROCESSO (o identificador único do processo), garantindo que ele
                        seja contado (e seu valor somado) apenas uma vez, mesmo quando existe mais de um registro para o
                        mesmo processo na base.
                    </p>
                </DocCard>

                <DocCard title="Compensação parcial do alvará (incontroverso / remanescente)">
                    <p>
                        Um processo pode ser pago em duas partes. A parte incontroversa (a fatia sobre a qual não há
                        discussão) costuma cair primeiro — LEXFLOW registra o valor (VALOR_INCONTROVERSO) e a data de
                        compensação (DATA_COMPENSACAO_ALVARA_INCONTROVERSO). O restante fica como VALOR_REMANESCENTE, e
                        só é pago depois — quando isso acontece, a DATA_COMPENSACAO_ALVARA "oficial" é preenchida e o
                        processo finalmente sai da fase Execução.
                    </p>
                    <p>
                        Isso afeta cinco cards e dois gráficos: <strong>Valor Total em execução</strong> desconta a
                        parte incontroversa já paga (mostra só o remanescente); <strong>Valor saída Execução</strong>{' '}
                        soma só o VALOR_REMANESCENTE (não o valor cheio) quando o processo que está saindo já teve a
                        parte incontroversa compensada antes, em outro mês; <strong>Valor Remanescente</strong> e{' '}
                        <strong>Valor Incontroverso</strong> são cards dedicados a esse detalhamento; o gráfico{' '}
                        <strong>Valor Remanescente Mês a Mês</strong> mostra a evolução desse saldo por mês de entrada
                        do processo; e o gráfico <strong>Valor Saída Execução Mês a Mês</strong> soma "Valor saída
                        Execução" com "Valor Incontroverso", mês a mês. Só o card <strong>Valor em Execução</strong>{' '}
                        continua com o valor cheio, sem desconto — veja o caveat de cada card/gráfico abaixo para o
                        detalhe exato.
                    </p>
                </DocCard>
            </DocSection>

            <DocSection
                id="indicadores"
                title="Indicadores"
                subtitle="Cards de volume, tempo e valor — a maioria olha o total atual, alguns olham só o período"
                icon="check"
            >
                <DocGrid>
                    <MetricCard
                        name="Total em Execução"
                        icon="scale"
                        what="Quantidade de processos atualmente na fase de Execução."
                        counts="Processos com ID_FASE = 12 (Execução) e situação Ativo, independente de quando entraram. Processos arquivados são excluídos, mesmo que ainda estejam com ID_FASE = 12 no LEXFLOW — arquivar um processo não atualiza sua fase automaticamente, então sem esse filtro processos já baixados continuariam contando aqui."
                        calc="Contagem direta, deduplicada por NUMERO_PROCESSO. Não é afetado pelo filtro de datas do calendário — mostra sempre o total acumulado atual."
                        interpret="Representa o estoque de trabalho em aberto no setor de Execução. Quanto maior, maior o volume de processos ainda em andamento."
                        caveat="Não muda com o filtro de período — é o único indicador que sempre reflete o total atual, igual ao 'Valor Total em execução' e 'Valor de Honorários'."
                    />
                    <MetricCard
                        name="Quantidade de entrada na Execução"
                        icon="check"
                        what="Processos que entraram na Execução no período selecionado E que ainda continuam nela hoje."
                        counts="Processos com DATA_EXECUCAO dentro do período selecionado E ID_FASE = 12 (ainda em Execução)."
                        calc="Contagem dos processos que atendem às duas condições ao mesmo tempo."
                        interpret="Mede quantos dos processos que entraram no período ainda estão represados na Execução — não é o total histórico de entradas (para isso, veja o gráfico 'Entradas na Execução por Mês')."
                        caveat="Um processo que entrou no período mas já saiu da Execução não conta aqui, mesmo aparecendo no gráfico de entradas por mês."
                    />
                    <MetricCard
                        name="Quantidade de saída da Execução"
                        icon="check"
                        what="Processos que saíram da Execução no período selecionado."
                        counts="Processos com DATA_COMPENSACAO_ALVARA preenchida dentro do período — independente da fase atual do processo."
                        calc="Contagem direta dos processos com DATA_COMPENSACAO_ALVARA no período."
                        interpret="Mede o volume de conclusão/baixa da Execução no período — quanto maior, mais processos foram finalizados."
                        caveat='Inclui processos já compensados (pagos), que saem da fase Financeiro e ficam arquivados (situação Arquivado, fase "Arquivado por Procedência", motivo "Valor Compensado") — a fase atual não é considerada, só a data de compensação do alvará.'
                    />
                    <MetricCard
                        name="Média de Tempo / Mediana de tempo"
                        icon="trendingUp"
                        what="Tempo (em dias) entre a entrada na Execução (DATA_EXECUCAO) e a saída dela (DATA_COMPENSACAO_ALVARA)."
                        counts="Processos com DATA_EXECUCAO e DATA_COMPENSACAO_ALVARA preenchidas e com duração positiva, independente da fase atual — inclui processos já compensados e arquivados por procedência."
                        calc="Média = soma das durações ÷ quantidade. Mediana = valor do meio da lista ordenada de durações. Sempre histórico completo, independente do filtro de período."
                        interpret="Compare os dois: se a Média estiver muito mais alta que a Mediana, é sinal de que um ou poucos processos com duração muito longa estão distorcendo a média — a Mediana costuma ser a referência mais confiável do tempo 'típico'."
                        caveat="A Média é sensível a outliers (processos muito antigos travados). Se ela parecer absurdamente alta, verifique a Mediana antes de desconfiar de um erro de cálculo."
                    />
                    <MetricCard
                        name="Estoque Inicial do período anterior"
                        icon="scale"
                        what="Estoque de processos em Execução estimado no início do período selecionado."
                        counts="Baseado no total atual, nas entradas e nas saídas do período (histórico completo para entradas/saídas)."
                        calc="Estoque Inicial = Total atual em Execução − Entradas no período + Saídas no período."
                        interpret="Permite comparar o tamanho da fila de Execução antes e depois do período selecionado."
                    />
                    <MetricCard
                        name="Valor de Honorários"
                        icon="info"
                        what="Soma dos honorários dos processos em Execução."
                        counts="Campo de valor de honorários dos processos com ID_FASE = 12, histórico completo."
                        calc="Soma direta, deduplicada por NUMERO_PROCESSO. Não é afetado pelo filtro de datas."
                        interpret="Indica o valor de honorários represado no setor de Execução."
                    />
                    <MetricCard
                        name="Valor Total em execução"
                        icon="info"
                        what="Soma do valor ainda em aberto de todos os processos atualmente em Execução."
                        counts="Processos com ID_FASE = 12 e situação Ativo, histórico completo. Quando já houve compensação parcial do alvará do incontroverso, soma VALOR_REMANESCENTE em vez do VALOR_EXECUCAO cheio."
                        calc="Soma direta, deduplicada por NUMERO_PROCESSO. Não é afetado pelo filtro de datas."
                        interpret="Junto com o 'Total em Execução', forma a base do cálculo do Ticket Médio."
                        caveat="Compensação parcial do alvará: a parte incontroversa já paga não conta mais aqui — ela sai deste total no mês em que é compensada e aparece no card 'Valor Incontroverso' daquele período."
                    />
                    <MetricCard
                        name="Valor em Execução"
                        icon="info"
                        what="Valor de execução dos processos que entraram na Execução no período selecionado E que ainda continuam nela hoje."
                        counts="Mesma dupla condição da 'Quantidade de entrada na Execução', mas somando o valor em vez de contar."
                        calc="Soma do VALOR_EXECUCAO dos processos que atendem às duas condições."
                        interpret="Não é o valor de causa inicial do processo — é o valor atualizado calculado na execução."
                    />
                    <MetricCard
                        name="Valor Remanescente"
                        icon="info"
                        what="Valor ainda em aberto de todos os processos atualmente em Execução, quando já houve compensação parcial do alvará do incontroverso."
                        counts="Mesmo conjunto de 'Total em Execução' / 'Valor Total em execução' (ID_FASE = 12 e situação Ativo, estoque atual), somando o campo VALOR_REMANESCENTE."
                        calc="Soma direta de VALOR_REMANESCENTE, sem fallback — processos sem compensação parcial do incontroverso (campo vazio) não contribuem para este card."
                        interpret="Compensação parcial do alvará: quando parte do valor de execução já caiu (parte incontroversa), o valor de fato ainda represado é o remanescente."
                        caveat="Não é filtrado por período — o remanescente normalmente vem de processos que entraram em Execução em períodos anteriores (a compensação do incontroverso costuma acontecer bem depois da entrada), então restringir por período esconderia a maior parte do saldo em aberto."
                    />
                    <MetricCard
                        name="Valor saída Execução"
                        icon="info"
                        what="Valor que efetivamente saiu da Execução no período — o que de fato foi pago."
                        counts="Valor de execução (VALOR_EXECUCAO, exibido em destaque) e valor de TED (VALOR_TED, exibido abaixo, menor), dos processos com DATA_COMPENSACAO_ALVARA no período — mesmo critério e mesma ressalva sobre fase atual da 'Quantidade de saída da Execução'."
                        calc="Soma direta dos processos de saída no período, para cada um dos dois valores."
                        interpret="Mede o valor financeiro que 'saiu' da Execução no período — útil para acompanhar o volume monetário liquidado."
                        caveat="Compensação parcial do alvará: se o processo já teve a parte incontroversa compensada antes (em outro mês), o valor em destaque soma só o VALOR_REMANESCENTE — o que de fato caiu nesta saída —, não o valor cheio. Isso evita contar a parte incontroversa duas vezes, já que ela foi somada no mês em que caiu, no card 'Valor Incontroverso'. Processos sem nenhum pagamento parcial (a maioria) continuam somando o valor cheio normalmente."
                    />
                    <MetricCard
                        name="Valor Incontroverso"
                        icon="info"
                        what="Valor incontroverso já compensado no período, mesmo com o processo ainda ativo na fase Execução."
                        counts="Soma de VALOR_INCONTROVERSO dos processos com DATA_COMPENSACAO_ALVARA_INCONTROVERSO dentro do período selecionado."
                        calc="Soma direta, independente de 'Valor saída Execução' — não é descontado nem somado a esse card, é um valor à parte."
                        interpret="Compensação parcial do alvará: mostra o que já caiu (parte incontroversa) antes mesmo do processo finalizar a Execução — para saber o total efetivamente recebido no período, some com 'Valor saída Execução' mentalmente."
                    />
                    <MetricCard
                        name="Ticket Médio"
                        icon="info"
                        what="Valor médio por processo, considerando todo o estoque atual de Execução."
                        counts="Todos os processos atualmente em Execução (histórico completo)."
                        calc="Ticket Médio = Valor Total em execução ÷ Total em Execução."
                        interpret="Quanto maior, maior o valor médio movimentado por processo em aberto na Execução."
                    />
                </DocGrid>
            </DocSection>

            <DocSection
                id="subfases"
                title="Matérias e subfases"
                subtitle="Rankings por subfase, matéria e tempo desde a última movimentação"
                icon="barChart"
            >
                <InfoBox>
                    Estes gráficos sempre mostram o total atual (histórico completo) de processos em Execução — não são
                    afetados pelo filtro de datas do calendário. Clique em uma barra ou fatia para filtrar o restante da
                    página por aquele valor.
                </InfoBox>
                <DocGrid>
                    <DocCard title="Valor Execução por Subfase">
                        <p>
                            Soma o VALOR_EXECUCAO dos processos em Execução, agrupado pela SUBFASE atual. Barras
                            roláveis quando há muitas subfases.
                        </p>
                    </DocCard>
                    <DocCard title="Processos por Subfase">
                        <p>Conta os processos em Execução por SUBFASE atual, com percentual do total.</p>
                    </DocCard>
                    <DocCard title="Valor Remanescente Mês a Mês">
                        <p>
                            Soma o VALOR_REMANESCENTE dos processos atualmente em Execução, agrupado pelo mês em que
                            cada processo ENTROU na Execução (DATA_EXECUCAO) — não pelo mês em que o incontroverso foi
                            compensado. Uma linha por ano, histórico completo, independente do filtro de calendário.
                        </p>
                        <p>
                            <strong>Exemplo:</strong> um processo que entrou em maio mas só teve a parte incontroversa
                            compensada em setembro aparece no gráfico em maio (o remanescente pertence ao mês de entrada
                            do processo), não em setembro.
                        </p>
                    </DocCard>
                    <DocCard title="Execução por Matéria">
                        <p>Distribuição (gráfico de pizza) dos processos em Execução por MATÉRIA.</p>
                    </DocCard>
                </DocGrid>
            </DocSection>

            <DocSection
                id="entradas-mes"
                title="Entradas na Execução por mês"
                subtitle="Quantidade e valor de entradas — histórico completo, com clique para filtrar a página"
                icon="trendingUp"
            >
                <InfoBox>
                    Diferente dos cards de "Indicadores", este gráfico conta e soma TODOS os processos cuja
                    DATA_EXECUCAO caiu em cada mês, sem exigir que o processo ainda esteja em Execução hoje — é o
                    recorte de "o que entrou historicamente", não "o que ainda está em aberto".
                </InfoBox>
                <DocCard title="Entradas na Execução por Mês">
                    <p>
                        Duas barras por mês — Quantidade e Valor — cada uma com sua própria escala (por isso o eixo Y
                        fica oculto: os dois números têm grandezas muito diferentes). Use o seletor de ano no canto
                        superior para trocar o ano exibido.
                    </p>
                    <p>
                        <strong>Clique em um mês</strong> para filtrar a página inteira pelo período daquele mês (1º ao
                        último dia). Clique de novo no mesmo mês para remover o filtro e voltar ao mês atual.
                    </p>
                </DocCard>
            </DocSection>

            <DocSection
                id="evolucao"
                title="Evolução mensal"
                subtitle="Valor de saída, mês a mês, comparado entre anos"
                icon="trendingUp"
            >
                <DocCard title="Valor Saída Execução Mês a Mês">
                    <p>
                        Mesmo valor do card "Valor saída Execução" (VALOR_EXECUCAO, ou VALOR_REMANESCENTE quando há
                        compensação parcial do alvará) somado ao card "Valor Incontroverso" (VALOR_INCONTROVERSO),
                        agrupado por mês — uma linha por ano (histórico completo, independente do filtro de calendário e
                        da fase atual do processo). Esta seção só aparece quando há dados de saída no histórico.
                    </p>
                    <p>
                        <strong>Compensação parcial do alvará:</strong> a parte incontroversa entra no mês em que caiu
                        (DATA_COMPENSACAO_ALVARA_INCONTROVERSO) e o remanescente entra no mês da compensação final
                        (DATA_COMPENSACAO_ALVARA) — sem duplicar. Até 09/09/2026 este gráfico somava VALOR_TED, não o
                        valor de execução.
                    </p>
                </DocCard>
            </DocSection>

            <DocSection
                id="atividades"
                title="Atividades"
                subtitle="Agendamentos do setor — com alternância entre 'Concluídas' e 'Por prazo'"
                icon="users"
            >
                <InfoBox>
                    No canto superior direito desta seção existe um botão com duas opções: <strong>Concluídas</strong>{' '}
                    (padrão) e <strong>Por prazo</strong>. Essa escolha muda o eixo temporal usado por{' '}
                    <strong>toda</strong> a seção — os KPIs, os dois gráficos, a "Produção Diária", a "Média Resolvidos
                    por Funcionário" e a lista de atividades trocam juntos.
                </InfoBox>

                <DocCard title='"Concluídas" vs. "Por prazo"'>
                    <DocGrid>
                        <div className="stack" style={{ gap: 6 }}>
                            <span>
                                <span className="badge ok">Concluídas (padrão)</span>
                            </span>
                            <p className="muted small">
                                Total = atividades <strong>criadas</strong> no período. Concluídas = atividades{' '}
                                <strong>encerradas</strong> no período (DATA_HORA_CONCLUSAO).
                            </p>
                        </div>
                        <div className="stack" style={{ gap: 6 }}>
                            <span>
                                <span className="badge info">Por prazo</span>
                            </span>
                            <p className="muted small">
                                Todas as métricas reclassificadas usando o <strong>PRAZO</strong> do agendamento como
                                referência de data, em vez da criação/conclusão — inclusive "Vencidas" e "Vencem hoje"
                                passam a considerar apenas prazos dentro do período selecionado.
                            </p>
                        </div>
                    </DocGrid>
                </DocCard>

                <DocGrid>
                    <MetricCard
                        name="Total / Em andamento / Vencidas / Vencem hoje / Concluídas"
                        icon="check"
                        what="Os cinco KPIs padrão de qualquer setor de agendamentos: volume total, em andamento, vencidas, vencendo hoje e concluídas."
                        counts='Status considerados "ativos": Recebido, Visualizado, Iniciado, Reaberto, Encaminhado. "Encerrado Cumprido" e "Encerrado Não Cumprido" contam como Concluídas.'
                        calc="Cada KPI usa o eixo temporal da visão ativa (Concluídas ou Por prazo) — ver caixa acima."
                        interpret="Use para monitorar o volume de trabalho pendente e a saúde geral do fluxo de atividades do setor."
                    />
                    <MetricCard
                        name="Por atividade"
                        icon="barChart"
                        what="Processos distintos por tipo de atividade do agendamento."
                        counts="Agendamentos criados no período (visão Concluídas) ou com prazo no período (visão Por prazo)."
                        calc="Contagem de processos únicos por ATIVIDADE, com percentual do total."
                        interpret="Clique em uma barra para filtrar a lista de atividades por aquele tipo."
                    />
                    <MetricCard
                        name="Demandas por Funcionário"
                        icon="users"
                        what="Atividades encerradas por funcionário, separadas em Cumprido e Não Cumprido."
                        counts="Agendamentos encerrados no período (Concluídas) ou com prazo no período (Por prazo), atribuídos ao funcionário que encerrou."
                        calc="Contagem por funcionário e status de encerramento."
                        interpret="Clique no nome de um funcionário para filtrar a lista de atividades por ele."
                    />
                    <MetricCard
                        name="Produção Diária – Execução (mês a mês)"
                        icon="trendingUp"
                        what="Quantidade de atividades com status 'Encerrado Cumprido', por mês (histórico completo)."
                        counts='Apenas atividades "Encerrado Cumprido" — não conta "Encerrado Não Cumprido".'
                        calc="Agrupamento por mês de conclusão (Concluídas) ou de prazo (Por prazo). Clique em um mês para ver o detalhamento dia a dia daquele mês; clique em 'Voltar à visão anual' para retornar."
                        interpret="Use para identificar meses de maior ou menor produtividade do setor."
                    />
                    <MetricCard
                        name="Média Resolvidos por Funcionário"
                        icon="clock"
                        what="Média diária de atividades 'Encerrado Cumprido' concluídas por cada funcionário, no período selecionado."
                        counts='Apenas atividades "Encerrado Cumprido".'
                        calc="Média = total de atividades cumpridas pelo funcionário ÷ número de dias distintos com conclusão (ou prazo, na visão Por prazo) dentro do período."
                        interpret="A linha tracejada verde marca a meta de referência (20). Funcionários com barra além da linha estão acima da meta."
                    />
                </DocGrid>
            </DocSection>

            <DocSection
                id="filtros"
                title="Filtros disponíveis"
                subtitle="Como personalizar a visão do dashboard"
                icon="filter"
            >
                <DocGrid>
                    {FILTERS.map((f) => (
                        <DocCard key={f.name} title={f.name}>
                            <p>{f.desc}</p>
                        </DocCard>
                    ))}
                </DocGrid>
            </DocSection>
        </DocPage>
    )
}
