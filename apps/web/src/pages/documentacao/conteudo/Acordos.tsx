import {
    DocCallout,
    DocChips,
    DocFeature,
    DocGrid,
    DocMini,
    DocPage,
    DocSection,
    Hl,
    MetricCard,
    type TocItem,
} from '../components/DocParts.tsx'

// Guia de Execução Acordos. Texto da v1: LexHub/src/pages/documentacao/ExecucaoAcordos.tsx.

const TOC: TocItem[] = [
    { id: 'como-funciona', label: 'Como funciona' },
    { id: 'fechamento', label: 'Fechamento de Acordo' },
    { id: 'indicadores', label: 'Indicadores' },
    { id: 'subfases', label: 'Matérias, subfases e comarcas' },
    { id: 'tendencia', label: 'Entradas e saídas por mês' },
    { id: 'evolucao', label: 'Evolução de valores' },
    { id: 'atividades', label: 'Atividades' },
    { id: 'diligencias', label: 'Diligências' },
    { id: 'lista', label: 'Execuções de Acordo (lista)' },
    { id: 'exportar', label: 'Exportar relatório' },
    { id: 'filtros', label: 'Filtros' },
]

export function AcordosDoc() {
    return (
        <DocPage
            title="Execução Acordos"
            tags={['NG', 'LA', 'LARJ']}
            note="Mesma lógica nas três unidades"
            toc={TOC}
            intro={
                <>
                    Este guia explica o dashboard de Execução Acordos: o recorte de processos resolvidos por acordo (em
                    vez de condenação/sentença), desde a negociação até o pagamento, com datas, valores e classificações
                    próprias. <strong>Nenhum conhecimento técnico é necessário.</strong>
                </>
            }
            header={
                <DocCallout caps title="Quem entra no universo de Acordos" badge='Etiqueta "Acordo"'>
                    <p>
                        Um processo entra no universo de Execução de Acordos quando tem a etiqueta{' '}
                        <strong>"Acordo"</strong> aplicada no LEXFLOW <strong>ou</strong> o campo{' '}
                        <strong>acordo fechado</strong> preenchido — o que vier primeiro. A partir daí, cada indicador
                        usa uma data diferente da tabela do processo, conforme a pergunta que responde. Datas e valor
                        próprios — não são os mesmos da Execução padrão:
                    </p>
                    <DocGrid cols={3}>
                        <DocMini label="Entrada">
                            <Hl mono>DATA DE EXECUÇÃO</Hl> — data em que o processo entrou de fato na fase de execução
                            no LEXFLOW. Só conta quem tem a etiqueta "Acordo" aplicada (Seção 01).
                        </DocMini>
                        <DocMini label="Saída">
                            <Hl tone="ok" mono>
                                DATA DE PAGAMENTO DO ACORDO
                            </Hl>{' '}
                            — data em que o acordo foi efetivamente pago.
                        </DocMini>
                        <DocMini label="Valor">
                            <Hl tone="info" mono>
                                VALOR DE ALÇADA FINAL
                            </Hl>{' '}
                            — valor final do acordo, usado em todos os indicadores e gráficos de valor deste dashboard.
                        </DocMini>
                    </DocGrid>
                </DocCallout>
            }
        >
            <DocSection
                id="como-funciona"
                title="01 — Como o dashboard funciona"
                subtitle="Um recorte de acordos que não depende da fase atual do processo"
            >
                <DocGrid cols={2}>
                    <DocFeature
                        title='Por que a "entrada" usa só a etiqueta, e não a fase'
                        tone="accent"
                        icon="flow"
                        badge="Entrada"
                        framed
                    >
                        <p>
                            As "Entradas de Acordos" (quantidade e valor) contam processos com a etiqueta "Acordo"
                            aplicada cuja data de execução caiu no período — sem exigir nenhuma fase específica (nem
                            "ACORDO", nem qualquer outra) e sem depender do campo <strong>acordo fechado</strong> estar
                            preenchido. Esse campo, na prática, nem sempre é preenchido no LEXFLOW mesmo quando o
                            processo já tem data de execução, valor e situação definidos — o que subcontava entradas
                            reais. Como a fase do processo muda com o tempo (ex.: acordo pago e arquivado), exigir uma
                            fase fixa faria o dashboard "perder" o processo depois que ele avança no fluxo. A etiqueta é
                            o único marcador estável usado para a entrada.
                        </p>
                    </DocFeature>
                    <DocFeature
                        title='O "estoque atual" já usa fase — só não é a mesma coisa que entrada'
                        tone="info"
                        icon="layers"
                        badge="Estoque atual"
                        framed
                    >
                        <p>
                            "Total em Execução de Acordos", "Valor Total", os rankings por matéria/subfase, o TRE e as
                            classificações Pré × Pós-Sentença e Judicial × Extrajudicial olham para o estoque{' '}
                            <strong>atual</strong>: processos com etiqueta "Acordo" OU acordo fechado preenchido que
                            estão, hoje, na fase "ACORDO" do LEXFLOW. Diferente da entrada, esses indicadores não usam
                            apenas a etiqueta — mas também não usam a data de execução, e sim a fase atual do processo.
                        </p>
                    </DocFeature>
                </DocGrid>
                <DocCallout tone="ok" icon="check-circle" title="Cada processo conta uma única vez">
                    <p>
                        Todos os cálculos deduplicam por <Hl mono>NUMERO_PROCESSO</Hl> (o identificador único do
                        processo), garantindo que ele seja contado (e seu valor somado) apenas uma vez.
                    </p>
                </DocCallout>
            </DocSection>

            <DocSection
                id="fechamento"
                title="02 — Fechamento de Acordo"
                subtitle="Processos ainda em negociação, antes de entrarem na Execução de Acordos"
                badge="Estoque atual"
            >
                <p>
                    Esta seção olha para uma etapa <strong>anterior</strong> à Execução de Acordos: processos cuja
                    SUBFASE atual indica que o acordo está sendo negociado ou já foi fechado/cancelado, mas que ainda
                    não necessariamente entraram no recorte de "Execução de Acordos" descrito acima.
                </p>
                <DocChips
                    label="Subfases consideradas:"
                    items={[
                        { label: 'ACORDO EM NEGOCIAÇÃO', tone: 'info' },
                        { label: 'AG. PROTOCOLO DA MINUTA DE ACORDO', tone: 'info' },
                        { label: 'MINUTA DE ACORDO PROTOCOLADA', tone: 'info' },
                        { label: 'ACORDO FECHADO', tone: 'ok' },
                        { label: 'ACORDO CANCELADO', tone: 'danger' },
                    ]}
                />
                <DocGrid cols={2}>
                    <DocFeature title="Valor Alçada Final por Subfase de Fechamento" tone="ok" badge="Soma de valor">
                        <p>
                            Soma o VALOR_ALCADA_FINAL dos processos atualmente em uma dessas 5 subfases, agrupado pela
                            subfase em que se encontram (situação de agora, independente do período selecionado no
                            calendário).
                        </p>
                    </DocFeature>
                    <DocFeature title="Processos por Subfase de Fechamento" tone="info" badge="Contagem">
                        <p>
                            Conta os processos atualmente em uma dessas 5 subfases, agrupado pela subfase em que se
                            encontram (estoque atual).
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="indicadores"
                title="03 — Indicadores"
                subtitle="9 cards de volume, tempo e valor — dois olham o estoque atual, os demais olham o período"
                badge="Estoque × período"
            >
                <DocGrid>
                    <MetricCard
                        name="Total em Execução de Acordos"
                        icon="scale"
                        what="Quantidade de processos de acordo atualmente na fase 'ACORDO' do LEXFLOW."
                        counts='Processos com etiqueta "Acordo" OU acordo fechado preenchido, que estão hoje na fase ACORDO.'
                        calc="Contagem direta, deduplicada por NUMERO_PROCESSO. Não é afetado pelo filtro de datas — mostra sempre o total atual."
                        interpret="Representa o estoque de acordos em aberto no setor."
                        caveat="Não muda com o filtro de período — junto com 'Valor Total em Execução de Acordos', é sempre o total atual."
                    />
                    <MetricCard
                        name="Entradas de Acordos"
                        icon="check"
                        what="Acordos que entraram na execução no período selecionado no calendário."
                        counts='Processos com etiqueta "Acordo" cuja DATA DE EXECUÇÃO está dentro do período selecionado — não depende da fase atual nem de acordo fechado estar preenchido.'
                        calc="Contagem direta dos processos que atendem a esse critério no período."
                        interpret="Mede o volume de acordos que entraram no fluxo de execução no período — é o indicador de 'entrada'."
                    />
                    <MetricCard
                        name="Acordos Pagos no Período"
                        icon="check-circle"
                        what="Acordos pagos no período selecionado no calendário."
                        counts="Processos (etiqueta 'Acordo' OU acordo fechado preenchido) com DATA DE PAGAMENTO DO ACORDO dentro do período selecionado."
                        calc="Contagem direta dos processos pagos no período."
                        interpret="Mede o volume de acordos efetivamente liquidados no período — é o indicador de 'saída'."
                    />
                    <MetricCard
                        name="Média de Tempo"
                        icon="clock"
                        what="Tempo médio (em dias) entre a DATA DE EXECUÇÃO e o pagamento do acordo."
                        counts="Acordos com DATA DE PAGAMENTO DO ACORDO dentro do período selecionado, com DATA DE EXECUÇÃO preenchida e duração positiva — independente da fase atual."
                        calc="Média = soma das durações ÷ quantidade. Duração de cada processo = DATA DE PAGAMENTO DO ACORDO − DATA DE EXECUÇÃO."
                        interpret="Compare com a Mediana: se a Média estiver muito mais alta, um ou poucos acordos com pagamento muito demorado estão distorcendo a média — a Mediana costuma ser a referência mais confiável do tempo 'típico'."
                        caveat="Amostrada pela saída: só entram os acordos pagos no período (o mesmo conjunto de 'Acordos Pagos no Período')."
                    />
                    <MetricCard
                        name="Estoque Inicial do período anterior"
                        icon="history"
                        what="Estoque de acordos em Execução estimado no início do período selecionado."
                        counts="Baseado no total atual e nas entradas/saídas do período (histórico completo para entradas/saídas)."
                        calc="Estoque Inicial = Total atual em Execução de Acordos − Entradas no período + Acordos Pagos no período."
                        interpret="Permite comparar o tamanho da fila de acordos em execução antes e depois do período selecionado."
                    />
                    <MetricCard
                        name="Valor Total em Execução de Acordos"
                        icon="dollar"
                        what="Soma do valor de alçada final de todos os acordos atualmente na fase ACORDO."
                        counts='Mesmo recorte de "Total em Execução de Acordos", somando o valor em vez de contar.'
                        calc="Soma direta do VALOR_ALCADA_FINAL, deduplicada por NUMERO_PROCESSO. Não é afetado pelo filtro de datas."
                        interpret="Indica o valor de acordos represado no setor."
                    />
                    <MetricCard
                        name="Valor de Entradas de Acordos"
                        icon="dollar"
                        what="Valor de alçada final dos acordos que entraram na execução no período selecionado."
                        counts='Mesmo conjunto de processos de "Entradas de Acordos", somando o valor em vez de contar.'
                        calc="Soma do VALOR_ALCADA_FINAL dos processos com entrada no período."
                        interpret="Mede o valor dos acordos que entraram no fluxo no período."
                    />
                    <MetricCard
                        name="Valor de Acordos Pagos"
                        icon="dollar"
                        what="Valor de alçada final dos acordos pagos no período selecionado."
                        counts='Mesmo conjunto de processos de "Acordos Pagos no Período", somando o valor em vez de contar.'
                        calc="Soma do VALOR_ALCADA_FINAL dos processos pagos no período."
                        interpret="Mede o valor financeiro efetivamente liquidado no período."
                    />
                    <MetricCard
                        name="Mediana de Tempo"
                        icon="clock"
                        what="Metade dos acordos pagos no período levou até este tempo da execução ao pagamento."
                        counts="Mesmo recorte da Média de Tempo (acordos pagos no período)."
                        calc="Valor do meio da lista ordenada de durações (DATA DE EXECUÇÃO → pagamento)."
                        interpret="Referência do tempo 'típico', menos sensível a casos extremos que a média."
                    />
                </DocGrid>
                <DocCallout tone="warn" icon="alert" title="Aviso de campos vazios">
                    <p>
                        A faixa "Atenção" no topo da página ("Existem N processo(s) em acordo sem …") conta, no estoque
                        atual de acordos, quantos processos estão com um campo importante em branco (como o valor de
                        alçada final) — um aviso por campo. O botão da faixa baixa o relatório para preencher, uma aba
                        por campo.
                    </p>
                </DocCallout>
            </DocSection>

            <DocSection
                id="subfases"
                title="04 — Matérias, subfases e comarcas"
                subtitle="Estoque atual por subfase, matéria, comarca e classificações Pré/Pós-Sentença e Judicial/Extrajudicial"
                badge="Clicável"
            >
                <DocCallout icon="layers" title="Sempre o estoque atual">
                    <p>
                        Estes gráficos mostram o estoque atual (processos na fase ACORDO agora) — não são afetados pelo
                        filtro de datas do calendário (exceto a TRE e os modos Entradas/Saídas do mapa). Clique em uma
                        barra, fatia ou município para filtrar o restante da página por aquele valor.
                    </p>
                </DocCallout>
                <DocGrid cols={3}>
                    <DocFeature title="Valor Alçada Final por Subfase" tone="ok" badge="Barras">
                        <p>
                            Soma o VALOR_ALCADA_FINAL dos acordos em execução, agrupado pela SUBFASE atual. Barras
                            roláveis quando há muitas subfases.
                        </p>
                    </DocFeature>
                    <DocFeature title="Processos por Subfase" tone="info" badge="Barras">
                        <p>Conta os acordos em execução por SUBFASE atual, com percentual do total.</p>
                    </DocFeature>
                    <DocFeature title="Taxa de Redução Estoque (TRE)" tone="accent" badge="%">
                        <p>
                            <Hl mono>(Total em Execução de Acordos − Estoque Inicial) × 100 ÷ Estoque Inicial</Hl>, onde
                            o Estoque Inicial é o do card (total − entradas + saídas do período). Positivo indica que o
                            estoque de acordos aumentou no período; negativo, que diminuiu.
                        </p>
                    </DocFeature>
                    <DocFeature title="Pré x Pós-Sentença" tone="violet" badge="Pizza">
                        <p>
                            Classifica (gráfico de pizza) os acordos em execução entre <strong>Pré-Sentença</strong> e{' '}
                            <strong>Pós-Sentença</strong>, a partir das etiquetas correspondentes aplicadas ao processo
                            no LEXFLOW. Processos sem nenhuma das duas etiquetas aparecem como{' '}
                            <strong>Sem classificação</strong>. Clique numa fatia para filtrar a página.
                        </p>
                    </DocFeature>
                    <DocFeature title="Execução de Acordos por Matéria" tone="warn" badge="Pizza">
                        <p>
                            Distribuição (gráfico de pizza) dos acordos em execução por MATÉRIA. Clique numa fatia para
                            filtrar a página.
                        </p>
                    </DocFeature>
                    <DocFeature title="Judicial x Extrajudicial" tone="neutral" badge="Etiquetas">
                        <p>
                            Classifica os acordos entre <strong>Judicial</strong> e <strong>Extrajudicial</strong> a
                            partir das etiquetas correspondentes aplicadas ao processo no LEXFLOW. Processos sem nenhuma
                            das duas etiquetas aparecem como <strong>Sem classificação</strong>. Clique numa fatia para
                            filtrar a página.
                        </p>
                    </DocFeature>
                    <DocFeature title="Mapa de acordos por comarca" tone="info" badge="Total · Entradas · Saídas">
                        <p>
                            Mapa com três critérios: <strong>Total</strong> (em execução agora),{' '}
                            <strong>Entradas</strong> e <strong>Saídas</strong> (no período). Passe o cursor num
                            município para ver quantidade, valor e tempo médio; clique para filtrar a página pela
                            comarca.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="tendencia"
                title="05 — Entradas e saídas de Acordos por mês"
                subtitle="Dois gráficos de linha, lado a lado, com uma linha por ano — histórico completo"
                badge="Histórico completo"
            >
                <DocCallout icon="calendar" title="O que entrou/saiu historicamente">
                    <p>
                        Diferente dos cards de "Indicadores", estes gráficos contam TODOS os processos cuja data de
                        execução ou de pagamento caiu em cada mês, sem exigir que o processo ainda esteja em uma fase
                        específica hoje — é o recorte de "o que entrou/saiu historicamente".
                    </p>
                </DocCallout>
                <DocGrid cols={2}>
                    <DocFeature title="Entradas de Acordos por Mês" tone="accent" badge="DATA DE EXECUÇÃO">
                        <p>
                            Quantidade de processos com etiqueta "Acordo" cuja DATA DE EXECUÇÃO caiu em cada mês, com
                            uma linha por ano — os anos são comparados lado a lado no mesmo gráfico.
                        </p>
                    </DocFeature>
                    <DocFeature title="Saídas de Acordos por Mês" tone="ok" badge="DATA DE PAGAMENTO">
                        <p>
                            Quantidade de acordos pagos (DATA DE PAGAMENTO DO ACORDO) por mês, com uma linha por ano —
                            mesmo formato do gráfico de entradas, para facilitar a comparação lado a lado.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="evolucao"
                title="06 — Evolução de valores de acordos"
                subtitle="Valor de entrada (esquerda) e de saída (direita), mês a mês, comparado entre anos"
                badge="Linha por ano"
            >
                <DocCallout icon="trendingUp" title="Mesma lógica, somando valor">
                    <p>
                        Mesma lógica dos gráficos de quantidade da seção anterior, mas somando o valor de alçada final
                        em vez de contar processos. Em qualquer gráfico com uma linha por ano, o ano atual aparece
                        sempre em <Hl>laranja</Hl> — as demais cores são atribuídas automaticamente por ano.
                    </p>
                </DocCallout>
                <DocGrid cols={2}>
                    <DocFeature title="Valor de Entrada de Acordos por Mês" tone="accent" badge="Histórico completo">
                        <p>
                            Soma o VALOR_ALCADA_FINAL dos processos com etiqueta "Acordo" cuja DATA DE EXECUÇÃO caiu em
                            cada mês, agrupado por mês, com uma linha por ano — histórico completo.
                        </p>
                    </DocFeature>
                    <DocFeature title="Valor de Acordos Pagos Mês a Mês" tone="ok" badge="DATA DE PAGAMENTO">
                        <p>
                            Soma o VALOR_ALCADA_FINAL dos acordos pagos (DATA DE PAGAMENTO DO ACORDO), agrupado por mês,
                            com uma linha por ano. Sem dados no histórico, o gráfico mostra "Sem dados no histórico."
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="atividades"
                title="07 — Atividades"
                subtitle="Agendamentos do setor ACORDOS no LEXFLOW — produtividade, prazos e atrasos"
                tone="info"
                badge="Seção independente"
            >
                <p>
                    Esta seção é independente do restante do dashboard: em vez de olhar para os processos de acordo em
                    si, olha para as <strong>tarefas/agendamentos</strong> do setor <strong>ACORDOS</strong> no LEXFLOW
                    (ex.: "ACORDOS - ANÁLISE DE PROPOSTA", "ACORDOS - MONITORAR PROTOCOLO DA MINUTA"). Tem um botão{' '}
                    <strong>Concluídas / Por prazo</strong> que troca o eixo de tempo usado por toda a seção:
                </p>
                <DocGrid cols={2}>
                    <DocFeature title="Concluídas" tone="ok" icon="check-circle" badge="Criação / conclusão" framed>
                        <p>
                            Usa a data de criação/conclusão do agendamento. "Total" conta o que foi criado no período;
                            "Concluídas" conta o que foi encerrado no período.
                        </p>
                    </DocFeature>
                    <DocFeature title="Por prazo" tone="info" icon="calendar" badge="PRAZO" framed>
                        <p>
                            Usa o PRAZO do agendamento como eixo — útil para ver o que estava previsto para acontecer no
                            período, independente de quando foi criado.
                        </p>
                    </DocFeature>
                </DocGrid>

                <DocGrid>
                    <MetricCard
                        name="Total de atividades / Em andamento"
                        icon="fileText"
                        what="Volume de agendamentos do setor ACORDOS no período selecionado."
                        counts={
                            '"Total": agendamentos ativos criados (ou com prazo, na visão "Por prazo") no período. "Em andamento": os que estão com status Iniciado/Reaberto.'
                        }
                        calc="Contagem direta de agendamentos, aplicando os filtros de funcionário/atividade/status/situação ativos na seção."
                        interpret="Visão geral do volume de trabalho do setor no período."
                    />
                    <MetricCard
                        name="Vencidas / Vencem hoje"
                        icon="alert"
                        what="Agendamentos ativos cujo prazo já passou (Vencidas) ou é hoje (Vencem hoje)."
                        counts="Agendamentos ainda ativos (não encerrados/cancelados) com PRAZO anterior a hoje (Vencidas) ou igual a hoje (Vencem hoje). Na visão Concluídas, independe do período selecionado; na visão Por prazo, só contam as atividades com prazo dentro do período."
                        calc="Comparação direta do PRAZO contra a data de hoje."
                        interpret="Clicar no card 'Vencidas' abre um detalhamento por faixa de dias de atraso (1 dia, 2 dias... 6+ dias)."
                    />
                    <MetricCard
                        name="Concluídas"
                        icon="check"
                        what="Agendamentos encerrados (Cumprido ou Não Cumprido) no período."
                        counts="Agendamentos com status de encerramento cuja data de conclusão (ou prazo, na visão 'Por prazo') caiu no período."
                        calc="Contagem direta."
                        interpret="Mede a produtividade de encerramento de tarefas no período."
                    />
                </DocGrid>

                <DocGrid cols={3}>
                    <DocFeature title="Por atividade / Por funcionário" tone="accent" badge="Clicável">
                        <p>
                            Dois gráficos de distribuição: processos distintos por tipo de atividade do agendamento, e
                            volume de demandas por funcionário responsável (clicáveis para filtrar a lista de tarefas
                            abaixo).
                        </p>
                    </DocFeature>
                    <DocFeature
                        title="Produção Diária / Média Resolvidos por Funcionário"
                        tone="ok"
                        badge="Meta 20/dia"
                    >
                        <p>
                            Quantidade de atividades "Encerrado Cumprido" por mês (com detalhamento dia a dia ao clicar
                            em um mês) e a média diária de atividades cumpridas por funcionário, contra uma meta de
                            referência de 20/dia.
                        </p>
                    </DocFeature>
                    <DocFeature title="Lista de tarefas" tone="info" badge="Paginada">
                        <p>
                            Ao final da seção, uma tabela paginada com cada agendamento individual (nº do processo,
                            atividade, status, situação, responsável, prazo). Reflete os mesmos filtros de
                            funcionário/atividade/status/situação aplicados acima.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="diligencias"
                title="08 — Diligências"
                subtitle="Quantas vezes a diligência foi feita em cada processo, ranking por colaborador e alvarás"
            >
                <p>
                    Agendamentos de diligência do setor de Execução de Acordos criados no período do calendário. Mesma
                    estrutura da seção Diligências da Execução Condenação, com o valor de alçada final no lugar do valor
                    da execução.
                </p>
                <DocGrid cols={2}>
                    <DocFeature title="Processos com mais diligências" tone="accent" badge="Filtra a página">
                        <p>
                            Diligências por processo, criadas no período. Aqui, clicar num processo filtra a{' '}
                            <strong>página inteira</strong> por ele (filtro "Processo").
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
                            Soma o valor de alçada final dos processos com pelo menos uma expedição de alvará cumprida
                            no período, sem repetir o processo. Clique para ver a lista de processos.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="lista"
                title="09 — Execuções de Acordo (lista)"
                subtitle="Tabela paginada de processos, com três recortes à escolha"
                badge="Entradas / Saídas / Total"
            >
                <p>
                    Tabela com nº do processo, UF, data da execução, valor de alçada final e subfase — com um seletor{' '}
                    <strong>Entradas / Saídas / Total</strong> que troca o recorte de processos exibido, usando
                    exatamente os mesmos critérios dos cards da seção Indicadores:
                </p>
                <DocGrid cols={3}>
                    <DocFeature title="Entradas" tone="accent" icon="arrowRight" badge="No período" framed>
                        <p>
                            Mesmo critério do card "Entradas de Acordos": etiqueta "Acordo" + DATA DE EXECUÇÃO no
                            período selecionado.
                        </p>
                    </DocFeature>
                    <DocFeature title="Saídas" tone="ok" icon="check-circle" badge="No período" framed>
                        <p>
                            Mesmo critério do card "Acordos Pagos no Período": DATA DE PAGAMENTO DO ACORDO no período
                            selecionado.
                        </p>
                    </DocFeature>
                    <DocFeature title="Total" tone="info" icon="layers" badge="Estoque atual" framed>
                        <p>
                            Mesmo critério do card "Total em Execução de Acordos": estoque atual (fase ACORDO), sem
                            depender do período selecionado.
                        </p>
                    </DocFeature>
                </DocGrid>
                <DocCallout tone="neutral" icon="list" title="Total e paginação">
                    <p>
                        Acima da tabela aparecem a quantidade de processos e a soma do valor de alçada final do recorte.
                        10 processos por página. A lista respeita os filtros e o período da página.
                    </p>
                </DocCallout>
            </DocSection>

            <DocSection
                id="exportar"
                title="10 — Exportar relatório"
                subtitle="Botão 'Exportar' no topo da página — disponível para gestores e desenvolvedores"
                badge="CSV ou XLSX"
            >
                <p>
                    Abre um diálogo com dois tipos de relatório, cada um com seus próprios campos e recorte, exportáveis
                    em CSV ou XLSX.
                </p>
                <DocGrid cols={2}>
                    <DocFeature title="Processos" tone="accent" icon="sheet" badge="19 campos">
                        <p>
                            Mesmos dados da tabela "Execuções de Acordo" (Seção 09): escolha entre Entradas, Saídas ou
                            Total, e marque quais dos 19 campos disponíveis (identificação, datas e valores) incluir na
                            planilha. Respeita os filtros da página (UF, comarca, matéria, subfase, Pré × Pós-Sentença e
                            Judicial × Extrajudicial).
                        </p>
                    </DocFeature>
                    <DocFeature title="Atividades" tone="info" icon="fileText" badge="Concluídas / Por prazo">
                        <p>
                            Dados da seção Atividades (Seção 07): escolha entre a visão Concluídas ou Por prazo. Inclui
                            um número do processo (obtido cruzando o agendamento com os processos de acordo — nem sempre
                            disponível), atividade, status, situação, responsáveis, prazo e descrição. Respeita os
                            filtros de funcionário/atividade/status/situação ativos na seção Atividades.
                        </p>
                    </DocFeature>
                </DocGrid>
                <DocCallout tone="warn" icon="calendar" title="Qual período o relatório usa?">
                    <p>
                        Em ambos os casos, o período selecionado no calendário também é usado — exceto no recorte
                        "Total" do relatório de Processos, que (como o card "Total em Execução de Acordos") ignora o
                        período e sempre reflete o estoque atual.
                    </p>
                </DocCallout>
            </DocSection>

            <DocSection
                id="filtros"
                title="11 — Filtros disponíveis"
                subtitle="Como personalizar a visão do dashboard"
                tone="info"
            >
                <DocGrid cols={2}>
                    <DocFeature title="Período (calendário)" badge="Entradas / pagos" badgeTone="accent">
                        <p>
                            Afeta os cards de 'entradas/pagos no período' e seus valores, e a seção Atividades. Não
                            afeta os cards e gráficos marcados como 'histórico completo' ou 'estoque atual'.
                        </p>
                    </DocFeature>
                    <DocFeature
                        title="UF / Comarca / Matéria / Subfase / Pré × Pós-Sentença / Judicial × Extrajudicial"
                        badge="Clique ou janela"
                        badgeTone="ok"
                    >
                        <p>
                            Na janela Filtros do topo da página, ou clicando numa fatia, barra ou município da seção 04
                            (todos clicáveis, inclusive Pré × Pós-Sentença).
                        </p>
                    </DocFeature>
                    <DocFeature title="Combinação de filtros" badge="Lógica E" badgeTone="info">
                        <p>
                            Os filtros se combinam entre si (lógica E) — ex.: Matéria + Subfase juntos restringem a
                            página à interseção dos dois. UF, Comarca, Matéria e Subfase aceitam vários valores; Pré ×
                            Pós-Sentença e Judicial × Extrajudicial aceitam um só (clicar em outro substitui o
                            anterior).
                        </p>
                    </DocFeature>
                    <DocFeature title="Processo (Diligências)" badge="Seção 08" badgeTone="violet">
                        <p>
                            Clicar num processo do gráfico "Processos com mais diligências" filtra a página inteira por
                            ele. Um processo por vez.
                        </p>
                    </DocFeature>
                    <DocFeature
                        title="Funcionário / Atividade / Status / Situação (Atividades)"
                        badge="Seção 07"
                        badgeTone="neutral"
                        wide
                    >
                        <p>
                            Filtros próprios da seção Atividades (07) — clique nos cards de situação, ou nas barras dos
                            gráficos 'Por atividade'/'Por funcionário', para restringir a seção e a lista de tarefas.
                            Independentes dos filtros de gráfico do restante da página.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>
        </DocPage>
    )
}
