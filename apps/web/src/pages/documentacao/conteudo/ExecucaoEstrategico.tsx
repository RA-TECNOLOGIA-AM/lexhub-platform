import {
    DocCard,
    DocGrid,
    DocPage,
    DocSection,
    InfoBox,
    MetricCard,
    WatchBox,
    type TocItem,
} from '../components/DocParts.tsx'

// Guia trazido da v1: LexHub/src/pages/documentacao/ExecucaoEstrategicoGeral.tsx (convertido para as peças da V2).

const TOC: TocItem[] = [
    { id: 'como-funciona', label: 'Como funciona' },
    { id: 'indicadores', label: 'Indicadores' },
    { id: 'tendencia', label: 'Entradas e saídas' },
    { id: 'confeccao-cs', label: 'Confecção CS' },
    { id: 'filtros', label: 'Filtros' },
    { id: 'relatorio', label: 'Relatório Personalizado' },
]

export function ExecucaoEstrategicoDoc() {
    return (
        <DocPage
            title="Execução Estratégico — NG, LA e LARJ"
            tags={['NG', 'LA', 'LARJ']}
            note="Mesma lógica nas três unidades, exceto Confecção CS (só NG/LA)"
            toc={TOC}
            intro={
                <>
                    Este guia explica o dashboard de Execução Estratégico: uma visão combinada que soma os dados
                    dos dashboards Execução Estratégico (Condenação) e Execução Acordos Estratégico num único conjunto
                    de indicadores e gráficos. Nenhum conhecimento técnico é necessário.
                </>
            }
        >
            <DocSection
                id="como-funciona"
                title="Como o dashboard funciona"
                subtitle="Soma dos dashboards Execução Estratégico (Condenação) e Execução Acordos Estratégico"
            >
                <InfoBox>
                    Este dashboard busca os dados dos dois dashboards de origem do mesmo escritório (Condenação e
                    Acordos) e soma indicador a indicador, gráfico a gráfico. Os dois universos são mutuamente
                    exclusivos — a base de Condenação já exclui processos com etiqueta "Acordo" — então a soma dá o
                    total real de "Execução" (Condenação + Acordos), sem risco de contar o mesmo processo duas vezes.
                    NG, LA e LARJ têm a mesma lógica, cada um somando só os dados do seu próprio escritório — com uma
                    exceção: LARJ não tem a seção "Confecção CS" (ver caixa abaixo).
                </InfoBox>
                <DocCard title={'LARJ não tem a seção "Confecção CS"'}>
                    <p>
                        A Seção 03 (gargalos da atividade "Elaborar Cumprimento de Sentença") só existe quando o
                        dashboard de origem Execução Condenação tem esse conceito cadastrado. NG e LA têm; LARJ, por
                        enquanto, não — então o dashboard de Execução Estratégico LARJ mostra só as Seções 01
                        (Indicadores) e 02 (Entradas e saídas por mês).
                    </p>
                </DocCard>
                <DocCard title="Filtro de Escopo">
                    <p>
                        O seletor "Ambos / Condenação / Acordos" no topo da página controla quais dos dois lados entram
                        na soma de cada indicador e gráfico. Quando um dos lados é excluído, a página se comporta como
                        se aquele dashboard de origem não existisse — inclusive a seção Confecção CS, que só existe no
                        lado Condenação, some quando o escopo é restrito a "Acordos".
                    </p>
                </DocCard>
                <DocCard title="Quando usar este dashboard em vez dos dois separados">
                    <p>
                        Use o Execução Estratégico para uma visão executiva única do setor de Execução como um
                        todo. Para o detalhe fino de cada domínio (TRE, classificação Judicial x Extrajudicial, alerta
                        de valor de alçada final vazio, etc.), use os dashboards de origem — Execução Estratégico e
                        Execução Acordos Estratégico (documentações separadas).
                    </p>
                </DocCard>
            </DocSection>

            <DocSection
                id="indicadores"
                title="Indicadores"
                subtitle="Soma dos indicadores de volume, entrada, saída e valor dos dois dashboards de origem"
            >
                <InfoBox>
                    Cada card soma o valor equivalente de Condenação e de Acordos (respeitando o filtro de Escopo). A
                    maioria reflete o total atual (histórico completo, não muda com o filtro de datas); "Quantidade de
                    entrada", "Quantidade de saída" e os valores correspondentes respeitam o período selecionado no
                    calendário. "Valor Remanescente" e "Valor Incontroverso" só existem no lado Condenação — Acordos não
                    tem o conceito de pagamento parcial do alvará.
                </InfoBox>

                <WatchBox>
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                        <h3 className="doc-h3">
                            Pagamento parcial do alvará: o que acontece com "Valor Total em execução"?
                        </h3>
                    </div>
                    <p>
                        Às vezes o alvará de um processo é pago em duas partes: primeiro a parte{' '}
                        <strong>incontroversa</strong> (o que ninguém discute que é devido), depois o restante. Quando
                        isso acontece, o valor "em aberto" do processo deixa de ser o valor cheio e passa a ser só o que
                        ainda falta pagar — o <strong>remanescente</strong>.
                    </p>
                    <DocCard>
                        <p>
                            <strong>Exemplo:</strong> um processo de <strong>R$ 100 mil</strong> tem R$ 80 mil de
                            incontroverso pago. Sobram <strong>R$ 20 mil</strong> de remanescente. A partir desse
                            momento, o "Valor Total em execução" passa a contar só os <strong>R$ 20 mil</strong> para
                            esse processo — os R$ 80 mil saem do total e não voltam, mesmo em períodos futuros.
                        </p>
                    </DocCard>
                    <p>
                        Os R$ 80 mil não somem do dashboard: eles aparecem no card{' '}
                        <strong>"Valor Incontroverso"</strong>, mas só no período em que a compensação aconteceu — é um
                        indicador de fluxo (o que caiu naquele mês), diferente de "Valor Total em execução", que é
                        sempre o estoque atual.
                    </p>
                </WatchBox>

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
                        counts={'Condenação: DATA_EXECUCAO no período. Acordos: DATA_ACORDO_FECHADO no período.'}
                        calc="Soma da quantidade de entrada no período dos dois dashboards."
                        interpret="Mede o volume de trabalho que chegou na Execução no período, somando os dois domínios."
                    />
                    <MetricCard
                        icon="dollar"
                        name="Valor em Execução"
                        what="Valor de entrada dos processos no período (Condenação + Acordos). Traz também o 'Ticket Médio' (Valor em Execução ÷ Quantidade de entrada)."
                        counts={
                            'Condenação: VALOR_EXECUCAO dos processos com DATA_EXECUCAO no período. Acordos: VALOR_ALCADA_FINAL dos processos com DATA_ACORDO_FECHADO no período.'
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
                        what="Valor de saída dos processos no período (Condenação + Acordos). Traz também o 'Valor TED' (só lado Condenação)."
                        counts={
                            'Condenação: valor executado com DATA_COMPENSACAO_ALVARA no período. Acordos: VALOR_ALCADA_FINAL dos acordos pagos no período.'
                        }
                        calc="Soma do valor de saída no período dos dois dashboards."
                        interpret="Mede o valor financeiro efetivamente liquidado da Execução no período."
                        caveat="Condenação: se o processo já teve a parte incontroversa compensada em outro período, o valor aqui soma só o remanescente — não o valor cheio, evitando contar a parte incontroversa duas vezes."
                    />
                    <MetricCard
                        icon="dollar"
                        name="Valor Incontroverso"
                        what="Valor incontroverso pago no período, mesmo com o processo ainda ativo na fase Execução (só lado Condenação)."
                        counts="Processos com compensação parcial do incontroverso registrada dentro do período selecionado."
                        calc="Soma de VALOR_INCONTROVERSO desses processos."
                        interpret="É o que 'saiu' de Valor Total em execução no período por causa de pagamento parcial — ver caixa de explicação acima."
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
                        icon="target"
                        name="Média de Tempo / Mediana de Tempo"
                        what="Tempo entre entrada e saída da Execução, em média e em mediana (Condenação + Acordos)."
                        counts="Soma da média/mediana de tempo calculada em cada dashboard de origem, no período selecionado."
                        calc="Média (ou mediana) de tempo de cada lado, somadas."
                        interpret="Quanto menor, mais rápido os processos estão sendo resolvidos."
                    />
                </DocGrid>
            </DocSection>

            <DocSection
                id="tendencia"
                title="Entradas e saídas na Execução por mês"
                subtitle="Gráficos de tendência combinados, com seletores de modo próprios"
            >
                <InfoBox>
                    Estes gráficos usam o histórico completo (não dependem do filtro de datas do calendário, exceto onde
                    indicado) e somam Condenação + Acordos mês a mês, matéria a matéria, subfase a subfase ou comarca a
                    comarca, conforme o caso.
                </InfoBox>
                <DocGrid>
                    <DocCard title="Entradas e Saídas na Execução por Mês">
                        <p>
                            Duas linhas (Quantidade Entrada e Quantidade Saída) por mês, somando os dois dashboards de
                            origem. Use o seletor de ano para trocar o ano exibido. Clique em um mês para filtrar a
                            página pelo período daquele mês.
                        </p>
                    </DocCard>
                    <DocCard title="Demonstrativo de Matérias">
                        <p>
                            Gráfico de pizza por matéria (soma dos dois lados), com um seletor de modo:{' '}
                            <strong>Total</strong> (estoque atual), <strong>Qtd Entrada</strong> ou{' '}
                            <strong>Valor Entrada</strong>. Clique em uma fatia para filtrar o restante da página por
                            aquela matéria.
                        </p>
                    </DocCard>
                    <DocCard title="Valor de Entrada na Execução por Mês">
                        <p>
                            Uma linha por ano, somando o valor de entrada (VALOR_EXECUCAO na Condenação,
                            VALOR_ALCADA_FINAL nos Acordos) de cada mês — todos os anos disponíveis lado a lado, para
                            comparação sazonal.
                        </p>
                    </DocCard>
                    <DocCard title="Valor por Subfase">
                        <p>
                            Barras horizontais roláveis com o valor por subfase (soma dos dois lados), com seletor{' '}
                            <strong>Total</strong> ou <strong>Entrada</strong>. Clique em uma barra para filtrar o
                            restante da página por aquela subfase.
                        </p>
                    </DocCard>
                    <DocCard title="Ano de Ajuizamento (Entradas / Total)">
                        <p>
                            Dois gráficos de pizza lado a lado — um para os processos que entraram no período, outro
                            para o total atual — agrupando por ano de ajuizamento (DATA_DISTRIBUICAO), com quantidade e
                            valor somados por ano. Clique em uma fatia para filtrar por aquele ano de ajuizamento.
                        </p>
                    </DocCard>
                    <DocCard title="Valor de Entrada e Saída na Execução por Mês">
                        <p>
                            Duas barras por mês (Valor de Entrada e Valor de Saída), cada uma com sua própria escala,
                            somando os dois dashboards de origem. Usa o mesmo ano selecionado no gráfico de Entradas e
                            Saídas acima.
                        </p>
                    </DocCard>
                    <DocCard title="Tempo Médio em Dias — Execução por Mês">
                        <p>
                            Uma linha por ano com o tempo médio (em dias) entre entrada e saída da Execução, somando o
                            tempo médio de Condenação e de Acordos mês a mês.
                        </p>
                    </DocCard>
                    <DocCard>
                        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                            <h3 className="doc-h3">Processos por Comarca</h3>
                        </div>
                        <p>
                            Lista rankeada de comarcas (soma dos dois lados), com seletor <strong>Total</strong>,{' '}
                            <strong>Entradas</strong> ou <strong>Saídas</strong> — esse seletor só afeta a quantidade e
                            o valor de cada linha. Além da quantidade e do percentual, cada linha traz o valor de
                            execução somado (Condenação: VALOR_EXECUCAO; Acordos: VALOR_ALCADA_FINAL) e o tempo médio
                            entre entrada e saída da Execução naquela comarca — este último é <strong>fixo</strong>,
                            calculado sempre sobre o histórico completo da comarca (não muda com o seletor
                            Total/Entradas/Saídas), pra servir de referência estável de quanto tempo um processo daquela
                            comarca costuma levar pra sair da Execução. Quando as duas datas relevantes não estão
                            preenchidas para nenhum processo da comarca, o tempo médio aparece como "—". Clique em uma
                            comarca para adicioná-la (ou removê-la) do filtro de Comarca da página — o mesmo filtro do
                            dropdown "Comarca" na barra de filtros. Pode selecionar mais de uma comarca ao mesmo tempo;
                            as barras das comarcas selecionadas ficam destacadas.
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>

            <DocSection
                id="confeccao-cs"
                title="Confecção CS"
                subtitle={
                    'Painel de gargalos da(s) atividade(s) "Elaborar Cumprimento de Sentença" — só no lado Condenação'
                }
            >
                <InfoBox>
                    Esta seção só existe no dashboard Execução Estratégico (Condenação) — não há equivalente em Execução
                    Acordos. Por isso ela desaparece da página quando o filtro de Escopo está restrito a "Acordos". Ela
                    filtra os agendamentos do setor pela atividade "Elaborar Cumprimento de Sentença" — a etapa que
                    formaliza o pedido de cumprimento de sentença e dá início à Execução.
                </InfoBox>
                <DocCard title="Diferença entre NG e LA">
                    <p>
                        No NG a atividade é dividida em duas variantes por grau — "Elaborar Cumprimento de Sentença
                        (1G)" e "Elaborar Cumprimento de Sentença (2G)" — e esta seção filtra as duas juntas. No LA a
                        atividade é uma só, sem esse split por grau. O resto do painel (KPIs, gráficos, lista de
                        tarefas) funciona da mesma forma nos dois escritórios.
                    </p>
                </DocCard>

                <DocCard title={'"Concluídas" vs. "Por prazo"'}>
                    <p>
                        O botão no canto superior direito da seção alterna o eixo temporal de toda a seção entre{' '}
                        <strong>Concluídas</strong> (data de criação/conclusão) e <strong>Por prazo</strong> (data de
                        prazo do agendamento).
                    </p>
                </DocCard>

                <DocGrid>
                    <MetricCard
                        icon="check"
                        name="Total / Em andamento / Vencidas / Vencem hoje / Concluídas"
                        what={
                            'Os cinco KPIs padrão, restritos à(s) atividade(s) "Elaborar Cumprimento de Sentença" (no NG, as duas variantes por grau; no LA, a atividade única).'
                        }
                        counts={'Agendamentos da(s) atividade(s) de Cumprimento de Sentença.'}
                        calc="Mesmo critério do dashboard de Execução, mas com o filtro de atividade fixo em Cumprimento de Sentença."
                        interpret="Um número alto de 'Vencidas' aqui é um forte indício de gargalo represando a entrada de novos processos na Execução."
                    />
                    <MetricCard
                        icon="trendingUp"
                        name="Média mensal de entrada"
                        what="Média histórica de quantas atividades de Cumprimento de Sentença são criadas por mês."
                        counts="Histórico completo de criação da(s) atividade(s), independente do período selecionado."
                        calc="Média histórica de criação por mês."
                        interpret={
                            'Serve como referência de "demanda normal" — compare com o volume atual para saber se a entrada está acima ou abaixo do padrão.'
                        }
                    />
                    <MetricCard
                        icon="users"
                        name="Demandas por Funcionário (Cumpridas)"
                        what="Volume de encerramentos com sucesso da Confecção CS, por funcionário responsável pelo encerramento."
                        counts={
                            'Agendamentos "Encerrado Cumprido" da(s) atividade(s), na visão ativa (Concluídas ou Por prazo).'
                        }
                        calc="Contagem por funcionário, considerando apenas status Encerrado Cumprido — os Não Cumpridos ficam fora deste gráfico (ver 'Motivo do Não Cumprimento')."
                        interpret="Clique no nome de um funcionário para filtrar; mostra quem está dando vazão ao gargalo com sucesso."
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
                    <MetricCard
                        icon="check"
                        name="Taxa de Cumprimento"
                        what="Percentual de encerramentos bem-sucedidos da Confecção CS sobre o total de encerramentos."
                        counts={
                            'Agendamentos "Encerrado Cumprido" e "Encerrado Não Cumprido" da(s) atividade(s), na visão ativa.'
                        }
                        calc="Taxa de Cumprimento = Cumpridos ÷ (Cumpridos + Não Cumpridos) × 100."
                        interpret="Quanto mais próximo de 100%, menor a perda de produtividade por atividades não cumpridas."
                    />
                </DocGrid>
            </DocSection>

            <DocSection id="filtros" title="Filtros disponíveis" subtitle="Como personalizar a visão do dashboard">
                <DocGrid>
                    {[
                        {
                            name: 'Período (calendário)',
                            desc: "Afeta os KPIs de entrada/saída da seção Indicadores e da Confecção CS. Não afeta os cards e gráficos marcados como 'histórico completo'.",
                        },
                        {
                            name: 'Escopo (Ambos / Condenação / Acordos)',
                            desc: "Na barra de filtros do topo. Restringe a soma de todos os indicadores e gráficos a um só dos dois dashboards de origem — ou mantém a soma dos dois ('Ambos').",
                        },
                        {
                            name: 'UF',
                            desc: 'Dropdown com múltipla escolha na barra de filtros. Restringe todo o dashboard (Condenação e Acordos) às UFs selecionadas. As opções vêm da união dos dois dashboards de origem.',
                        },
                        {
                            name: 'Comarca',
                            desc: "Dropdown com múltipla escolha na barra de filtros, ou clique direto numa barra do gráfico 'Processos por Comarca' — os dois controlam o mesmo filtro. Restringe todo o dashboard às comarcas selecionadas.",
                        },
                        {
                            name: 'Matéria / Subfase',
                            desc: 'Dropdown de escolha única na barra de filtros, ou clique direto numa fatia/barra dos gráficos de Matéria e Subfase — os dois controlam o mesmo filtro. As opções vêm da união dos dois dashboards de origem.',
                        },
                        {
                            name: 'Ano de Ajuizamento',
                            desc: 'Clique em uma barra do gráfico de tendência para filtrar o restante da página por aquele ano.',
                        },
                        {
                            name: 'Mês (gráficos de entrada/saída)',
                            desc: 'Clique em um mês para aplicar o período daquele mês inteiro ao filtro de calendário.',
                        },
                        {
                            name: 'Modo do gráfico (Matérias / Subfase / Comarca)',
                            desc: 'Seletores próprios de cada gráfico para trocar entre visão Total, Entrada, Saída ou Valor Entrada, conforme o gráfico.',
                        },
                        {
                            name: 'Funcionário / Situação (Confecção CS)',
                            desc: 'Clique em uma barra, nome de funcionário ou card de KPI para filtrar a lista de atividades de Confecção CS.',
                        },
                        {
                            name: 'Concluídas / Por prazo',
                            desc: 'Alterna o eixo temporal (data de conclusão vs. data de prazo) da seção Confecção CS.',
                        },
                    ].map((f) => (
                        <DocCard>
                            <p>{f.name}</p>
                            <p>{f.desc}</p>
                        </DocCard>
                    ))}
                </DocGrid>
            </DocSection>

            <DocSection
                id="relatorio"
                title="Relatório Personalizado"
                subtitle="Exportação em CSV/XLSX, em três etapas"
            >
                <InfoBox>
                    O botão "Relatório Personalizado" (canto superior direito) abre um diálogo em etapas: primeiro
                    pergunta a <strong>origem</strong> do relatório, depois (dependendo da resposta) o{' '}
                    <strong>escopo</strong>, e por fim deixa escolher o <strong>recorte</strong> e os{' '}
                    <strong>campos</strong>. Um botão "Voltar" permite corrigir uma etapa anterior sem fechar o diálogo.
                </InfoBox>

                <DocGrid>
                    <DocCard title="1. Origem: Filtros ativos na Página">
                        <p>
                            Pula direto para a escolha de recorte e campos, usando o escopo que já está ativo na página
                            (Ambos/Condenação/Acordos). O arquivo sai automaticamente filtrado pelo período do
                            calendário e pelos filtros de UF, Comarca, Matéria, Subfase e Ano de Ajuizamento ativos na
                            página. Por exemplo, se a página estiver filtrada por Comarca "Beruri" e você exportar o
                            recorte "Saída", o arquivo trará só as saídas daquela comarca, não o total geral.
                        </p>
                    </DocCard>
                    <DocCard title="1. Origem: Relatório personalizado">
                        <p>
                            Monta um relatório do zero, independente do que está filtrado na página — pergunta em
                            seguida o escopo: <strong>Condenação</strong>, <strong>Acordos</strong> ou{' '}
                            <strong>Os dois juntos</strong>.
                        </p>
                    </DocCard>
                    <DocCard title={'"Os dois juntos" sai num arquivo só'}>
                        <p>
                            Condenação e Acordos são consultas diferentes e não podem virar uma tabela só, mas viram um{' '}
                            <strong>arquivo</strong> só. Quando o escopo envolve os dois — seja porque a página estava
                            com Escopo "Ambos" e você escolheu "Filtros ativos na Página", seja porque você escolheu "Os
                            dois juntos" no relatório personalizado — a tela final mostra os campos de Condenação e de
                            Acordos em blocos separados (cada um com seu próprio "Selecionar todos"/"Desmarcar todos"),
                            e um único clique em Exportar baixa: no <strong>XLSX</strong>, um arquivo com uma aba
                            "Execução Condenação" e outra "Execução Acordos"; no <strong>CSV</strong>, um .zip com um
                            CSV de cada (CSV não tem o conceito de aba). Se você desmarcar todos os campos de um dos
                            dois lados, aquela origem simplesmente não entra no arquivo.
                        </p>
                    </DocCard>
                    <DocCard>
                        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                            <h3 className="doc-h3">Recorte (Entrada / Saída / Total)</h3>
                        </div>
                        <p>
                            Escolhe quais processos entram no arquivo: os que entraram no período, os que saíram no
                            período, ou o estoque total atual — mesmo critério usado pelos KPIs da página. Aparece em
                            todas as combinações de origem/escopo.
                        </p>
                    </DocCard>
                    <DocCard title="Campos">
                        <p>
                            Lista de colunas selecionáveis por grupo (Identificação, Datas, Valores) — inclui UF,
                            Comarca, Vara e Competência em "Identificação". "Selecionar todos" / "Desmarcar todos"
                            agilizam a escolha.
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>
        </DocPage>
    )
}
