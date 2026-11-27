import {
    Code,
    DocCallout,
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

// Guia da Execução Condenação. Texto da v1: LexHub/src/pages/documentacao/Execucao.tsx.

const TOC: TocItem[] = [
    { id: 'como-funciona', label: 'Como funciona' },
    { id: 'indicadores', label: 'Indicadores' },
    { id: 'subfases', label: 'Matérias, subfases e comarcas' },
    { id: 'entradas-mes', label: 'Entradas por mês' },
    { id: 'evolucao', label: 'Evolução mensal' },
    { id: 'atividades', label: 'Atividades' },
    { id: 'diligencias', label: 'Diligências' },
    { id: 'exportar', label: 'Exportar' },
    { id: 'filtros', label: 'Filtros' },
]

const FILTERS: { name: string; badge: string; tone: Tone; desc: string }[] = [
    {
        name: 'Período (calendário)',
        badge: 'Topo',
        tone: 'accent',
        desc: "Afeta os cards de 'entrada/saída no período' e os KPIs de Atividades. Não afeta os cards e gráficos marcados como 'histórico completo'.",
    },
    {
        name: 'UF / Comarca / Matéria / Subfase',
        badge: 'Janela de filtros',
        tone: 'info',
        desc: 'Na janela Filtros do topo da página, com as opções da base inteira. Aceitam mais de um valor.',
    },
    {
        name: 'Matéria / Subfase / Comarca',
        badge: 'Clique',
        tone: 'ok',
        desc: 'Clique em uma fatia, barra ou município dos gráficos da seção 03 para ligar o mesmo filtro da página.',
    },
    {
        name: 'Funcionário / Atividade / Situação',
        badge: 'Clique',
        tone: 'violet',
        desc: 'Na seção Atividades, clique em uma barra, nome de funcionário ou card de KPI para filtrar a lista de tarefas.',
    },
    {
        name: 'Concluídas / Por prazo',
        badge: 'Alternância',
        tone: 'warn',
        desc: 'Alterna o eixo temporal (data de conclusão vs. data de prazo) de toda a seção Atividades.',
    },
    {
        name: 'Diligência / Colaborador',
        badge: 'Clique',
        tone: 'violet',
        desc: 'Na seção Diligências (NG e LARJ), os cards de alvará filtram os gráficos pelo tipo de diligência e o ranking mostra os números de um colaborador.',
    },
]

export function ExecucaoDoc() {
    return (
        <DocPage
            title="Execução Condenação"
            tags={['NG', 'LA', 'LARJ']}
            note="Mesma lógica nas três unidades (a LA não tem a seção Diligências)"
            toc={TOC}
            intro={
                <>
                    Este guia explica cada número e gráfico do dashboard de Execução. Você vai entender a diferença
                    entre "processos ainda em execução" e "processos que entraram/saíram no período", como funciona o
                    filtro por prazo das atividades e o que cada gráfico representa.{' '}
                    <strong>Nenhum conhecimento técnico é necessário.</strong>
                </>
            }
            header={
                <DocCallout caps title="Entrada e saída da fase de Execução" badge="ID_FASE = 12">
                    <p>
                        Um processo entra na fase de Execução (<Code>ID_FASE = 12</Code>) quando o campo{' '}
                        <Code>DATA_EXECUCAO</Code> é preenchido no LEXFLOW. A saída é medida pela data de compensação do
                        alvará (<Code>DATA_COMPENSACAO_ALVARA</Code>), independente da fase atual.
                    </p>
                    <DocGrid>
                        <DocMini label="Entrada">
                            <Hl tone="ok">DATA_EXECUCAO</Hl> preenchida no LEXFLOW.
                        </DocMini>
                        <DocMini label="Saída">
                            <Hl tone="info">DATA_COMPENSACAO_ALVARA</Hl> — processos já compensados (pagos) deixam a
                            fase Financeiro e ficam arquivados (situação Arquivado, fase "Arquivado por Procedência",
                            motivo "Valor Compensado"), mas continuam contando no histórico de saídas.
                        </DocMini>
                    </DocGrid>
                </DocCallout>
            }
        >
            <DocSection
                id="como-funciona"
                title="01 — Como o dashboard funciona"
                subtitle="Duas perguntas diferentes: 'o que está em execução hoje' e 'o que entrou/saiu no período'"
            >
                <p>
                    O dashboard combina dois recortes: (1) o que está atualmente na fase de Execução, e (2) o que entrou
                    ou saiu dela dentro do período selecionado no calendário. Nenhum card de período exige que o
                    processo continue na fase de Execução hoje.
                </p>
                <DocGrid cols={2}>
                    <DocFeature
                        title='"Ainda em execução hoje"'
                        tone="ok"
                        icon="scale"
                        badge="Cards de Indicadores"
                        framed
                    >
                        <p>
                            Total em Execução, Valor Total em execução e Valor Remanescente — o estoque de agora,
                            independente do período.
                        </p>
                    </DocFeature>
                    <DocFeature
                        title='"Entrou/saiu no período"'
                        tone="info"
                        icon="trendingUp"
                        badge="Cards de período + gráficos"
                        framed
                    >
                        <p>
                            Quantidade e valor de entrada e saída, incontroverso, média e mediana de tempo, e os
                            gráficos "Entradas na Execução por Mês" e "Valor Saída Execução Mês a Mês" — olham só a
                            data, sem exigir que o processo continue em Execução hoje.
                        </p>
                    </DocFeature>
                </DocGrid>
                <DocCallout tone="warn" icon="alert" title="Dois recortes que parecem iguais, mas não são">
                    <p>
                        <strong>Exemplo prático:</strong> um processo que entrou em Execução em março e já saiu para o
                        Financeiro em abril conta no card "Quantidade de entrada na Execução" (com o período em março) e
                        no gráfico "Entradas na Execução por Mês" (março), mas <strong>não</strong> conta no "Total em
                        Execução" — esse card só conta processos que estão na fase Execução hoje.
                    </p>
                    <p>
                        Os cards de entrada não exigem a fase atual justamente para bater com o gráfico mensal: o mesmo
                        mês dá o mesmo número nos dois. O estoque de agora (Total, Valor Total e Remanescente) responde
                        "quanto ainda temos em aberto"; os cards de período e os gráficos respondem "quanto
                        entrou/saiu".
                    </p>
                </DocCallout>
                <DocGrid cols={2}>
                    <DocFeature title="Cada processo conta uma única vez" tone="accent" badge="NUMERO_PROCESSO">
                        <p>
                            Um mesmo processo pode ter mais de uma parte adversa cadastrada no LEXFLOW. Todos os
                            cálculos do dashboard deduplicam por NUMERO_PROCESSO (o identificador único do processo),
                            garantindo que ele seja contado (e seu valor somado) apenas uma vez, mesmo quando existe
                            mais de um registro para o mesmo processo na base.
                        </p>
                    </DocFeature>
                    <DocFeature
                        title="Compensação parcial do alvará"
                        tone="violet"
                        badge="Incontroverso / remanescente"
                    >
                        <p>
                            Um processo pode ser pago em duas partes. A parte incontroversa (a fatia sobre a qual não há
                            discussão) costuma cair primeiro — LEXFLOW registra o valor (VALOR_INCONTROVERSO) e a data
                            de compensação (DATA_COMPENSACAO_ALVARA_INCONTROVERSO). O restante fica como
                            VALOR_REMANESCENTE, e só é pago depois — quando isso acontece, a DATA_COMPENSACAO_ALVARA
                            "oficial" é preenchida e o processo finalmente sai da fase Execução.
                        </p>
                    </DocFeature>
                </DocGrid>
                <DocCallout
                    tone="violet"
                    icon="layers"
                    title="O que a compensação parcial muda"
                    badge="4 cards · 2 gráficos"
                >
                    <ul>
                        <li>
                            <strong>Valor Total em execução</strong> desconta a parte incontroversa já paga (mostra só o
                            remanescente).
                        </li>
                        <li>
                            <strong>Valor saída Execução</strong> soma o VALOR_REMANESCENTE (não o valor cheio) quando o
                            processo que está saindo já teve a parte incontroversa compensada, mais o incontroverso
                            compensado no período — cada parcela pela sua própria data, sem contar duas vezes.
                        </li>
                        <li>
                            <strong>Valor Remanescente</strong> e <strong>Valor Incontroverso</strong> são cards
                            dedicados a esse detalhamento.
                        </li>
                        <li>
                            O gráfico <strong>Valor Remanescente Mês a Mês</strong> mostra a evolução desse saldo por
                            mês de entrada do processo.
                        </li>
                        <li>
                            O gráfico <strong>Valor Saída Execução Mês a Mês</strong> usa a mesma regra do card "Valor
                            saída Execução", mês a mês.
                        </li>
                    </ul>
                    <p>
                        Só o card <strong>Valor em Execução</strong> continua com o valor cheio, sem desconto — veja o
                        caveat de cada card/gráfico abaixo para o detalhe exato.
                    </p>
                </DocCallout>
            </DocSection>

            <DocSection
                id="indicadores"
                title="02 — Indicadores"
                subtitle="Cards de volume, tempo e valor — três olham o estoque atual, os demais olham o período"
                badge="Estoque atual + período"
            >
                <DocGrid>
                    <MetricCard
                        name="Total em Execução"
                        icon="scale"
                        what="Quantidade de processos atualmente na fase de Execução."
                        counts="Processos com ID_FASE = 12 (Execução) e situação Ativo, independente de quando entraram. Processos arquivados são excluídos, mesmo que ainda estejam com ID_FASE = 12 no LEXFLOW — arquivar um processo não atualiza sua fase automaticamente, então sem esse filtro processos já baixados continuariam contando aqui."
                        calc="Contagem direta, deduplicada por NUMERO_PROCESSO. Não é afetado pelo filtro de datas do calendário — mostra sempre o total acumulado atual."
                        interpret="Representa o estoque de trabalho em aberto no setor de Execução. Quanto maior, maior o volume de processos ainda em andamento."
                        caveat="Não muda com o filtro de período — sempre reflete o total atual, igual ao 'Valor Total em execução' e ao 'Valor Remanescente'."
                    />
                    <MetricCard
                        name="Quantidade de entrada na Execução"
                        icon="check"
                        what="Processos que entraram na Execução no período selecionado."
                        counts="Processos com DATA_EXECUCAO dentro do período selecionado, independente da fase atual."
                        calc="Contagem direta, deduplicada por NUMERO_PROCESSO."
                        interpret="Mede o volume de entradas no período — o mesmo número do gráfico 'Entradas na Execução por Mês' para o mesmo mês."
                        caveat="Um processo que entrou no período e já saiu da Execução continua contando aqui (ele só some do 'Total em Execução')."
                    />
                    <MetricCard
                        name="Quantidade de saída da Execução"
                        icon="check-circle"
                        what="Processos que saíram da Execução no período selecionado."
                        counts="Processos com DATA_COMPENSACAO_ALVARA preenchida dentro do período — independente da fase atual do processo."
                        calc="Contagem direta dos processos com DATA_COMPENSACAO_ALVARA no período."
                        interpret="Mede o volume de conclusão/baixa da Execução no período — quanto maior, mais processos foram finalizados."
                        caveat='Inclui processos já compensados (pagos), que saem da fase Financeiro e ficam arquivados (situação Arquivado, fase "Arquivado por Procedência", motivo "Valor Compensado") — a fase atual não é considerada, só a data de compensação do alvará.'
                    />
                    <MetricCard
                        name="Média de Tempo · Mediana de Tempo"
                        icon="clock"
                        what="Tempo (em dias) entre a entrada na Execução (DATA_EXECUCAO) e a saída dela (DATA_COMPENSACAO_ALVARA)."
                        counts="Processos com DATA_COMPENSACAO_ALVARA dentro do período selecionado, com DATA_EXECUCAO preenchida e duração positiva, independente da fase atual — inclui processos já compensados e arquivados por procedência."
                        calc="Média = soma das durações ÷ quantidade. Mediana = valor do meio da lista ordenada de durações. Na tela são dois cards separados, ambos amostrados pela saída no período."
                        interpret="Compare os dois: se a Média estiver muito mais alta que a Mediana, é sinal de que um ou poucos processos com duração muito longa estão distorcendo a média — a Mediana costuma ser a referência mais confiável do tempo 'típico'."
                        caveat="A Média é sensível a outliers (processos muito antigos travados). Se ela parecer absurdamente alta, verifique a Mediana antes de desconfiar de um erro de cálculo."
                    />
                    <MetricCard
                        name="Estoque Inicial do período anterior"
                        icon="layers"
                        what="Estoque de processos em Execução estimado no início do período selecionado."
                        counts="Baseado no total atual, nas entradas e nas saídas do período (histórico completo para entradas/saídas)."
                        calc="Estoque Inicial = Total atual em Execução − Entradas no período + Saídas no período."
                        interpret="Permite comparar o tamanho da fila de Execução antes e depois do período selecionado."
                    />
                    <MetricCard
                        name="Valor Total em execução"
                        icon="dollar"
                        what="Soma do valor ainda em aberto de todos os processos atualmente em Execução."
                        counts="Processos com ID_FASE = 12 e situação Ativo, histórico completo. Quando já houve compensação parcial do alvará do incontroverso, soma VALOR_REMANESCENTE em vez do VALOR_EXECUCAO cheio."
                        calc="Soma direta, deduplicada por NUMERO_PROCESSO. Não é afetado pelo filtro de datas."
                        interpret="Junto com o 'Total em Execução', forma a base do cálculo do Ticket Médio. Os honorários não têm card próprio: o valor de honorários só sai no relatório (seção 08)."
                        caveat="Compensação parcial do alvará: a parte incontroversa já paga não conta mais aqui — ela sai deste total no mês em que é compensada e aparece no card 'Valor Incontroverso' daquele período."
                    />
                    <MetricCard
                        name="Valor em Execução"
                        icon="dollar"
                        what="Valor de execução dos processos que entraram na Execução no período selecionado."
                        counts="Mesmo conjunto da 'Quantidade de entrada na Execução' (DATA_EXECUCAO no período, independente da fase atual), somando o valor em vez de contar."
                        calc="Soma do VALOR_EXECUCAO cheio, mesmo quando já houve compensação parcial do incontroverso. Embaixo, o ticket médio de entrada: valor ÷ quantidade de entrada."
                        interpret="Não é o valor de causa inicial do processo — é o valor atualizado calculado na execução."
                    />
                    <MetricCard
                        name="Valor Remanescente"
                        icon="dollar"
                        what="Valor ainda em aberto de todos os processos atualmente em Execução, quando já houve compensação parcial do alvará do incontroverso."
                        counts="Mesmo conjunto de 'Total em Execução' / 'Valor Total em execução' (ID_FASE = 12 e situação Ativo, estoque atual), somando o campo VALOR_REMANESCENTE."
                        calc="Soma direta de VALOR_REMANESCENTE, sem fallback — processos sem compensação parcial do incontroverso (campo vazio) não contribuem para este card."
                        interpret="Compensação parcial do alvará: quando parte do valor de execução já caiu (parte incontroversa), o valor de fato ainda represado é o remanescente."
                        caveat="Não é filtrado por período — o remanescente normalmente vem de processos que entraram em Execução em períodos anteriores (a compensação do incontroverso costuma acontecer bem depois da entrada), então restringir por período esconderia a maior parte do saldo em aberto."
                    />
                    <MetricCard
                        name="Valor saída Execução"
                        icon="dollar"
                        what="Valor que efetivamente saiu da Execução no período — o que de fato foi pago."
                        counts="Em destaque: o valor dos processos com DATA_COMPENSACAO_ALVARA no período (independente da fase atual) mais o VALOR_INCONTROVERSO dos processos com DATA_COMPENSACAO_ALVARA_INCONTROVERSO no período. Embaixo, menor: o Valor TED dessas mesmas saídas."
                        calc="Valor = remanescente (ou valor cheio) pela compensação do alvará + incontroverso pela compensação dele, cada parcela pela sua data. TED: na compensação do incontroverso entra o VALOR_TED; na compensação final entram VALOR_TED_2 + VALOR_TED_3 (ou os três, quando não houve incontroverso)."
                        interpret="Mede o valor financeiro que 'saiu' da Execução no período — o total efetivamente recebido, já com a parte incontroversa."
                        caveat="Compensação parcial do alvará: se o processo já teve a parte incontroversa compensada, a parcela da compensação final soma só o VALOR_REMANESCENTE, não o valor cheio — a parte incontroversa já entrou no período em que caiu. Processos sem nenhum pagamento parcial (a maioria) somam o valor cheio normalmente."
                    />
                    <MetricCard
                        name="Valor Incontroverso"
                        icon="dollar"
                        what="Valor incontroverso já compensado no período, mesmo com o processo ainda ativo na fase Execução."
                        counts="Soma de VALOR_INCONTROVERSO dos processos com DATA_COMPENSACAO_ALVARA_INCONTROVERSO dentro do período selecionado."
                        calc="Soma direta. Este valor já está incluído no 'Valor saída Execução' — o card mostra só a parcela incontroversa, em separado."
                        interpret="Compensação parcial do alvará: mostra o que já caiu (parte incontroversa) antes mesmo do processo finalizar a Execução. Não some com o 'Valor saída Execução', senão o incontroverso conta duas vezes."
                    />
                    <MetricCard
                        name="Ticket Médio"
                        icon="percent"
                        what="Valor médio por processo, considerando todo o estoque atual de Execução."
                        counts="Todos os processos atualmente em Execução (histórico completo)."
                        calc="Ticket Médio = Valor Total em execução ÷ Total em Execução."
                        interpret="Quanto maior, maior o valor médio movimentado por processo em aberto na Execução."
                    />
                </DocGrid>
            </DocSection>

            <DocSection
                id="subfases"
                title="03 — Matérias, subfases e comarcas"
                subtitle="Processos em execução agora por subfase, matéria e comarca, mais a TRE"
                badge="Estoque atual"
            >
                <DocCallout icon="filter" title="Sem filtro de datas, mas clicáveis">
                    <p>
                        Estes gráficos mostram os processos em Execução agora — não são afetados pelo filtro de datas do
                        calendário (exceto a TRE e os modos Entradas/Saídas do mapa). Clique em uma barra, fatia ou
                        município para filtrar o restante da página por aquele valor.
                    </p>
                </DocCallout>
                <DocGrid cols={2}>
                    <DocFeature title="Valor Execução por Subfase" tone="accent" badge="VALOR_EXECUCAO">
                        <p>
                            Soma o VALOR_EXECUCAO dos processos em Execução, agrupado pela SUBFASE atual. Barras
                            roláveis quando há muitas subfases.
                        </p>
                    </DocFeature>
                    <DocFeature title="Processos por Subfase" tone="info" badge="% do total">
                        <p>Conta os processos em Execução por SUBFASE atual, com percentual do total.</p>
                    </DocFeature>
                    <DocFeature title="Valor Remanescente Mês a Mês" tone="violet" badge="Mês de entrada">
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
                    </DocFeature>
                    <DocFeature title="Execução por Matéria" tone="ok" badge="Pizza">
                        <p>Distribuição (gráfico de pizza) dos processos em Execução por MATÉRIA.</p>
                    </DocFeature>
                    <DocFeature title="Mapa de processos por comarca" tone="info" badge="Total · Entradas · Saídas">
                        <p>
                            Mapa com três critérios: <strong>Total</strong> (em execução agora),{' '}
                            <strong>Entradas</strong> e <strong>Saídas</strong> (no período). Passe o cursor num
                            município para ver quantidade, valor e tempo médio; clique para filtrar a página pela
                            comarca.
                        </p>
                    </DocFeature>
                    <DocFeature title="Taxa de Redução de Estoque (TRE)" tone="warn" badge="−50 a 50">
                        <p>
                            Medidor de −50 a 50, com o risco no zero:{' '}
                            <Code>TRE = (Total em Execução − Estoque Inicial) × 100 ÷ Estoque Inicial</Code>, onde o
                            Estoque Inicial é o do card da seção 02. Usa o período do calendário.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="entradas-mes"
                title="04 — Entradas na Execução por mês"
                subtitle="Quantidade e valor de entradas — histórico completo, um ano por vez"
                badge="Histórico completo"
            >
                <DocCallout tone="info" icon="calendar" title="O que entrou historicamente">
                    <p>
                        Conta e soma TODOS os processos cuja DATA_EXECUCAO caiu em cada mês, sem exigir que o processo
                        ainda esteja em Execução hoje — a mesma regra do card "Quantidade de entrada na Execução", mas
                        mês a mês e sem o filtro de período.
                    </p>
                </DocCallout>
                <DocGrid cols={2}>
                    <DocFeature title="Entradas por mês" tone="accent" icon="barChart" badge="Quantidade">
                        <p>
                            Colunas com a quantidade de processos que entraram em cada mês do ano escolhido. Use o
                            seletor de ano no canto do gráfico (padrão: o ano mais recente).
                        </p>
                    </DocFeature>
                    <DocFeature title="Valor das entradas" tone="info" icon="dollar" badge="VALOR_EXECUCAO">
                        <p>
                            Gráfico separado, ao lado, com a soma do valor de execução das entradas de cada mês do mesmo
                            ano. Os dois gráficos só mostram valores no tooltip; não filtram a página.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="evolucao"
                title="05 — Evolução mensal"
                subtitle="Valor de saída, mês a mês, comparado entre anos"
                badge="Uma linha por ano"
            >
                <Formula>
                    Valor Saída Execução Mês a Mês = remanescente (ou valor cheio) pela compensação do alvará +
                    incontroverso pela compensação dele
                </Formula>
                <p>
                    A mesma regra do card "Valor saída Execução" (que já inclui o incontroverso), agrupada por mês — uma
                    linha por ano (histórico completo, independente do filtro de calendário e da fase atual do
                    processo). Sem dados no histórico, o gráfico mostra "Sem dados no histórico."
                </p>
                <DocGrid cols={2}>
                    <DocFeature title="Compensação parcial do alvará" tone="violet" badge="Sem duplicar">
                        <p>
                            A parte incontroversa entra no mês em que caiu (DATA_COMPENSACAO_ALVARA_INCONTROVERSO) e o
                            remanescente entra no mês da compensação final (DATA_COMPENSACAO_ALVARA) — sem duplicar.
                        </p>
                    </DocFeature>
                    <DocFeature title="Até 09/09/2026" tone="warn" icon="history" badge="Mudança">
                        <p>Este gráfico somava VALOR_TED, não o valor de execução.</p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="atividades"
                title="06 — Atividades"
                subtitle="Agendamentos do setor — com alternância entre 'Concluídas' e 'Por prazo'"
                badge="Concluídas · Por prazo"
            >
                <DocCallout icon="sliders" title="Uma escolha que muda a seção inteira">
                    <p>
                        No canto superior direito desta seção existe um botão com duas opções:{' '}
                        <strong>Concluídas</strong> (padrão) e <strong>Por prazo</strong>. Essa escolha muda o eixo
                        temporal usado por <strong>toda</strong> a seção — os KPIs, os dois gráficos, a "Produção
                        Diária", a "Média Resolvidos por Funcionário" e a lista de atividades trocam juntos.
                    </p>
                </DocCallout>
                <DocGrid cols={2}>
                    <DocFeature title="Concluídas" tone="ok" icon="check-circle" badge="Padrão" framed>
                        <p>
                            Total = atividades <strong>criadas</strong> no período. Concluídas = atividades{' '}
                            <strong>encerradas</strong> no período (DATA_HORA_CONCLUSAO).
                        </p>
                    </DocFeature>
                    <DocFeature title="Por prazo" tone="info" icon="calendar" badge="PRAZO" framed>
                        <p>
                            Todas as métricas reclassificadas usando o <strong>PRAZO</strong> do agendamento como
                            referência de data, em vez da criação/conclusão — inclusive "Vencidas" e "Vencem hoje"
                            passam a considerar apenas prazos dentro do período selecionado.
                        </p>
                    </DocFeature>
                </DocGrid>
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
                        icon="target"
                        what="Média diária de atividades 'Encerrado Cumprido' concluídas por cada funcionário, no período selecionado."
                        counts='Apenas atividades "Encerrado Cumprido".'
                        calc="Média = total de atividades cumpridas pelo funcionário ÷ número de dias distintos com conclusão (ou prazo, na visão Por prazo) dentro do período."
                        interpret="A linha tracejada verde marca a meta de referência (20). Funcionários com barra além da linha estão acima da meta."
                    />
                    <MetricCard
                        name="Atividades vencidas por dias de atraso"
                        icon="alert"
                        what="Detalhamento das vencidas por faixa de atraso, de 1 dia até 6 dias ou mais."
                        counts="As atividades do card 'Vencidas' da visão ativa."
                        calc="Quantidade e percentual por faixa de dias de atraso."
                        interpret="Abre ao clicar no card 'Vencidas' (os outros cards filtram a seção pela situação)."
                    />
                    <MetricCard
                        name="Lista de atividades"
                        icon="list"
                        what="As tarefas da visão ativa, com os filtros da seção (funcionário, atividade, situação, status)."
                        counts="Mesmo universo dos cards da seção."
                        calc="Modo compacto ou expandido (com nº do processo e data de criação), paginada. O prazo fica vermelho quando venceu e laranja quando vence hoje."
                        interpret="Use para chegar às tarefas por trás de um número: clique num card, barra ou funcionário e a lista acompanha."
                    />
                </DocGrid>
            </DocSection>

            <DocSection
                id="diligencias"
                title="07 — Diligências"
                subtitle="Quantas vezes a diligência foi feita em cada processo, ranking por colaborador e alvarás"
                badge="NG e LARJ"
            >
                <DocCallout icon="info" title="Só NG e LARJ">
                    <p>
                        A LA não tem esta seção (a rota da unidade não manda os dados). Tudo aqui usa os agendamentos de
                        diligência criados no período do calendário.
                    </p>
                </DocCallout>
                <DocGrid cols={2}>
                    <DocFeature title="Processos com mais diligências" tone="accent" badge="Por processo">
                        <p>
                            Agendamentos de diligência por processo, criados no período — o mesmo processo pode aparecer
                            com várias diligências.
                        </p>
                    </DocFeature>
                    <DocFeature title="Ranking por colaborador" tone="info" badge="Clique">
                        <p>
                            Diligências por colaborador. Clique num nome para que os cards abaixo mostrem só os números
                            dele.
                        </p>
                    </DocFeature>
                    <DocFeature title="Alvarás" tone="ok" badge="Cards clicáveis">
                        <p>
                            "Diligências de expedição de alvará" (criadas no período) e "Expedições de alvará cumpridas"
                            (encerradas como cumpridas no período). Clique num deles para filtrar os gráficos por esse
                            tipo.
                        </p>
                    </DocFeature>
                    <DocFeature title="Valor realizado (alvará)" tone="violet" badge="Ver lista">
                        <p>
                            Soma o valor da execução dos processos com pelo menos uma expedição de alvará cumprida no
                            período, sem repetir o processo. Clique para ver a lista de processos.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection id="exportar" title="08 — Exportar" subtitle="Relatório de processos com os campos escolhidos">
                <p>
                    O botão <strong>Exportar</strong> do cabeçalho gera o relatório de Processos. Primeiro escolha o
                    recorte — <strong>Entradas no período</strong> (padrão), <strong>Saídas no período</strong> ou{' '}
                    <strong>Total em execução agora</strong>, os mesmos dos cards de Indicadores — e depois os campos,
                    em cinco grupos: Identificação, Datas, Valores (inclui Valor de Honorários e Valor TED),
                    Incontroverso e Saída no período.
                </p>
            </DocSection>

            <DocSection
                id="filtros"
                title="09 — Filtros disponíveis"
                subtitle="Como personalizar a visão do dashboard"
                tone="info"
            >
                <DocGrid cols={2}>
                    {FILTERS.map((f) => (
                        <DocFeature key={f.name} title={f.name} badge={f.badge} badgeTone={f.tone}>
                            <p>{f.desc}</p>
                        </DocFeature>
                    ))}
                </DocGrid>
            </DocSection>
        </DocPage>
    )
}
