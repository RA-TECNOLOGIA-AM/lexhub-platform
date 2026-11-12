import {
    Code,
    DiffBox,
    DocCard,
    DocGrid,
    DocPage,
    DocSection,
    InfoBox,
    MetricCard,
    type TocItem,
} from '../components/DocParts.tsx'

// Guia do Recursal (LA). Texto da v1: LexHub/src/pages/documentacao/Recursal_LA.tsx.

const TOC: TocItem[] = [
    { id: 'como-funciona', label: 'Como funciona' },
    { id: 'indicadores', label: 'Estoque e extintos' },
    { id: 'decisoes', label: 'Decisões 1G × 2G' },
    { id: 'distribuicao', label: 'Matéria, competência e vara' },
    { id: 'atividades', label: 'Atividades do setor Recursos' },
    { id: 'exportacao', label: 'Exportação' },
    { id: 'filtros', label: 'Filtros' },
]

const FILTERS = [
    { name: 'Data', desc: 'Período aplicado a entradas, decisões e atividades do setor.' },
    { name: '1º grau / 2º grau', desc: 'Status de sentença/acórdão — clicável direto nos gráficos.' },
    { name: 'Decisão', desc: 'Um dos 8 tipos da Matriz de Julgamento — clicável nos cartões ou na matriz.' },
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

export function RecursalLADoc() {
    return (
        <DocPage
            title="Recursal — LA"
            tags={['LA']}
            toc={TOC}
            intro={
                <>
                    Este guia explica o estoque e as entradas na fase Recursal, o cruzamento de decisões 1º × 2º grau
                    via Matriz de Julgamento, as tarefas do setor <strong>RECURSOS</strong> e a exportação de dados via
                    Relatório Personalizado.
                </>
            }
        >
            <DocSection
                id="como-funciona"
                title="Como o dashboard funciona"
                subtitle="Fase Recursal, escritório LA e o catálogo dinâmico de atividades"
                icon="fileText"
            >
                <InfoBox>
                    A base é todo processo do escritório LA (Luis Albert) atualmente na fase Recursal (
                    <Code>ID_FASE</Code> = 8). Quando o processo tem um agendamento aberto no setor{' '}
                    <strong>RECURSOS</strong> (<Code>id_setor</Code> = 16), esse agendamento só é considerado válido se
                    a atividade pertencer ao catálogo do setor — carregado dinamicamente do banco a cada ciclo, não é
                    uma lista fixa no código. Isso significa que uma atividade nova cadastrada no setor aparece
                    automaticamente nos gráficos, sem precisar de deploy.
                </InfoBox>
                <DiffBox>
                    Corrigido em 15/09/2026: até então, o catálogo de atividades do setor RECURSOS (LA) era uma lista
                    fixa no código (28 atividades), diferente do NG (que já era dinâmico). Essa lista ficou
                    desatualizada e fez tarefas de atividades novas — "ELABORAR CONTRARRAZÕES APELAÇÃO", "ELABORAR
                    CONTRARRAZOES INOMINADO", "DILIGÊNCIA HT/NHT" e "REVISAR MEMORIAIS HT/NHT" — sumirem silenciosamente
                    dos KPIs e gráficos, mesmo estando ativas no LexFlow. Achado ao investigar uma divergência real: o
                    dashboard mostrava 140 tarefas encerradas por uma funcionária num período em que o relatório nativo
                    do LexFlow mostrava 149. Agora os dois escritórios usam o mesmo mecanismo dinâmico (NG:{' '}
                    <Code>id_setor</Code> = 149, ~65 atividades; LA: <Code>id_setor</Code> = 16, ~30 atividades) — uma
                    atividade nova cadastrada em qualquer um dos dois setores passa a contar automaticamente, sem exigir
                    alteração de código.
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
                    Todas as contagens de processo passam por deduplicação — a query de origem pode gerar mais de uma
                    linha por processo (ex.: mais de uma parte adversa), e isso é corrigido antes de qualquer soma ou
                    contagem.
                </p>
            </DocSection>

            <DocSection
                id="indicadores"
                title="Estoque e extintos"
                subtitle="Os cartões de resumo da seção '01 · Estoque e extintos'"
                icon="barChart"
            >
                <DocGrid>
                    <MetricCard
                        name="Total em recursal"
                        icon="scale"
                        what="Estoque atual na fase Recursal, sem filtro de data."
                        counts="Todo processo da LA com ID_FASE = 8, deduplicado por processo."
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
                        icon="scale"
                        what="Valor de causa/acordo dos processos que entraram na Recursal no período."
                        counts="Soma de VALOR_CAUSA_ACORDO dos processos com entrada no intervalo."
                        calc="Mesma base do cartão anterior — soma em vez de contagem."
                        interpret="Dimensiona financeiramente o fluxo de entrada, não o estoque total."
                    />
                </DocGrid>

                <InfoBox>
                    O painel de <strong>Extintos em 2º grau</strong>, ao lado do gráfico "Recursal por subfases", não lê
                    a base do Recursal (agendamentos/processos na fase 8) — usa a mesma base do dashboard{' '}
                    <strong>Controle de Processos</strong>, incluindo processos <strong>arquivados e suspensos</strong>,
                    não só os ainda ativos na Recursal. Por isso um processo pode aparecer aqui mesmo depois de já ter
                    saído da fase.
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
                        <strong>Improcedente</strong> — incluindo "Improcedente por Prescrição/Decadência" — é o único
                        grupo fora do numerador, mas continua no denominador.
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
                subtitle="Cruzamento sentença × acórdão via Matriz de Julgamento"
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
                    <Code>status_segundo_grau</Code>) para este novo cruzamento por mérito — mesma mudança aplicada ao
                    Recursal NG, no mesmo módulo compartilhado (<Code>matriz_julgamento</Code>). O ID de mérito vem das
                    colunas novas do LexFlow (<Code>id_sentenca_merito_grau1</Code>/<Code>id_acordao_merito_grau2</Code>
                    ) quando preenchidas; quando vazias, é traduzido pelo nome do status antigo — cobertura validada em{' '}
                    {'>'}99,9% de correspondência contra a base histórica. Não há mais diferença de implementação entre
                    NG e LA nesta matriz.
                </DiffBox>
                <p className="muted small">
                    Clicar em uma barra dos gráficos de 1º ou 2º grau, ou em uma célula da matriz (ícone <em>i</em> ao
                    lado do título "Decisões 1º e 2º grau"), aplica o filtro correspondente à página inteira.
                </p>

                <DocCard title="Ranking de Juízes e Relatores">
                    <p>
                        Taxa de sucesso por magistrado — juiz responsável pela sentença (1G) e relator responsável pelo
                        acórdão (2G) — calculada sobre as decisões do período. Clicar em um nome filtra a página inteira
                        por aquele magistrado.
                    </p>
                </DocCard>
            </DocSection>

            <DocSection
                id="distribuicao"
                title="Matérias, competência e vara"
                subtitle="Distribuição do estoque ou da entrada no período, por dimensão"
                icon="barChart"
            >
                <InfoBox>
                    Os três gráficos (matéria, competência e vara) compartilham o mesmo alternador Estoque/Entrada da
                    seção "01 · Estoque e extintos" — Total mostra a distribuição de todo o estoque atual na fase
                    Recursal; Entrada no período restringe aos processos cuja entrada caiu no intervalo selecionado.
                    Clicar numa fatia ou barra filtra a página inteira por aquele valor.
                </InfoBox>
            </DocSection>

            <DocSection
                id="atividades"
                title="Atividades no período (setor RECURSOS)"
                subtitle="KPIs de fila de trabalho e o alternador 'Por prazo / Concluídas'"
                icon="fileText"
            >
                <InfoBox>
                    O alternador <strong>"Por prazo" / "Concluídas"</strong> no cabeçalho da seção troca a base dos 4
                    cartões de KPI sem nenhuma chamada nova à API — o backend já devolve os dois conjuntos de números no
                    mesmo payload, e o frontend só troca qual conjunto é exibido. "Por prazo" (padrão) mostra a fila
                    considerando o prazo de cada tarefa; "Concluídas" mostra a mesma fila considerando o fechamento
                    (Cumprido/Não Cumprido) no período.
                </InfoBox>
                <DocGrid>
                    <MetricCard
                        name="Total / Em andamento / Vencidas / Vencem hoje"
                        icon="clock"
                        what="Volume de tarefas do setor RECURSOS e sua situação de prazo."
                        counts='Total = criadas no período. Em andamento = abertas ("Recebido"/"Visualizado") entre as criadas no período. Vencidas/Vencem hoje comparam o PRAZO com a data de hoje.'
                        calc="Contagens diretas sobre os agendamentos do setor, filtrados pelo catálogo dinâmico de atividades (id_setor = 16)."
                        interpret="Fila de trabalho corrente — não é o mesmo recorte do estoque/entrada da fase Recursal acima."
                    />
                    <MetricCard
                        name="Concluídas"
                        icon="check"
                        what="Tarefas do setor encerradas no período."
                        counts='"Encerrado Cumprido" ou "Encerrado Não Cumprido" com DATA_HORA_CONCLUSAO no período.'
                        calc="Contagem direta dos registros encerrados no período."
                        interpret="Produção de fechamento do setor — é a mesma contagem usada na comparação com relatórios nativos do LexFlow (ex.: filtro de funcionário/período/status)."
                        caveat="A data de fechamento é convertida para o fuso America/Manaus antes de comparar com o período — tarefas fechadas entre 20h e 23h59 (Manaus) já contam no dia correto desde a correção de 15/09/2026."
                    />
                </DocGrid>
                <DiffBox>
                    A LA não tem cartão de <strong>Cancelados</strong> nem seção de <strong>Comissionamento</strong> —
                    ambos existem apenas no Recursal NG, onde há um roster fixo de colaboradores e regras próprias de
                    remuneração por atividade. A LA também não tem <strong>Meta de Provimento Mensal</strong> — a Taxa
                    de Provimento (2º grau) já aparece no painel de Extintos, na seção "01 · Estoque e extintos", mas
                    sem uma meta numérica fixa associada.
                </DiffBox>

                <DocCard title="Gráficos e listas">
                    <ul>
                        <li>
                            <strong>Por atividade</strong>: volume de tarefas por nome de atividade do catálogo dinâmico
                            — clique para filtrar.
                        </li>
                        <li>
                            <strong>Demandas por Funcionário</strong>: empilhado (Cumprido/Não Cumprido), contado por
                            quem <em>encerrou</em> a tarefa (não por quem estava atribuído) — quem executa o fechamento
                            pode divergir do responsável atribuído.
                        </li>
                        <li>
                            <strong>Produção Recursal mês a mês</strong>: histórico de "Encerrado Cumprido" por dia, com
                            drilldown de mês para dia.
                        </li>
                        <li>
                            <strong>Média Resolvidos por Funcionário</strong>: gráfico de metas (bullet chart)
                            comparando a produção de cada colaborador contra uma referência.
                        </li>
                        <li>
                            <strong>Lista de tarefas</strong>: aparece só com pelo menos um filtro de
                            funcionário/atividade ativo — evita carregar uma lista de milhares de linhas sem recorte.
                        </li>
                    </ul>
                </DocCard>
            </DocSection>

            <DocSection id="exportacao" title="Exportação" subtitle="Relatório Personalizado (CSV)" icon="sheet">
                <DocCard title="Relatório Personalizado">
                    <p>
                        Exportação CSV com até 27 campos selecionáveis (identificação, processo, status judicial,
                        valores, datas, atividades), respeitando todos os filtros ativos no dashboard. Módulo genérico,
                        criado originalmente para este dashboard e hoje reutilizado também no Recursal NG.
                    </p>
                </DocCard>
                <p className="muted small">
                    A LA não tem Relatório de Comissão (PDF/CSV) — essa exportação é exclusiva do Recursal NG, por conta
                    da regra de comissionamento própria daquele setor.
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
