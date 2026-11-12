import {
    Code,
    DiffBox,
    DocCard,
    DocGrid,
    DocPage,
    DocSection,
    Formula,
    InfoBox,
    MetricCard,
    WatchBox,
    type TocItem,
} from '../components/DocParts.tsx'

// Guia do Recursal (NG). Texto da v1: LexHub/src/pages/documentacao/Recursal_NG.tsx.

const TOC: TocItem[] = [
    { id: 'como-funciona', label: 'Como funciona' },
    { id: 'indicadores', label: 'Estoque e entrada' },
    { id: 'extintos-2g', label: 'Extintos 2º grau' },
    { id: 'decisoes', label: 'Decisões 1G × 2G' },
    { id: 'meta-provimento', label: 'Meta de Provimento Mensal' },
    { id: 'atividades', label: 'Atividades do setor Recursos' },
    { id: 'comissao', label: 'Comissionamento' },
    { id: 'exportacao', label: 'Exportação' },
    { id: 'filtros', label: 'Filtros' },
]

const FILTERS = [
    { name: 'Data', desc: 'Período aplicado a entradas, decisões e Meta de Provimento Mensal.' },
    { name: '1º grau / 2º grau', desc: 'Status de sentença/acórdão — clicável direto nos gráficos.' },
    { name: 'Decisão', desc: 'Um dos 10 tipos da Matriz de Classificação — clicável nos cartões ou na matriz.' },
    { name: 'Juiz / Relator', desc: 'Filtra pelo ranking de magistrados correspondente.' },
    {
        name: 'Matéria / Competência / Vara / Subfase',
        desc: 'Distribuição da fase Recursal — clicável nos gráficos de pizza/barras.',
    },
    { name: 'Extinto 2º grau', desc: 'Com mérito ou sem mérito, no painel de Extintos.' },
    {
        name: 'Funcionário / Atividade',
        desc: 'Restringe a lista de tarefas do setor RECURSOS e os gráficos de produção.',
    },
]

export function RecursalNGDoc() {
    return (
        <DocPage
            title="Recursal — NG"
            tags={['NG']}
            toc={TOC}
            intro={
                <>
                    Este guia explica o estoque e as entradas na fase Recursal, o cruzamento de decisões 1º × 2º grau, a
                    Meta de Provimento Mensal, as tarefas do setor <strong>RECURSOS</strong> e — em detalhe — a regra de
                    comissionamento do setor, incluindo como erros de retrabalho são detectados e por que exigem revisão
                    manual antes de fechar a folha.
                </>
            }
        >
            <DocSection
                id="como-funciona"
                title="Como o dashboard funciona"
                subtitle="Fase Recursal, escritório NG e o catálogo dinâmico de atividades"
                icon="fileText"
            >
                <InfoBox>
                    A base é todo processo do escritório NG (<Code>ID_ESCRITORIO</Code> = 20) atualmente na fase
                    Recursal (<Code>ID_FASE</Code> = 8). Quando o processo tem um agendamento aberto no setor{' '}
                    <strong>RECURSOS</strong> (ids de setor = 149), esse agendamento só é considerado válido se a
                    atividade pertencer ao catálogo do setor — carregado dinamicamente do banco a cada ciclo, não é uma
                    lista fixa no código. Isso significa que uma atividade nova cadastrada no setor aparece
                    automaticamente nos gráficos, sem precisar de deploy.
                </InfoBox>
                <DiffBox>
                    O Recursal LA usa o mesmo mecanismo de catálogo dinâmico (setor RECURSOS = <Code>id_setor</Code>{' '}
                    16), desde 15/09/2026 — antes disso a LA usava uma lista fixa no código, que ficou desatualizada e
                    fez tarefas de atividades novas ("ELABORAR CONTRARRAZÕES APELAÇÃO", "ELABORAR CONTRARRAZOES
                    INOMINADO", entre outras) sumirem silenciosamente dos KPIs. A diferença que permanece é só de
                    volume: o setor do NG tem 65+ atividades cadastradas, bem mais granular que as ~30 da LA — reflexo
                    de como cada escritório organiza o próprio fluxo de trabalho, não uma diferença de implementação.
                </DiffBox>
                <DocCard title="Estoque × Entrada">
                    <p>
                        Os gráficos de distribuição (subfase, matéria, competência, vara) têm um alternador que troca a
                        base de cálculo:
                    </p>
                    <DocGrid>
                        <DocCard title="Total (estoque)">
                            <p>
                                Todo processo com <Code>ID_FASE</Code> = 8 hoje, sem filtro de data — "quanto está
                                parado na Recursal agora".
                            </p>
                        </DocCard>
                        <DocCard title="Entrada no período">
                            <p>
                                Processos cuja <Code>DT_ENTRADA_RECURSAL</Code> cai dentro do período selecionado —
                                "quanto chegou na Recursal nesse intervalo".
                            </p>
                        </DocCard>
                    </DocGrid>
                </DocCard>
                <p className="muted small">
                    Todas as contagens de processo passam por deduplicação (<Code>_deduplicar_por_processo</Code>) — a
                    query de origem pode gerar mais de uma linha por processo (ex.: mais de uma parte adversa), e isso é
                    corrigido antes de qualquer soma ou contagem.
                </p>
            </DocSection>

            <DocSection
                id="indicadores"
                title="Estoque e entrada"
                subtitle="Os cartões de resumo da seção 'Estoque e extintos'"
                icon="barChart"
            >
                <DocGrid>
                    <MetricCard
                        name="Total em recursal"
                        icon="scale"
                        what="Estoque atual na fase Recursal, sem filtro de data."
                        counts="Todo processo do NG com ID_FASE = 8, deduplicado por processo."
                        calc="Contagem direta — não depende do período selecionado no topo do dashboard."
                        interpret="É a 'fila' inteira da fase, não o que entrou ou saiu no período."
                    />
                    <MetricCard
                        name="Total de entrada em recursal"
                        icon="fileText"
                        what="Quantos processos passaram a estar na Recursal durante o período."
                        counts="ID_FASE = 8 com DT_ENTRADA_RECURSAL dentro do intervalo selecionado."
                        calc="DT_ENTRADA_RECURSAL vem do log de fase (log_fase_processual, MAX(data) para id_fase=8, tipo_movimentacao='entrada') — não da tabela de agendamentos."
                        interpret="Mede o fluxo de entrada, não o estoque acumulado."
                    />
                    <MetricCard
                        name="Valor entrada acórdão Recursal"
                        icon="dollar"
                        what="Valor de causa/acordo dos processos que entraram na Recursal no período."
                        counts="Soma de VALOR_CAUSA_ACORDO dos processos com entrada no intervalo."
                        calc="Mesma base do cartão anterior — soma em vez de contagem."
                        interpret="Dimensiona financeiramente o fluxo de entrada, não o estoque total."
                    />
                </DocGrid>
            </DocSection>

            <DocSection
                id="extintos-2g"
                title="Extintos em 2º grau"
                subtitle="Com mérito, sem mérito e Taxa de Provimento"
                icon="scale"
            >
                <InfoBox>
                    Este painel não lê a base do Recursal (agendamentos/processos na fase 8) — usa a mesma base do
                    dashboard <strong>Controle de Processos</strong> (<Code>controle_processo_todas_situacoes</Code>),
                    incluindo processos <strong>arquivados e suspensos</strong>, não só os ainda ativos na Recursal. Por
                    isso um processo pode aparecer aqui mesmo depois de já ter saído da fase.
                </InfoBox>
                <DocGrid>
                    <MetricCard
                        name="Extintos com mérito (2º grau)"
                        icon="scale"
                        what="Processos cujo acórdão de 2º grau é uma decisão de mérito."
                        counts="Todo ID de mérito do 2G (esquema novo, 1-8) exceto Extinto Sem Mérito (7)."
                        calc="Contagem e soma de VALOR_CAUSA_ACORDO filtrando DATA_ACORDAO no período (usa DATA_ACORDAO_EMBARGOS quando presente)."
                        interpret="Volume e valor financeiro dos processos que tiveram desfecho de mérito em 2G no período."
                    />
                    <MetricCard
                        name="Extintos sem mérito (2º grau)"
                        icon="ban"
                        what="Processos cujo acórdão de 2º grau extinguiu sem julgar o mérito."
                        counts="ID de mérito do 2G = 7 (EXTINTO SEM MÉRITO, esquema novo)."
                        calc="Mesma lógica do card anterior, restrita a esse único ID."
                        interpret="Separado do 'com mérito' porque conta como decisão positiva na Taxa de Provimento (ver abaixo), apesar de não julgar o mérito."
                    />
                </DocGrid>
                <InfoBox>
                    O "ID de mérito" vem da coluna nova <Code>id_acordao_merito_grau2</Code> quando preenchida; quando
                    vazia, é traduzido pelo nome do status antigo (<Code>status_segundo_grau</Code>) para o ID
                    equivalente no esquema novo — mesma lógica em toda a Matriz de Julgamento (ver seção "Decisões 1º e
                    2º grau" abaixo). Migrado de <Code>ID_2G</Code> bruto para esse esquema em 15/09/2026.
                </InfoBox>
                <DocCard title="Taxa de Provimento (2º grau)">
                    <p>
                        <Code>positivos / total × 100</Code>, onde <strong>positivos</strong> = procedente, parcialmente
                        procedente (com ou sem proveito econômico), sentença anulada e extinto sem mérito;{' '}
                        <strong>total</strong> = todos os acórdãos 2G do período (com mérito + sem mérito).{' '}
                        <strong>Improcedente</strong> — incluindo, desde a migração, "Improcedente por
                        Prescrição/Decadência" — é o único grupo fora do numerador, mas continua no denominador.
                    </p>
                </DocCard>
                <DiffBox>
                    A coluna de valor aqui é <Code>VALOR_CAUSA_ACORDO</Code> (valor do acordo/decisão), diferente do
                    painel equivalente em Controle de Processos, que soma <Code>VALOR_DE_CAUSA</Code> (valor de causa
                    inicial) — mesma base de processos, coluna de dinheiro diferente porque respondem perguntas
                    diferentes.
                </DiffBox>
            </DocSection>

            <DocSection
                id="decisoes"
                title="Decisões 1º e 2º grau"
                subtitle="Cruzamento sentença × acórdão via Matriz de Classificação"
                icon="scale"
            >
                <InfoBox>
                    Os dois gráficos horizontais ("1º grau" e "2º grau") mostram a contagem bruta por status, filtrando
                    por <Code>DATA_SENTENCA</Code> (1G) ou <Code>DATA_ACORDAO</Code> (2G) no período. Os cartões de
                    "Decisões" acima deles já aplicam o cruzamento — a <strong>Matriz de Julgamento</strong>, que
                    combina o mérito de 1G com o de 2G para chegar a um dos 8 tipos de resultado ("Resultado Mapeado").
                </InfoBox>
                <DocCard title="Os 8 tipos de resultado">
                    <DocGrid>
                        <p>
                            <span className="badge ok">Mantido Ganho</span> — 1G e 2G no mesmo patamar de procedência.
                        </p>
                        <p>
                            <span className="badge ok">Ganho Ampliado</span> — 2G reconhece mais do que o 1G havia dado.
                        </p>
                        <p>
                            <span className="badge ok">Revertido Ganho</span> — 1G improcedente/extinto, 2G reverte para
                            procedente.
                        </p>
                        <p>
                            <span className="badge warn">Ganho Reduzido</span> — 2G reconhece menos do que o 1G.
                        </p>
                        <p>
                            <span className="badge warn">Extinção (Permite Reajuizar)</span> — 2G extingue sem mérito.
                        </p>
                        <p>
                            <span className="badge info">Instrução Retomada</span> — 2G anula a sentença (Sentença
                            Anulada), processo volta à instrução.
                        </p>
                        <p>
                            <span className="badge danger">Mantido Perda</span> — 1G e 2G ambos improcedentes.
                        </p>
                        <p>
                            <span className="badge danger">Revertido Perda</span> — 1G procedente, 2G reverte para
                            improcedente.
                        </p>
                    </DocGrid>
                </DocCard>
                <InfoBox>
                    Escala de mérito do esquema novo: <strong>1º grau</strong> tem 7 valores (Procedente Com/Sem PE,
                    Parc. Procedente Com/Sem PE, Improcedente, Improcedente por Prescrição/Decadência, Extinto Sem
                    Mérito). <strong>2º grau</strong> tem os mesmos 7 + <strong>Sentença Anulada</strong> (exclusivo do
                    2G). A matriz cruza as 7 linhas (1G) × 9 colunas (2G, incluindo "sem recurso" quando não há acórdão)
                    definidas na planilha "Matriz de Julgamento — 1º x 2º Grau".
                </InfoBox>
                <DiffBox>
                    Migrado em 15/09/2026 do esquema antigo (10 tipos, baseados em <Code>status_primeiro_grau</Code>/
                    <Code>status_segundo_grau</Code>) para este novo cruzamento por mérito. O ID de mérito vem das
                    colunas novas do LexFlow (<Code>id_sentenca_merito_grau1</Code>/<Code>id_acordao_merito_grau2</Code>
                    ) quando preenchidas; quando vazias, é traduzido pelo nome do status antigo — cobertura validada em{' '}
                    {'>'}99,9% de correspondência contra a base histórica. É o mesmo módulo (
                    <Code>matriz_julgamento</Code>), compartilhado entre NG e LA — não há mais diferença de
                    implementação entre os dois escritórios nesta matriz.
                </DiffBox>
                <p className="muted small">
                    Clicar em uma barra dos gráficos de 1º ou 2º grau, ou em uma célula da matriz (botão "Ver matriz de
                    classificação" no topo da seção), aplica o filtro correspondente à página inteira.
                </p>
            </DocSection>

            <DocSection
                id="meta-provimento"
                title="Meta de Provimento Mensal"
                subtitle="80 processos providos por mês — e por que a data do acórdão de embargos importa"
                icon="target"
            >
                <InfoBox>
                    Conta processos cujo acórdão de 2º grau caiu em uma das categorias "providas" — Procedente (COM PE),
                    Parc. Procedente (COM PE), Sentença Anulada e Procedente (SEM PE) — contra uma meta fixa de{' '}
                    <strong>80 processos/mês</strong>. A régua horizontal mostra o percentual atingido, com faixas em
                    0–70% (vermelho), 70–100% (cinza) e a marca de 100% (âmbar) quando a meta é batida.
                </InfoBox>
                <DocCard title="Data de referência: embargos primeiro">
                    <p>
                        A data usada para posicionar o processo no período é <Code>DATA_ACORDAO_EMBARGOS</Code> quando o
                        processo teve embargos de declaração — é o acórdão dos embargos que define a procedência final,
                        não o acórdão original. Só cai para <Code>DATA_ACORDAO</Code> quando não houve embargos.
                    </p>
                </DocCard>
                <DiffBox>
                    Corrigido em 24/08/2026: antes, a meta só olhava <Code>DATA_ACORDAO</Code>, ignorando que um novo
                    recurso (embargos) pode mudar a data — e o resultado — da procedência. A mesma regra de prioridade
                    (embargos, com fallback no acórdão original) é usada nesta meta.
                </DiffBox>
                <p className="muted small">
                    Este indicador também alimenta o comissionamento: <Code>meta_qualidade_atingida</Code> (usada no
                    bônus de R$ 200,00 da seção de Comissionamento) é exatamente <Code>qtd_provimento_mensal ≥ 80</Code>{' '}
                    no período selecionado no momento da exportação.
                </p>
            </DocSection>

            <DocSection
                id="atividades"
                title="Atividades no período (setor RECURSOS)"
                subtitle="KPIs de fila de trabalho, o alternador 'Por prazo / Concluídas' e o cartão 'Cancelados'"
                icon="fileText"
            >
                <InfoBox>
                    O alternador <strong>"Por prazo" / "Concluídas"</strong> no cabeçalho da seção troca a base dos 5
                    cartões de KPI sem nenhuma chamada nova à API — o backend já devolve os dois conjuntos de números no
                    mesmo payload, e o frontend só troca qual conjunto é exibido. "Por prazo" (padrão) mostra a fila
                    considerando o prazo de cada tarefa; "Concluídas" mostra a mesma fila considerando o fechamento
                    (Cumprido/Não Cumprido) no período. A Meta de Provimento Mensal (ver acima) é renderizada dentro
                    desta mesma seção, logo abaixo dos cartões de KPI.
                </InfoBox>
                <DocGrid>
                    <MetricCard
                        name="Total / Em andamento / Vencidas / Vencem hoje"
                        icon="clock"
                        what="Volume de tarefas do setor RECURSOS e sua situação de prazo."
                        counts='Total = criadas no período. Em andamento = abertas ("Recebido"/"Visualizado") entre as criadas no período. Vencidas/Vencem hoje comparam o PRAZO com a data de hoje.'
                        calc="Contagens diretas sobre os agendamentos do setor, filtrados pelo catálogo dinâmico de atividades."
                        interpret="Fila de trabalho corrente — não é o mesmo recorte do estoque/entrada da fase Recursal acima."
                    />
                    <MetricCard
                        name="Concluídas"
                        icon="check"
                        what="Tarefas do setor encerradas no período."
                        counts='"Encerrado Cumprido" ou "Encerrado Não Cumprido" com DATA_HORA_CONCLUSAO no período.'
                        calc="Contagem direta dos registros encerrados no período."
                        interpret="Produção de fechamento do setor — mas não confundir com a contagem de erros da Comissão (ver seção abaixo)."
                    />
                    <MetricCard
                        name="Cancelados"
                        icon="ban"
                        what="Casos em que uma tarefa foi encerrada como erro e encaminhada para retrabalho."
                        counts='Tarefa de ORIGEM encerrada como "Cancelado" ou "Encerrado Não Cumprido" cujo motivo_encaminhamento aponta para a família AVR-RETORNO ou RETORNO-CR.'
                        calc="Soma get_total_avr_retorno_recurso_cancelado_NG + get_total_retorno_cr_recurso_cancelado_NG, filtrando pela data de conclusão/cancelamento da tarefa de ORIGEM."
                        interpret="Mede quantos casos geraram retrabalho no período — ver o quadro de comparação na seção de Comissão para a diferença em relação à contagem de erros que efetivamente desconta comissão."
                    />
                </DocGrid>
            </DocSection>

            <DocSection
                id="comissao"
                title="Comissionamento"
                subtitle="Quantidade + qualidade − erros, por colaborador do roster fixo"
                icon="dollar"
            >
                <InfoBox>
                    O roster do setor é fixo no código (não vem de uma tabela de "subsetor" — não existe uma no banco):
                    Análise = Alessandra Souza de Aquino, Anderton Matheus Aquino dos Santos, Giovanna Santos Gualberto
                    da Costa e Vivian Alessandra Souza Fernandes; Confecção = Vivian, Bárbara Vitória Arirama Bezerra,
                    Isa Fernanda Morais da Silva Sousa e Náthaly Blanca Nunes de Sousa. Vivian aparece nos dois
                    subsetores e comissiona pela atividade que efetivamente concluir.
                </InfoBox>

                <DocCard title="Quantidade">
                    <div className="tblwrap">
                        <table className="tbl">
                            <thead>
                                <tr>
                                    <th>Subsetor</th>
                                    <th>Valor</th>
                                    <th>Conta quando</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>Análise</td>
                                    <td>
                                        <strong>R$ 0,50 / atividade</strong>
                                    </td>
                                    <td className="muted small">
                                        "Encerrado Cumprido" <strong>ou</strong> "Encerrado Não Cumprido" — a análise de
                                        viabilidade é remunerada independente do resultado. Inclui "Análise Sentença -
                                        Embargos".
                                    </td>
                                </tr>
                                <tr>
                                    <td>Confecção</td>
                                    <td>
                                        <strong>R$ 2,00 / atividade</strong>
                                    </td>
                                    <td className="muted small">
                                        Só "Encerrado Cumprido" — remunera o recurso de fato interposto.
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </DocCard>

                <DocCard title="Erros — contagem direta na própria atividade de retorno">
                    <p>
                        Cada fechamento (Cumprido <em>ou</em> Não Cumprido, no período) da própria atividade{' '}
                        <strong>AVR-RETORNO</strong> (qualquer variante da família) conta{' '}
                        <strong>1 erro de Análise</strong>, atribuído a quem estava atribuído àquela tarefa de retorno —
                        não a quem cometeu o erro na tarefa que a originou. O mesmo vale para{' '}
                        <strong>RETORNO-CR</strong>, contando 1 erro de Confecção.
                    </p>
                    <div className="tblwrap">
                        <table className="tbl">
                            <thead>
                                <tr>
                                    <th>Retorno</th>
                                    <th>Subsetor descontado</th>
                                    <th>Desconto</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>AVR-RETORNO — texto do fechamento contém "ALTERADO"</td>
                                    <td className="muted small">Análise</td>
                                    <td>
                                        <strong>R$ 0,50</strong>
                                    </td>
                                </tr>
                                <tr>
                                    <td>AVR-RETORNO — demais casos (inclusive sem texto)</td>
                                    <td className="muted small">Análise</td>
                                    <td>
                                        <strong>R$ 1,00</strong>
                                    </td>
                                </tr>
                                <tr>
                                    <td>RETORNO-CR — qualquer fechamento</td>
                                    <td className="muted small">Confecção</td>
                                    <td>
                                        <strong>R$ 4,00 (fixo)</strong>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </DocCard>

                <WatchBox>
                    <strong>Revisar antes de fechar a folha.</strong> Levantamento de casos históricos mostrou que a
                    maioria dos fechamentos de retorno tem uma causa <em>não</em> imputável ao colaborador — renúncia do
                    cliente, ausência em audiência sem justificativa, trânsito em julgado, entre outras. O sistema não
                    distingue isso automaticamente com segurança, então a decisão foi: sempre aplicar o desconto pela
                    regra acima, <strong>mas mostrar o texto do motivo de cada desconto no relatório</strong> para o
                    líder decidir manualmente se ele deve ser mantido ou revertido antes de fechar a folha do mês.
                </WatchBox>

                <DocCard title="Bônus de qualidade">
                    <DocGrid>
                        <DocCard title="Meta batida — R$ 200,00">
                            <p>
                                Para <strong>todo</strong> colaborador do roster, se a Meta de Provimento Mensal
                                (80/mês) foi atingida no período selecionado.
                            </p>
                        </DocCard>
                        <DocCard title="Zero retrabalho — R$ 100,00">
                            <p>
                                Individual — só para quem não teve <strong>nenhum</strong> erro (Análise + Confecção) no
                                mês.
                            </p>
                        </DocCard>
                    </DocGrid>
                </DocCard>

                <DocCard title="Fórmula do total por colaborador">
                    <Formula>
                        total = (qtd_análise × R$0,50) + (qtd_confecção × R$2,00) − desconto_análise −
                        desconto_confecção + bônus_meta + bônus_zero_retrabalho
                    </Formula>
                </DocCard>

                <DiffBox>
                    <strong>Não confundir com o cartão "Cancelados" da seção de Atividades.</strong> Aquele cartão conta
                    pelo <em>destino</em> apontado no <Code>motivo_encaminhamento</Code> da tarefa de <em>origem</em> —
                    é uma visão de fluxo de trabalho, para saber quantos casos foram encaminhados para retrabalho. A
                    comissão conta os <em>fechamentos da própria atividade de retorno</em>, atribuídos a quem executou o
                    retorno — é a visão de responsabilidade individual que efetivamente desconta em reais. Os dois
                    números podem — e costumam — divergir. Validado com dados reais de agosto/2026: 1 fechamento de
                    RETORNO-CR no mês (Bárbara Vitória Arirama Bezerra, R$ 4,00) e 19 fechamentos de AVR-RETORNO (1
                    deles identificado como "Recurso Alterado", R$ 0,50; os demais a R$ 1,00).
                </DiffBox>
            </DocSection>

            <DocSection
                id="exportacao"
                title="Exportação"
                subtitle="Relatório Personalizado (CSV) e Relatório de Comissão (PDF/CSV)"
                icon="sheet"
            >
                <DocGrid>
                    <DocCard title="Relatório Personalizado">
                        <p>
                            Exportação CSV com até 27 campos selecionáveis (identificação, processo, status judicial,
                            valores, datas, atividades), respeitando todos os filtros ativos no dashboard. Módulo
                            genérico, criado originalmente para o Recursal LA.
                        </p>
                    </DocCard>
                    <DocCard title="Relatório de Comissão">
                        <p>
                            PDF ou CSV com o resumo por colaborador (quantidade, bônus, descontos, total) e uma segunda
                            tabela de detalhamento — um linha por desconto de erro, com o texto do motivo do fechamento,
                            para a revisão manual descrita na seção de Comissionamento.
                        </p>
                    </DocCard>
                </DocGrid>
                <p className="muted small">
                    Endpoint: <Code>GET /recursal_NG/comissao/export</Code> (parâmetros <Code>from</Code>,{' '}
                    <Code>to</Code>, <Code>format</Code> e <Code>funcionario_recursos[]</Code>). O PDF usa quebras de
                    linha (<Code>Paragraph</Code>) em toda célula de texto que pode ser longa — nomes completos e textos
                    de motivo não sobrepõem mais colunas vizinhas.
                </p>
            </DocSection>

            <DocSection
                id="filtros"
                title="Filtros disponíveis"
                subtitle="Como personalizar a página inteira"
                icon="filter"
            >
                <DocGrid>
                    {FILTERS.map((f) => (
                        <DocCard key={f.name} title={f.name}>
                            <p>{f.desc}</p>
                        </DocCard>
                    ))}
                </DocGrid>
                <p className="muted small">
                    Os filtros se combinam em "E". Ao clicar num gráfico para filtrar sua própria dimensão, a API é
                    chamada sem esse filtro específico (os demais permanecem), para que a barra/fatia clicada continue
                    visível como opção.
                </p>
            </DocSection>
        </DocPage>
    )
}
