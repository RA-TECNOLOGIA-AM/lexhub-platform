import {
    DocCallout,
    DocFeature,
    DocGrid,
    DocMini,
    DocPage,
    DocSection,
    Formula,
    Hl,
    MetricCard,
    type TocItem,
} from '../components/DocParts.tsx'

// Guia trazido da v1: LexHub/src/pages/documentacao/ExecucaoEstrategicoGeral.tsx (convertido para as peças da V2).

const TOC: TocItem[] = [
    { id: 'como-funciona', label: 'Como funciona' },
    { id: 'indicadores', label: 'Indicadores' },
    { id: 'tendencia', label: 'Entradas e saídas' },
    { id: 'confeccao-cs', label: 'Confecção CS' },
    { id: 'alvaras', label: 'Alvarás expedidos' },
    { id: 'filtros', label: 'Filtros' },
    { id: 'relatorio', label: 'Relatório Personalizado' },
]

const FILTERS: { name: string; badge: string; tone: 'accent' | 'info' | 'ok' | 'neutral'; desc: string }[] = [
    {
        name: 'Período (calendário)',
        badge: 'Calendário',
        tone: 'accent',
        desc: "Afeta os KPIs de entrada/saída da seção Indicadores e da Confecção CS. Não afeta os cards e gráficos marcados como 'histórico completo'.",
    },
    {
        name: 'Escopo (Ambos / Condenação / Acordos)',
        badge: 'Topo',
        tone: 'accent',
        desc: "Na barra de filtros do topo. Restringe a soma de todos os indicadores e gráficos a um só dos dois dashboards de origem — ou mantém a soma dos dois ('Ambos').",
    },
    {
        name: 'UF',
        badge: 'Topo · múltipla',
        tone: 'info',
        desc: 'Dropdown com múltipla escolha na barra de filtros. Restringe todo o dashboard (Condenação e Acordos) às UFs selecionadas. As opções vêm da união dos dois dashboards de origem.',
    },
    {
        name: 'Comarca',
        badge: 'Topo + Clique',
        tone: 'info',
        desc: "Dropdown com múltipla escolha na barra de filtros, ou clique direto numa barra do gráfico 'Processos por Comarca' — os dois controlam o mesmo filtro. Restringe todo o dashboard às comarcas selecionadas.",
    },
    {
        name: 'Matéria / Subfase',
        badge: 'Topo + Clique',
        tone: 'ok',
        desc: 'Dropdown com múltipla escolha na barra de filtros, ou clique direto numa fatia/barra dos gráficos de Matéria e Subfase — os dois controlam o mesmo filtro. As opções vêm da união dos dois dashboards de origem.',
    },
    {
        name: 'Ano de Ajuizamento',
        badge: 'Topo + Clique',
        tone: 'neutral',
        desc: "Clique numa fatia das pizzas 'Ano de Ajuizamento' (seção 02) ou escolha no dropdown da barra de filtros. Um ano por vez.",
    },
    {
        name: 'Modo do gráfico (Matérias / Subfase / Comarca / Condenação x Acordos)',
        badge: 'Seletor',
        tone: 'neutral',
        desc: 'Seletores próprios de cada gráfico para trocar entre visão Total, Entrada, Saída ou Valor Entrada, conforme o gráfico.',
    },
    {
        name: 'Atividade / Funcionário / Situação (Confecção CS)',
        badge: 'Clique + Topo',
        tone: 'neutral',
        desc: "Clique numa barra de 'Por atividade' ou num nome de 'Demandas por funcionário' para filtrar a seção Confecção CS; a Situação fica na janela de filtros. 'Limpar filtros' tira os três de uma vez.",
    },
]

export function ExecucaoEstrategicoDoc() {
    return (
        <DocPage
            title="Execução Estratégico — NG, LA e LARJ"
            tags={['NG', 'LA', 'LARJ']}
            note="Mesma lógica nas três unidades"
            toc={TOC}
            intro={
                <>
                    Este guia explica o dashboard de Execução Estratégico: uma visão combinada que soma os dados dos
                    dashboards Execução Estratégico (Condenação) e Execução Acordos Estratégico num único conjunto de
                    indicadores e gráficos. <strong>Nenhum conhecimento técnico é necessário.</strong>
                </>
            }
            header={
                <DocCallout caps title="Visão combinada: Condenação + Acordos" badge="Soma sem duplicar">
                    <p>
                        Este dashboard busca os dados dos dois dashboards de origem do mesmo escritório (Condenação e
                        Acordos) e soma indicador a indicador, gráfico a gráfico. Os dois universos são mutuamente
                        exclusivos — a base de Condenação já exclui processos com etiqueta "Acordo" — então a soma dá o
                        total real de "Execução" (Condenação + Acordos), sem risco de contar o mesmo processo duas
                        vezes.
                    </p>
                    <DocGrid>
                        <DocMini label="Entre unidades">
                            NG, LA e LARJ têm a mesma lógica, cada um somando só os dados do seu próprio escritório —
                            inclusive a seção <Hl>"Confecção CS"</Hl>, que existe nas três.
                        </DocMini>
                        <DocMini label="Filtro de Escopo">
                            <Hl tone="info">Ambos / Condenação / Acordos</Hl> — controla quais dos dois lados entram na
                            soma de cada indicador e gráfico.
                        </DocMini>
                    </DocGrid>
                </DocCallout>
            }
        >
            <DocSection
                id="como-funciona"
                title="Como o dashboard funciona"
                icon="info"
                subtitle="Soma dos dashboards Execução Estratégico (Condenação) e Execução Acordos Estratégico"
            >
                <Formula>Execução Estratégico = Execução Condenação + Execução Acordos</Formula>
                <DocGrid cols={3}>
                    <DocFeature title="Filtro de Escopo" tone="accent" icon="filter" badge="Ambos · Cond. · Acordos">
                        <p>
                            O seletor "Ambos / Condenação / Acordos" no topo da página controla quais dos dois lados
                            entram na soma de cada indicador e gráfico. Quando um dos lados é excluído, a página se
                            comporta como se aquele dashboard de origem não existisse — inclusive a seção Confecção CS,
                            que só existe no lado Condenação, some quando o escopo é restrito a "Acordos".
                        </p>
                    </DocFeature>
                    <DocFeature
                        title={'"Confecção CS" depende do escopo'}
                        tone="warn"
                        icon="alert"
                        badge="Só lado Condenação"
                        framed
                    >
                        <p>
                            A Seção 03 (gargalos do Cumprimento de Sentença) aparece nas três unidades sempre que a
                            Condenação está no escopo ("Ambos" ou "Condenação"). Com o escopo em "Acordos", ela some e a
                            seção Alvarás expedidos passa a ser a 03.
                        </p>
                    </DocFeature>
                    <DocFeature title="Quando usar este dashboard" tone="info" icon="layers" badge="Visão executiva">
                        <p>
                            Use o Execução Estratégico para uma visão executiva única do setor de Execução como um todo.
                            Para o detalhe fino de cada domínio (TRE, classificação Judicial x Extrajudicial, alerta de
                            valor de alçada final vazio, etc.), use os dashboards de origem — Execução Estratégico e
                            Execução Acordos Estratégico (documentações separadas).
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="indicadores"
                title="01 — Indicadores"
                subtitle="Soma dos indicadores de volume, entrada, saída e valor dos dois dashboards de origem"
                badge="Condenação + Acordos"
            >
                <DocCallout icon="calendar" title="Qual data cada card usa?">
                    <p>
                        Cada card soma o valor equivalente de Condenação e de Acordos (respeitando o filtro de Escopo).
                        Só três refletem o estoque atual e não mudam com o filtro de datas: "Total em Execução", "Valor
                        Total em execução" e "Valor Remanescente". Os demais (entradas, saídas, valores, tempos,
                        incontroverso, estoque inicial) respeitam o período selecionado no calendário. "Valor
                        Remanescente" e "Valor Incontroverso" só existem no lado Condenação — Acordos não tem o conceito
                        de pagamento parcial do alvará.
                    </p>
                </DocCallout>

                <DocCallout
                    tone="warn"
                    icon="alert"
                    title={'Pagamento parcial do alvará: o que acontece com "Valor Total em execução"?'}
                >
                    <p>
                        Às vezes o alvará de um processo é pago em duas partes: primeiro a parte{' '}
                        <strong>incontroversa</strong> (o que ninguém discute que é devido), depois o restante. Quando
                        isso acontece, o valor "em aberto" do processo deixa de ser o valor cheio e passa a ser só o que
                        ainda falta pagar — o <strong>remanescente</strong>.
                    </p>
                    <DocGrid>
                        <DocMini label="Exemplo">
                            Um processo de <Hl mono>R$ 100 mil</Hl> tem R$ 80 mil de incontroverso pago. Sobram{' '}
                            <Hl tone="ok" mono>
                                R$ 20 mil
                            </Hl>{' '}
                            de remanescente. A partir desse momento, o "Valor Total em execução" passa a contar só os{' '}
                            <strong>R$ 20 mil</strong> para esse processo — os R$ 80 mil saem do total e não voltam,
                            mesmo em períodos futuros.
                        </DocMini>
                        <DocMini label="Para onde vão os R$ 80 mil">
                            Eles não somem do dashboard: aparecem no card <strong>"Valor Incontroverso"</strong>, mas só
                            no período em que a compensação aconteceu — é um indicador de fluxo (o que caiu naquele
                            mês), diferente de "Valor Total em execução", que é sempre o estoque atual.
                        </DocMini>
                    </DocGrid>
                </DocCallout>

                <DocGrid>
                    <MetricCard
                        icon="target"
                        name="Total em Execução"
                        what="Quantidade total de processos em Execução (Condenação + Acordos)."
                        counts="Estoque atual dos dois dashboards de origem, histórico completo."
                        calc="Soma da quantidade total de processos na fase de Execução dos dois dashboards. Não muda com o filtro de datas."
                        interpret="Estoque de trabalho em aberto no setor de Execução como um todo."
                    />
                    <MetricCard
                        icon="dollar"
                        name="Valor Total em execução"
                        what="Soma do valor ainda em aberto de todos os processos em Execução (Condenação + Acordos). Traz também o 'Total Ticket médio' (Valor Total ÷ Total em Execução)."
                        counts="Estoque atual dos dois dashboards de origem, histórico completo."
                        calc="Condenação: valor ainda em aberto (já descontando o incontroverso já compensado — ver caixa acima). Acordos: valor de alçada final cheio."
                        interpret="Indica o valor represado no setor como um todo, independente do período selecionado."
                        caveat="Este é o card afetado pelo pagamento parcial do alvará: veja a explicação e o exemplo logo acima."
                    />
                    <MetricCard
                        icon="check"
                        name="Quantidade de entrada na Execução"
                        what="Processos que entraram na Execução no período selecionado (Condenação + Acordos)."
                        counts={
                            'Condenação: DATA_EXECUCAO no período. Acordos: processos com a etiqueta "Acordo" e DATA_EXECUCAO no período.'
                        }
                        calc="Soma da quantidade de entrada no período dos dois dashboards."
                        interpret="Mede o volume de trabalho que chegou na Execução no período, somando os dois domínios."
                    />
                    <MetricCard
                        icon="dollar"
                        name="Valor em Execução"
                        what="Valor de entrada dos processos no período (Condenação + Acordos). Traz também o 'Ticket Médio' (Valor em Execução ÷ Quantidade de entrada)."
                        counts={
                            'Condenação: VALOR_EXECUCAO dos processos com DATA_EXECUCAO no período. Acordos: VALOR_ALCADA_FINAL dos processos com a etiqueta "Acordo" e DATA_EXECUCAO no período.'
                        }
                        calc="Soma do valor de entrada no período dos dois dashboards."
                        interpret="Mede o valor financeiro que entrou na Execução no período."
                        caveat="Diferente de 'Valor Total em execução', aqui o valor da Condenação é sempre o cheio (VALOR_EXECUCAO), mesmo que já tenha havido pagamento parcial — não é descontado."
                    />
                    <MetricCard
                        icon="dollar"
                        name="Valor Remanescente"
                        what="Quanto ainda falta pagar nos processos que já tiveram pagamento parcial do alvará (só lado Condenação)."
                        counts="Processos atualmente em Execução Condenação com compensação parcial do incontroverso já registrada, histórico completo."
                        calc="Soma de VALOR_REMANESCENTE desses processos."
                        interpret="É a parcela do 'Valor Total em execução' que vem de processos com pagamento parcial — ajuda a enxergar separadamente o que ainda está represado por causa desse mecanismo."
                    />
                    <MetricCard
                        icon="check"
                        name="Quantidade de saída da Execução"
                        what="Processos com saída da Execução no período selecionado (Condenação + Acordos). Traz também 'Qtd. Incontroverso' (só lado Condenação)."
                        counts={
                            'Condenação: DATA_COMPENSACAO_ALVARA no período. Acordos: DATA_PAGAMENTO_ACORDO no período.'
                        }
                        calc="Soma da quantidade de saída no período dos dois dashboards."
                        interpret="Mede o volume financeiro/processual liquidado da Execução no período."
                        caveat={
                            'Qtd. Incontroverso: processos (só Condenação) com a parte incontroversa paga no período mas que ainda não tiveram o remanescente compensado — ainda aparecem no estoque, aguardando a saída de fato. Quando o remanescente cai, o processo passa a contar só na quantidade de cima, nunca nos dois ao mesmo tempo.'
                        }
                    />
                    <MetricCard
                        icon="dollar"
                        name="Valor saída Execução"
                        what="Valor de saída dos processos no período (Condenação + Acordos). Traz também o 'Valor TED' (soma do TED de Condenação e de Acordos)."
                        counts={
                            'Condenação: remanescente (ou valor cheio) dos processos com DATA_COMPENSACAO_ALVARA no período + incontroverso dos processos com DATA_COMPENSACAO_ALVARA_INCONTROVERSO no período. Acordos: VALOR_ALCADA_FINAL dos acordos pagos no período.'
                        }
                        calc="Soma do valor de saída no período dos dois dashboards."
                        interpret="Mede o valor financeiro efetivamente liquidado da Execução no período."
                        caveat="Condenação: o valor já inclui o incontroverso compensado no período (o card 'Valor Incontroverso' mostra essa parcela em separado — não some os dois). Se o processo já teve a parte incontroversa compensada, a compensação final soma só o remanescente, sem contar o incontroverso duas vezes."
                    />
                    <MetricCard
                        icon="dollar"
                        name="Valor Incontroverso"
                        what="Valor incontroverso pago no período, mesmo com o processo ainda ativo na fase Execução (só lado Condenação)."
                        counts="Processos com compensação parcial do incontroverso registrada dentro do período selecionado."
                        calc="Soma de VALOR_INCONTROVERSO desses processos."
                        interpret="É o que 'saiu' de Valor Total em execução no período por causa de pagamento parcial — ver caixa de explicação acima. Já está incluído no 'Valor saída Execução'."
                    />
                    <MetricCard
                        icon="target"
                        name="Estoque Inicial do período anterior"
                        what="Estoque de processos em Execução estimado no início do período selecionado (Condenação + Acordos)."
                        counts="Soma do estoque inicial calculado em cada dashboard de origem."
                        calc="Estoque inicial de cada lado = Total atual − Entradas no período + Saídas no período; os dois resultados são somados."
                        interpret="Permite comparar o tamanho da fila de Execução (como um todo) antes e depois do período."
                    />
                    <MetricCard
                        icon="clock"
                        name="Média de Tempo · Mediana de Tempo"
                        what="Tempo entre entrada e saída da Execução, em média e em mediana (dois cards separados)."
                        counts="Processos que saíram no período: Condenação pela compensação do alvará, Acordos pelo pagamento do acordo."
                        calc="As durações de Condenação e de Acordos são juntadas numa lista só, e a média e a mediana são calculadas sobre essa lista (não é a soma nem a média das médias de cada lado)."
                        interpret="Quanto menor, mais rápido os processos estão sendo resolvidos."
                    />
                </DocGrid>
                <DocGrid cols={2}>
                    <DocFeature title="Taxa de atualização de valores" tone="info" icon="percent" badge="Só Condenação">
                        <p>
                            Três cards abaixo dos indicadores: a taxa total (1G + 2G) e as taxas{' '}
                            <strong>1G — sentença</strong> e <strong>2G — acórdão</strong>. Mostram quanto o valor
                            cresceu da decisão (sentença ou acórdão) até a Execução, nas entradas da Condenação no
                            período, com a quantidade de processos e o aumento em R$. Clique em qualquer um para abrir
                            os detalhes.
                        </p>
                    </DocFeature>
                    <DocFeature title="Comparativo com o período anterior" tone="neutral" icon="history">
                        <p>
                            Os cards de período (entradas, saídas, valores, tempos e a taxa total) trazem uma etiqueta
                            com a variação ("vs mês anterior") em relação ao período anterior equivalente.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="tendencia"
                title="02 — Entradas e saídas na Execução por mês"
                subtitle="Gráficos de tendência combinados, com seletores de modo próprios"
                badge="Histórico completo"
            >
                <p>
                    Estes gráficos usam o histórico completo (não dependem do filtro de datas do calendário, exceto onde
                    indicado) e somam Condenação + Acordos mês a mês, matéria a matéria, subfase a subfase ou comarca a
                    comarca, conforme o caso.
                </p>
                <DocGrid cols={2}>
                    <DocFeature title="Entradas e Saídas na Execução por Mês" tone="accent" badge="Seletor de ano">
                        <p>
                            Duas linhas (Quantidade Entrada e Quantidade Saída) por mês, somando os dois dashboards de
                            origem. Use o seletor de ano para trocar o ano exibido — o mesmo ano vale para "Entradas por
                            fluxo" e "Valor de entrada e saída por mês".
                        </p>
                    </DocFeature>
                    <DocFeature title="Demonstrativo de Matérias" tone="ok" badge="Pizza · Clicável">
                        <p>
                            Gráfico de pizza por matéria (soma dos dois lados), com um seletor de modo:{' '}
                            <strong>Total</strong> (estoque atual), <strong>Qtd Entrada</strong> ou{' '}
                            <strong>Valor Entrada</strong>. Clique em uma fatia para filtrar o restante da página por
                            aquela matéria.
                        </p>
                    </DocFeature>
                    <DocFeature title="Entradas por fluxo" tone="warn" badge="1G · 2G · Outros · Acordos">
                        <p>
                            Linhas por mês do ano escolhido: <strong>1G</strong> e <strong>2G</strong> (entradas da
                            Condenação vindas da Confecção CS — Elaborar CS ou Manifestação Cálculo),{' '}
                            <strong>CS (sem grau)</strong> quando houver, <strong>Outros</strong> (entradas por outro
                            caminho) e <strong>Acordos</strong> (acordos com entrada no mês). As linhas seguem o escopo.
                        </p>
                    </DocFeature>
                    <DocFeature title="Valor de Entrada na Execução por Mês" tone="info" badge="Ano a ano">
                        <p>
                            Uma linha por ano, somando o valor de entrada (VALOR_EXECUCAO na Condenação,
                            VALOR_ALCADA_FINAL nos Acordos) de cada mês — todos os anos disponíveis lado a lado, para
                            comparação sazonal.
                        </p>
                    </DocFeature>
                    <DocFeature title="Valor por Subfase" tone="violet" badge="Barras · Clicável">
                        <p>
                            Barras horizontais roláveis com o valor por subfase (soma dos dois lados), com seletor{' '}
                            <strong>Total</strong> ou <strong>Entrada</strong>. Clique em uma barra para filtrar o
                            restante da página por aquela subfase.
                        </p>
                    </DocFeature>
                    <DocFeature title="Ano de Ajuizamento (Entradas / Total)" tone="accent" badge="Pizza · Clicável">
                        <p>
                            Dois gráficos de pizza lado a lado — um para os processos que entraram no período, outro
                            para o total atual — agrupando por ano de ajuizamento (DATA_DISTRIBUICAO), com quantidade e
                            valor somados por ano. Clique em uma fatia para filtrar por aquele ano de ajuizamento.
                        </p>
                    </DocFeature>
                    <DocFeature title="Valor de Entrada e Saída na Execução por Mês" tone="info" badge="Duas linhas">
                        <p>
                            Duas linhas no mesmo gráfico (Valor de Entrada e Valor de Saída), somando os dois dashboards
                            de origem. Usa o mesmo ano selecionado no gráfico de Entradas e Saídas acima.
                        </p>
                    </DocFeature>
                    <DocFeature title="Tempo Médio em Dias — Execução por Mês" tone="neutral" badge="Ano a ano">
                        <p>
                            Uma linha por ano com o tempo médio (em dias) entre entrada e saída da Execução, somando o
                            tempo médio de Condenação e de Acordos mês a mês (com os dois lados no escopo, é a soma, não
                            a média — como na v1; o subtítulo do gráfico avisa).
                        </p>
                    </DocFeature>
                    <DocFeature title="Ticket Médio Entrada — Execução por Mês" tone="ok" badge="Ano a ano">
                        <p>
                            Uma linha por ano com o valor de entrada ÷ a quantidade de entradas de cada mês (Condenação
                            e Acordos somados antes de dividir).
                        </p>
                    </DocFeature>
                    <DocFeature title="Condenação x Acordos" tone="violet" badge="Pizza · Clicável">
                        <p>
                            Pizza com a divisão entre os dois lados, com seletor <strong>Total</strong>,{' '}
                            <strong>Entradas</strong> ou <strong>Saídas</strong>. Clique numa fatia para mudar o Escopo
                            da página para aquele lado.
                        </p>
                    </DocFeature>
                </DocGrid>
                <DocFeature title="Processos por Comarca" tone="ok" icon="pin" badge="Ranking · Multi-seleção" framed>
                    <p>
                        Tabela paginada de comarcas (soma dos dois lados), com seletor <strong>Total</strong>,{' '}
                        <strong>Entradas</strong> ou <strong>Saídas</strong> — esse seletor só afeta a quantidade e o
                        valor de cada linha. Além da quantidade e do percentual, cada linha traz o valor de execução
                        somado (Condenação: VALOR_EXECUCAO; Acordos: VALOR_ALCADA_FINAL) e o tempo médio entre entrada e
                        saída da Execução naquela comarca — este último é <strong>fixo</strong>, calculado sempre sobre
                        o histórico completo da comarca (não muda com o seletor Total/Entradas/Saídas), pra servir de
                        referência estável de quanto tempo um processo daquela comarca costuma levar pra sair da
                        Execução. Quando as duas datas relevantes não estão preenchidas para nenhum processo da comarca,
                        o tempo médio aparece como "—".
                    </p>
                    <p>
                        Clique em uma comarca para adicioná-la (ou removê-la) do filtro de Comarca da página — o mesmo
                        filtro do dropdown "Comarca" na barra de filtros. Pode selecionar mais de uma comarca ao mesmo
                        tempo; as linhas das demais comarcas ficam esmaecidas.
                    </p>
                </DocFeature>
            </DocSection>

            <DocSection
                id="confeccao-cs"
                title="03 — Confecção CS"
                subtitle={
                    'Gargalos de Elaborar Cumprimento de Sentença e Manifestação Cálculo 1 e 2 — só no lado Condenação'
                }
                tone="warn"
                badge="Só lado Condenação"
            >
                <DocCallout tone="warn" icon="flow" title="Só existe no lado Condenação">
                    <p>
                        Esta seção só existe no dashboard Execução Condenação — não há equivalente em Execução Acordos.
                        Por isso ela desaparece da página quando o filtro de Escopo está restrito a "Acordos". Ela olha
                        os agendamentos das atividades que formalizam o pedido de cumprimento de sentença e dão início à
                        Execução.
                    </p>
                </DocCallout>
                <DocGrid cols={2}>
                    <DocFeature title="Atividades por unidade" tone="info" icon="building" badge="NG · LA · LARJ">
                        <p>
                            NG: "Elaborar Cumprimento de Sentença (1G)", "Elaborar Cumprimento de Sentença (2G)",
                            "Manifestação Cálculo 1" e "Manifestação Cálculo 2". LA e LARJ: as mesmas quatro mais a
                            atividade antiga, sem grau ("Elaborar Cumprimento de Sentença"), que ainda recebe tarefas. O
                            resto do painel funciona da mesma forma nas três unidades.
                        </p>
                    </DocFeature>
                    <DocFeature title="Sem alternância de visão" tone="accent" icon="calendar" badge="Período">
                        <p>
                            Diferente da seção Atividades dos dashboards de Execução, aqui não há botão Concluídas / Por
                            prazo: o total e as concluídas usam o período do calendário, e "Em andamento" é sempre o
                            acumulado sem período.
                        </p>
                    </DocFeature>
                </DocGrid>

                <DocGrid>
                    <MetricCard
                        icon="check"
                        name="Total de atividades / Em andamento / Concluídas"
                        what="Os três cards da seção, restritos às atividades da Confecção CS."
                        counts="Total: tarefas criadas no período, mesmo as já concluídas (canceladas não entram). Em andamento: tarefas em aberto, acumulado sem período. Concluídas: tarefas encerradas no período."
                        calc="Contagem direta, com os filtros de atividade, funcionário e situação da seção."
                        interpret="Um número alto de 'Em andamento' é um forte indício de gargalo represando a entrada de novos processos na Execução. Clique em 'Em andamento' ou 'Concluídas' para ver a lista de tarefas."
                    />
                    <MetricCard
                        icon="barChart"
                        name="Por atividade"
                        what="Tarefas por atividade da Confecção CS, em barras empilhadas: Concluídos e Em aberto."
                        counts="As mesmas tarefas dos cards."
                        calc="Contagem por atividade."
                        interpret="Clique numa atividade para ver só ela na seção."
                    />
                    <MetricCard
                        icon="users"
                        name="Demandas por Funcionário (Cumpridas)"
                        what="Volume de encerramentos com sucesso da Confecção CS, por funcionário responsável pelo encerramento, com a taxa de conclusão de cada um ao lado do nome."
                        counts={'Agendamentos "Encerrado Cumprido" das atividades da seção, no período.'}
                        calc="Contagem por funcionário, considerando apenas status Encerrado Cumprido — os Não Cumpridos ficam fora deste gráfico (ver 'Motivo do Não Cumprimento')."
                        interpret="Clique no nome de um funcionário para filtrar a seção; mostra quem está dando vazão ao gargalo com sucesso."
                    />
                    <MetricCard
                        icon="alert"
                        name="Motivo do Não Cumprimento"
                        what="Agrupa, pelo motivo registrado no encaminhamento do LEXFLOW, os agendamentos da(s) atividade(s) encerrados como Não Cumprido."
                        counts="Agendamentos 'Encerrado Não Cumprido' com motivo registrado — histórico completo, independente do período selecionado."
                        calc="Contagem por motivo (campo motivo_encaminhamento do agendamento), do mais para o menos frequente."
                        interpret="Aponta a causa mais comum de não cumprimento (ex.: falta de documentação do cliente, sem tratativa, pagamento voluntário já feito)."
                        caveat="Este gráfico só aparece se houver ao menos um motivo registrado. Se ele sumir junto com os KPIs e 'Demandas por Funcionário' todos zerados, o problema é ausência de dados das atividades no recorte — não um defeito deste gráfico específico."
                    />
                </DocGrid>
            </DocSection>

            <DocSection
                id="alvaras"
                title="04 — Alvarás expedidos"
                subtitle="Processos com alvará já expedido aguardando compensação em conta, conforme o escopo"
                badge="03 com escopo Acordos"
            >
                <DocGrid cols={2}>
                    <DocFeature title="Alvarás expedidos por mês" tone="accent" icon="barChart" badge="Clique no mês">
                        <p>
                            Colunas por mês do ano escolhido, com seletores de <strong>Origem</strong> (Todos /
                            Condenação / Acordos, conforme o escopo) e <strong>Métrica</strong> (Quantidade ou Valor).
                            Clique num mês para ver os dias; o botão "Meses" volta.
                        </p>
                    </DocFeature>
                    <DocFeature title="Lista de alvarás" tone="info" icon="list" badge="20 por página">
                        <p>
                            Os alvarás expedidos com a previsão de compensação (expedição + 5 dias úteis) e quantos dias
                            úteis faltam até ela. Ordene clicando no cabeçalho (expedição, previsão, prazo ou valor).
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="filtros"
                title="Filtros disponíveis"
                icon="filter"
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

            <DocSection
                id="relatorio"
                title="Relatório Personalizado"
                icon="download"
                subtitle="Exportação em CSV/XLSX, em três etapas"
                badge="CSV · XLSX"
            >
                <DocCallout icon="download" title="Um diálogo em etapas">
                    <p>
                        O botão "Relatório Personalizado" (canto superior direito) abre um diálogo em etapas: primeiro
                        pergunta a <strong>origem</strong> do relatório, depois (dependendo da resposta) o{' '}
                        <strong>escopo</strong>, e por fim deixa escolher o <strong>recorte</strong> e os{' '}
                        <strong>campos</strong>. Um botão "Voltar" permite corrigir uma etapa anterior sem fechar o
                        diálogo.
                    </p>
                </DocCallout>

                <DocGrid cols={2}>
                    <DocFeature title="Origem: Filtros ativos na Página" tone="accent" badge="Etapa 1">
                        <p>
                            Pula direto para a escolha de recorte e campos, usando o escopo que já está ativo na página
                            (Ambos/Condenação/Acordos). O arquivo sai automaticamente filtrado pelo período do
                            calendário e pelos filtros de UF, Comarca, Matéria, Subfase e Ano de Ajuizamento ativos na
                            página. Por exemplo, se a página estiver filtrada por Comarca "Beruri" e você exportar o
                            recorte "Saída", o arquivo trará só as saídas daquela comarca, não o total geral.
                        </p>
                    </DocFeature>
                    <DocFeature title="Origem: Relatório personalizado" tone="info" badge="Etapa 1">
                        <p>
                            Monta um relatório do zero, independente do que está filtrado na página — pergunta em
                            seguida o escopo: <strong>Condenação</strong>, <strong>Acordos</strong> ou{' '}
                            <strong>Os dois juntos</strong>.
                        </p>
                    </DocFeature>
                    <DocFeature title="Recorte (Entrada / Saída / Total)" tone="ok" badge="Etapa 3">
                        <p>
                            Escolhe quais processos entram no arquivo: os que entraram no período, os que saíram no
                            período, ou o estoque total atual — mesmo critério usado pelos KPIs da página. Aparece em
                            todas as combinações de origem/escopo.
                        </p>
                    </DocFeature>
                    <DocFeature title="Campos" tone="neutral" badge="Etapa 3">
                        <p>
                            Lista de colunas selecionáveis por grupo (Identificação, Datas, Valores) — inclui UF,
                            Comarca, Vara e Competência em "Identificação". "Selecionar todos" / "Desmarcar todos"
                            agilizam a escolha.
                        </p>
                    </DocFeature>
                </DocGrid>
                <DocCallout tone="ok" icon="sheet" title={'"Os dois juntos" sai num arquivo só'}>
                    <p>
                        Condenação e Acordos são consultas diferentes e não podem virar uma tabela só, mas viram um{' '}
                        <strong>arquivo</strong> só. Quando o escopo envolve os dois — seja porque a página estava com
                        Escopo "Ambos" e você escolheu "Filtros ativos na Página", seja porque você escolheu "Os dois
                        juntos" no relatório personalizado — a tela final mostra os campos de Condenação e de Acordos em
                        blocos separados (cada um com seu próprio "Selecionar todos"/"Desmarcar todos"), e um único
                        clique em Exportar baixa:
                    </p>
                    <DocGrid>
                        <DocMini label="XLSX">
                            Um arquivo com uma aba <Hl tone="ok">"Execução Condenação"</Hl> e outra{' '}
                            <Hl tone="ok">"Execução Acordos"</Hl>.
                        </DocMini>
                        <DocMini label="CSV">
                            Um <Hl mono>.zip</Hl> com um CSV de cada (CSV não tem o conceito de aba).
                        </DocMini>
                    </DocGrid>
                    <p>
                        Se você desmarcar todos os campos de um dos dois lados, aquela origem simplesmente não entra no
                        arquivo.
                    </p>
                </DocCallout>
            </DocSection>
        </DocPage>
    )
}
