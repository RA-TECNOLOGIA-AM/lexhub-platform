import { DocCard, DocGrid, DocPage, DocSection, InfoBox, MetricCard, type TocItem } from '../components/DocParts.tsx'

// Guia de Execução Acordos. Texto da v1: LexHub/src/pages/documentacao/ExecucaoAcordos.tsx.

const TOC: TocItem[] = [
    { id: 'como-funciona', label: 'Como funciona' },
    { id: 'fechamento', label: 'Fechamento de Acordo' },
    { id: 'indicadores', label: 'Indicadores' },
    { id: 'subfases', label: 'Matérias e subfases' },
    { id: 'tendencia', label: 'Entradas e saídas por mês' },
    { id: 'evolucao', label: 'Evolução de valores' },
    { id: 'atividades', label: 'Atividades' },
    { id: 'lista', label: 'Execuções de Acordo (lista)' },
    { id: 'exportar', label: 'Exportar relatório' },
    { id: 'filtros', label: 'Filtros' },
]

const FILTERS = [
    {
        name: 'Período (calendário)',
        desc: "Afeta os cards de 'entradas/pagos no período' e seus valores, e a seção Atividades. Não afeta os cards e gráficos marcados como 'histórico completo' ou 'estoque atual'.",
    },
    {
        name: 'Matéria / Subfase / Judicial × Extrajudicial / Pré × Pós-Sentença',
        desc: "Clique em uma fatia ou barra dos gráficos da seção 'Matérias e subfases' para filtrar o restante da página por aquele valor (o gráfico Pré × Pós-Sentença é apenas informativo, não é clicável).",
    },
    {
        name: 'Combinação de filtros',
        desc: 'Os filtros de gráfico se combinam entre si (lógica E) — ex.: Matéria + Subfase juntos restringem a página à interseção dos dois. Dentro de cada dimensão, só um valor fica ativo por vez; clicar em outro valor da mesma dimensão substitui o anterior.',
    },
    {
        name: 'Limpar filtros (Indicadores)',
        desc: 'Clique em qualquer card da seção Indicadores para limpar de uma vez todos os filtros de gráfico ativos (Matéria, Subfase e Judicial × Extrajudicial).',
    },
    {
        name: 'Funcionário / Atividade / Status / Situação (Atividades)',
        desc: "Filtros próprios da seção Atividades (06) — clique nos cards de situação, ou nas barras dos gráficos 'Por atividade'/'Por funcionário', para restringir a seção e a lista de tarefas. Independentes dos filtros de gráfico do restante da página.",
    },
]

export function AcordosDoc() {
    return (
        <DocPage
            title="Execução Acordos"
            tags={['NG']}
            note="Ainda não existe versão LA"
            toc={TOC}
            intro={
                <>
                    Este guia explica o dashboard de Execução Acordos: o recorte de processos resolvidos por acordo (em
                    vez de condenação/sentença), desde a negociação até o pagamento, com datas, valores e classificações
                    próprias. Nenhum conhecimento técnico é necessário.
                </>
            }
        >
            <DocSection
                id="como-funciona"
                title="Como o dashboard funciona"
                subtitle="Um recorte de acordos que não depende da fase atual do processo"
                icon="fileText"
            >
                <InfoBox>
                    Um processo entra no universo de Execução de Acordos quando tem a etiqueta <strong>"Acordo"</strong>{' '}
                    aplicada no LEXFLOW <strong>ou</strong> o campo <strong>acordo fechado</strong> preenchido — o que
                    vier primeiro. A partir daí, cada indicador usa uma data diferente da tabela do processo, conforme a
                    pergunta que responde.
                </InfoBox>

                <DocCard title="Datas e valor próprios — não são os mesmos da Execução padrão">
                    <DocGrid>
                        <DocCard title="Entrada">
                            <p>
                                DATA DE EXECUÇÃO — data em que o processo entrou de fato na fase de execução no LEXFLOW.
                                Só conta quem tem a etiqueta "Acordo" aplicada (ver caixa abaixo).
                            </p>
                        </DocCard>
                        <DocCard title="Saída">
                            <p>DATA DE PAGAMENTO DO ACORDO — data em que o acordo foi efetivamente pago.</p>
                        </DocCard>
                        <DocCard title="Valor">
                            <p>
                                VALOR DE ALÇADA FINAL — valor final do acordo, usado em todos os indicadores e gráficos
                                de valor deste dashboard.
                            </p>
                        </DocCard>
                    </DocGrid>
                </DocCard>

                <DocCard title='Por que a "entrada" usa só a etiqueta, e não a fase'>
                    <p>
                        As "Entradas de Acordos" (quantidade e valor) contam processos com a etiqueta "Acordo" aplicada
                        cuja data de execução caiu no período — sem exigir nenhuma fase específica (nem "ACORDO", nem
                        qualquer outra) e sem depender do campo <strong>acordo fechado</strong> estar preenchido. Esse
                        campo, na prática, nem sempre é preenchido no LEXFLOW mesmo quando o processo já tem data de
                        execução, valor e situação definidos — o que subcontava entradas reais. Como a fase do processo
                        muda com o tempo (ex.: acordo pago e arquivado), exigir uma fase fixa faria o dashboard "perder"
                        o processo depois que ele avança no fluxo. A etiqueta é o único marcador estável usado para a
                        entrada.
                    </p>
                </DocCard>

                <DocCard title='O "estoque atual" já usa fase — só não é a mesma coisa que entrada'>
                    <p>
                        "Total em Execução de Acordos", "Valor Total", os rankings por matéria/subfase, o TRE e a
                        classificação Judicial × Extrajudicial olham para o estoque <strong>atual</strong>: processos
                        com etiqueta "Acordo" OU acordo fechado preenchido que estão, hoje, na fase "ACORDO" do LEXFLOW.
                        Diferente da entrada, esses indicadores não usam apenas a etiqueta — mas também não usam a data
                        de execução, e sim a fase atual do processo.
                    </p>
                </DocCard>

                <DocCard title="Cada processo conta uma única vez">
                    <p>
                        Todos os cálculos deduplicam por NUMERO_PROCESSO (o identificador único do processo), garantindo
                        que ele seja contado (e seu valor somado) apenas uma vez.
                    </p>
                </DocCard>
            </DocSection>

            <DocSection
                id="fechamento"
                title="01 — Fechamento de Acordo"
                subtitle="Processos ainda em negociação, antes de entrarem na Execução de Acordos"
                icon="users"
            >
                <InfoBox>
                    Esta seção olha para uma etapa <strong>anterior</strong> à Execução de Acordos: processos cuja
                    SUBFASE atual indica que o acordo está sendo negociado ou já foi fechado/cancelado, mas que ainda
                    não necessariamente entraram no recorte de "Execução de Acordos" descrito acima. As subfases
                    consideradas são: <strong>ACORDO EM NEGOCIAÇÃO</strong>,{' '}
                    <strong>AG. PROTOCOLO DA MINUTA DE ACORDO</strong>, <strong>MINUTA DE ACORDO PROTOCOLADA</strong>,{' '}
                    <strong>ACORDO FECHADO</strong> e <strong>ACORDO CANCELADO</strong>.
                </InfoBox>
                <DocGrid>
                    <DocCard title="Valor Alçada Final por Subfase de Fechamento">
                        <p>
                            Soma o VALOR_ALCADA_FINAL dos processos atualmente em uma dessas 5 subfases, agrupado pela
                            subfase em que se encontram (histórico completo, independente do período selecionado no
                            calendário).
                        </p>
                    </DocCard>
                    <DocCard title="Processos por Subfase de Fechamento">
                        <p>
                            Conta os processos atualmente em uma dessas 5 subfases, agrupado pela subfase em que se
                            encontram (histórico completo).
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>

            <DocSection
                id="indicadores"
                title="02 — Indicadores"
                subtitle="9 cards de volume, tempo e valor — a maioria olha o estoque atual, alguns olham só o período"
                icon="check"
            >
                <DocGrid>
                    <MetricCard
                        name="Total em Execução de Acordos"
                        icon="scale"
                        what="Quantidade de processos de acordo atualmente na fase 'ACORDO' do LEXFLOW."
                        counts='Processos NG com etiqueta "Acordo" OU acordo fechado preenchido, que estão hoje na fase ACORDO.'
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
                        icon="check"
                        what="Acordos pagos no período selecionado no calendário."
                        counts="Processos (etiqueta 'Acordo' OU acordo fechado preenchido) com DATA DE PAGAMENTO DO ACORDO dentro do período selecionado."
                        calc="Contagem direta dos processos pagos no período."
                        interpret="Mede o volume de acordos efetivamente liquidados no período — é o indicador de 'saída'."
                    />
                    <MetricCard
                        name="Média de Tempo / Mediana de Tempo"
                        icon="scale"
                        what="Tempo (em dias) entre a DATA DE EXECUÇÃO e o pagamento do acordo."
                        counts="Processos atualmente na fase ACORDO que têm as duas datas preenchidas e com duração positiva. Sempre histórico completo, independente do filtro de período."
                        calc="Média = soma das durações ÷ quantidade. Mediana = valor do meio da lista ordenada de durações. Duração de cada processo = DATA DE PAGAMENTO DO ACORDO − DATA DE EXECUÇÃO."
                        interpret="Compare os dois: se a Média estiver muito mais alta que a Mediana, um ou poucos acordos com pagamento muito demorado estão distorcendo a média — a Mediana costuma ser a referência mais confiável do tempo 'típico'."
                        caveat="Mesmo critério de data usado nas 'Entradas de Acordos' (DATA DE EXECUÇÃO) — mas aqui o recorte é o estoque atual (fase ACORDO), não o período selecionado."
                    />
                    <MetricCard
                        name="Estoque Inicial do período anterior"
                        icon="scale"
                        what="Estoque de acordos em Execução estimado no início do período selecionado."
                        counts="Baseado no total atual e nas entradas/saídas do período (histórico completo para entradas/saídas)."
                        calc="Estoque Inicial = Total atual em Execução de Acordos − Entradas no período + Acordos Pagos no período."
                        interpret="Permite comparar o tamanho da fila de acordos em execução antes e depois do período selecionado."
                    />
                    <MetricCard
                        name="Valor Total em Execução de Acordos"
                        icon="info"
                        what="Soma do valor de alçada final de todos os acordos atualmente na fase ACORDO."
                        counts='Mesmo recorte de "Total em Execução de Acordos", somando o valor em vez de contar.'
                        calc="Soma direta do VALOR_ALCADA_FINAL, deduplicada por NUMERO_PROCESSO. Não é afetado pelo filtro de datas."
                        interpret="Indica o valor de acordos represado no setor."
                    />
                    <MetricCard
                        name="Valor de Entradas de Acordos"
                        icon="info"
                        what="Valor de alçada final dos acordos que entraram na execução no período selecionado."
                        counts='Mesmo conjunto de processos de "Entradas de Acordos", somando o valor em vez de contar.'
                        calc="Soma do VALOR_ALCADA_FINAL dos processos com entrada no período."
                        interpret="Mede o valor dos acordos que entraram no fluxo no período."
                    />
                    <MetricCard
                        name="Valor de Acordos Pagos"
                        icon="info"
                        what="Valor de alçada final dos acordos pagos no período selecionado."
                        counts='Mesmo conjunto de processos de "Acordos Pagos no Período", somando o valor em vez de contar.'
                        calc="Soma do VALOR_ALCADA_FINAL dos processos pagos no período."
                        interpret="Mede o valor financeiro efetivamente liquidado no período."
                    />
                    <MetricCard
                        name="Mediana de Tempo"
                        icon="scale"
                        what="Ver 'Média de Tempo / Mediana de Tempo' acima — os dois cards usam o mesmo cálculo."
                        counts="Mesmo recorte da Média de Tempo."
                        calc="Mediana das durações (DATA DE EXECUÇÃO → pagamento)."
                        interpret="Referência do tempo 'típico', menos sensível a casos extremos que a média."
                    />
                </DocGrid>
                <InfoBox>
                    O aviso no topo da página ("Existem N processos com valor de alçada final vazios!") conta, no total
                    atual em Execução de Acordos, quantos processos ainda não têm o campo VALOR_ALCADA_FINAL preenchido
                    — útil para identificar acordos que precisam de atenção antes de entrarem nos totais de valor.
                </InfoBox>
            </DocSection>

            <DocSection
                id="subfases"
                title="03 — Matérias e subfases"
                subtitle="Rankings do estoque atual por subfase, matéria, tempo de movimentação e classificação Judicial/Extrajudicial"
                icon="barChart"
            >
                <InfoBox>
                    Estes gráficos sempre mostram o estoque atual (processos na fase ACORDO, histórico completo) — não
                    são afetados pelo filtro de datas do calendário. Clique em uma barra ou fatia para filtrar o
                    restante da página por aquele valor.
                </InfoBox>
                <DocGrid>
                    <DocCard title="Valor Alçada Final por Subfase">
                        <p>
                            Soma o VALOR_ALCADA_FINAL dos acordos em execução, agrupado pela SUBFASE atual. Barras
                            roláveis quando há muitas subfases.
                        </p>
                    </DocCard>
                    <DocCard title="Processos por Subfase">
                        <p>Conta os acordos em execução por SUBFASE atual, com percentual do total.</p>
                    </DocCard>
                    <DocCard title="Taxa de Redução Estoque (TRE)">
                        <p>
                            (Estoque Inicial − Estoque Final) × 100 ÷ Estoque Final. Positivo indica que o estoque de
                            acordos diminuiu no período; negativo, que aumentou.
                        </p>
                    </DocCard>
                    <DocCard title="Pré x Pós-Sentença">
                        <p>
                            Classifica (gráfico de pizza) os acordos em execução entre <strong>Pré-Sentença</strong> e{' '}
                            <strong>Pós-Sentença</strong>, a partir das etiquetas correspondentes aplicadas ao processo
                            no LEXFLOW. Processos sem nenhuma das duas etiquetas aparecem como{' '}
                            <strong>Sem classificação</strong>.
                        </p>
                    </DocCard>
                    <DocCard title="Execução de Acordos por Matéria">
                        <p>
                            Distribuição (gráfico de pizza) dos acordos em execução por MATÉRIA. Só aparece quando há
                            mais de uma matéria no recorte atual.
                        </p>
                    </DocCard>
                    <DocCard title="Judicial x Extrajudicial">
                        <p>
                            Classifica os acordos entre <strong>Judicial</strong> e <strong>Extrajudicial</strong> a
                            partir das etiquetas correspondentes aplicadas ao processo no LEXFLOW. Processos sem nenhuma
                            das duas etiquetas aparecem como <strong>Sem classificação</strong>.
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>

            <DocSection
                id="tendencia"
                title="04 — Entradas e saídas de Acordos por mês"
                subtitle="Dois gráficos de linha, lado a lado, com uma linha por ano — histórico completo"
                icon="trendingUp"
            >
                <InfoBox>
                    Diferente dos cards de "Indicadores", estes gráficos contam TODOS os processos cuja data de execução
                    ou de pagamento caiu em cada mês, sem exigir que o processo ainda esteja em uma fase específica hoje
                    — é o recorte de "o que entrou/saiu historicamente".
                </InfoBox>
                <DocGrid>
                    <DocCard title="Entradas de Acordos por Mês">
                        <p>
                            Quantidade de processos com etiqueta "Acordo" cuja DATA DE EXECUÇÃO caiu em cada mês, com
                            uma linha por ano — os anos são comparados lado a lado no mesmo gráfico.
                        </p>
                    </DocCard>
                    <DocCard title="Saídas de Acordos por Mês">
                        <p>
                            Quantidade de acordos pagos (DATA DE PAGAMENTO DO ACORDO) por mês, com uma linha por ano —
                            mesmo formato do gráfico de entradas, para facilitar a comparação lado a lado.
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>

            <DocSection
                id="evolucao"
                title="05 — Evolução de valores de acordos"
                subtitle="Valor de entrada (esquerda) e de saída (direita), mês a mês, comparado entre anos"
                icon="trendingUp"
            >
                <InfoBox>
                    Mesma lógica dos gráficos de quantidade da seção anterior, mas somando o valor de alçada final em
                    vez de contar processos. Em qualquer gráfico com uma linha por ano, o ano atual aparece sempre em
                    laranja — as demais cores são atribuídas automaticamente por ano.
                </InfoBox>
                <DocGrid>
                    <DocCard title="Valor de Entrada de Acordos por Mês">
                        <p>
                            Soma o VALOR_ALCADA_FINAL dos processos com etiqueta "Acordo" cuja DATA DE EXECUÇÃO caiu em
                            cada mês, agrupado por mês, com uma linha por ano — histórico completo.
                        </p>
                    </DocCard>
                    <DocCard title="Valor de Acordos Pagos Mês a Mês">
                        <p>
                            Soma o VALOR_ALCADA_FINAL dos acordos pagos (DATA DE PAGAMENTO DO ACORDO), agrupado por mês,
                            com uma linha por ano. Esta seção só aparece quando há dados de entrada ou de pagamento no
                            histórico.
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>

            <DocSection
                id="atividades"
                title="06 — Atividades"
                subtitle="Agendamentos do setor ACORDOS no LEXFLOW — produtividade, prazos e atrasos"
                icon="fileText"
            >
                <InfoBox>
                    Esta seção é independente do restante do dashboard: em vez de olhar para os processos de acordo em
                    si, olha para as <strong>tarefas/agendamentos</strong> do setor <strong>ACORDOS</strong> no LEXFLOW
                    (ex.: "ACORDOS - ANÁLISE DE PROPOSTA", "ACORDOS - MONITORAR PROTOCOLO DA MINUTA"). Tem um botão{' '}
                    <strong>Concluídas / Por prazo</strong> que troca o eixo de tempo usado por toda a seção:
                </InfoBox>
                <DocGrid>
                    <DocCard title="Concluídas">
                        <p>
                            Usa a data de criação/conclusão do agendamento. "Total" conta o que foi criado no período;
                            "Concluídas" conta o que foi encerrado no período.
                        </p>
                    </DocCard>
                    <DocCard title="Por prazo">
                        <p>
                            Usa o PRAZO do agendamento como eixo — útil para ver o que estava previsto para acontecer no
                            período, independente de quando foi criado.
                        </p>
                    </DocCard>
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
                        counts="Agendamentos ainda ativos (não encerrados/cancelados) com PRAZO anterior a hoje (Vencidas) ou igual a hoje (Vencem hoje) — independe do período selecionado."
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

                <DocGrid>
                    <DocCard title="Por atividade / Por funcionário">
                        <p>
                            Dois gráficos de distribuição: processos distintos por tipo de atividade do agendamento, e
                            volume de demandas por funcionário responsável (clicáveis para filtrar a lista de tarefas
                            abaixo).
                        </p>
                    </DocCard>
                    <DocCard title="Produção Diária / Média Resolvidos por Funcionário">
                        <p>
                            Quantidade de atividades "Encerrado Cumprido" por mês (com detalhamento dia a dia ao clicar
                            em um mês) e a média diária de atividades cumpridas por funcionário, contra uma meta de
                            referência de 20/dia.
                        </p>
                    </DocCard>
                </DocGrid>

                <DocCard title="Lista de tarefas">
                    <p>
                        Ao final da seção, uma tabela paginada com cada agendamento individual (nº do processo,
                        atividade, status, situação, responsável, prazo). Reflete os mesmos filtros de
                        funcionário/atividade/status/situação aplicados acima.
                    </p>
                </DocCard>
            </DocSection>

            <DocSection
                id="lista"
                title="07 — Execuções de Acordo (lista)"
                subtitle="Tabela paginada de processos, com três recortes à escolha"
                icon="sheet"
            >
                <InfoBox>
                    Tabela com nº do processo, UF, data da execução, valor de alçada final e subfase — com um seletor{' '}
                    <strong>Entradas / Saídas / Total</strong> que troca o recorte de processos exibido, usando
                    exatamente os mesmos critérios dos cards da seção Indicadores:
                </InfoBox>
                <DocGrid>
                    <DocCard title="Entradas">
                        <p>
                            Mesmo critério do card "Entradas de Acordos": etiqueta "Acordo" + DATA DE EXECUÇÃO no
                            período selecionado.
                        </p>
                    </DocCard>
                    <DocCard title="Saídas">
                        <p>
                            Mesmo critério do card "Acordos Pagos no Período": DATA DE PAGAMENTO DO ACORDO no período
                            selecionado.
                        </p>
                    </DocCard>
                    <DocCard title="Total">
                        <p>
                            Mesmo critério do card "Total em Execução de Acordos": estoque atual (fase ACORDO), sem
                            depender do período selecionado.
                        </p>
                    </DocCard>
                </DocGrid>
                <DocCard title="Ordenação e paginação">
                    <p>
                        10 processos por página, com opção de ordenar por data (mais recente/mais antiga primeiro) ou
                        por valor de alçada final (maior/menor primeiro).
                    </p>
                </DocCard>
            </DocSection>

            <DocSection
                id="exportar"
                title="Exportar relatório"
                subtitle="Botão 'Exportar' no topo da página — disponível para gestores e desenvolvedores"
                icon="download"
            >
                <InfoBox>
                    Abre um diálogo com dois tipos de relatório, cada um com seus próprios campos e recorte, exportáveis
                    em CSV ou XLSX.
                </InfoBox>
                <DocGrid>
                    <DocCard title="Processos">
                        <p>
                            Mesmos dados da tabela "Execuções de Acordo" (seção 07): escolha entre Entradas, Saídas ou
                            Total, e marque quais dos 14 campos disponíveis (identificação, datas e valores) incluir na
                            planilha. Respeita os filtros de matéria/subfase/Judicial × Extrajudicial ativos na página.
                        </p>
                    </DocCard>
                    <DocCard title="Atividades">
                        <p>
                            Dados da seção Atividades (06): escolha entre a visão Concluídas ou Por prazo. Inclui um
                            número do processo (obtido cruzando o agendamento com os processos de acordo — nem sempre
                            disponível), atividade, status, situação, responsáveis, prazo e descrição. Respeita os
                            filtros de funcionário/atividade/status/situação ativos na seção Atividades.
                        </p>
                    </DocCard>
                </DocGrid>
                <InfoBox>
                    Em ambos os casos, o período selecionado no calendário também é usado — exceto no recorte "Total" do
                    relatório de Processos, que (como o card "Total em Execução de Acordos") ignora o período e sempre
                    reflete o estoque atual.
                </InfoBox>
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
