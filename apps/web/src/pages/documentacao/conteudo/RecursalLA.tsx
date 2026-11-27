import type { ReactNode } from 'react'
import {
    Code,
    DocCallout,
    DocChange,
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

const FILTERS: { name: string; desc: string; badge: string; tone: Tone }[] = [
    {
        name: 'Data',
        desc: 'Período aplicado a entradas, decisões e atividades do setor.',
        badge: 'Calendário',
        tone: 'accent',
    },
    {
        name: '1º grau / 2º grau',
        desc: 'Status de sentença/acórdão — clicável direto nos gráficos.',
        badge: 'Clique no gráfico',
        tone: 'info',
    },
    {
        name: 'Decisão',
        desc: 'Um dos 8 tipos da Matriz de Julgamento — clicável nos cartões ou na matriz.',
        badge: 'Cartões / matriz',
        tone: 'info',
    },
    {
        name: 'Juiz / Relator',
        desc: 'Filtra pelo ranking de magistrados correspondente.',
        badge: 'Ranking',
        tone: 'violet',
    },
    {
        name: 'Matéria / Competência / Vara / Subfase',
        desc: 'Distribuição da fase Recursal — clicável nos gráficos de pizza/barras.',
        badge: 'Clique no gráfico',
        tone: 'info',
    },
    {
        name: 'Extinto 2º grau',
        desc: 'Com mérito ou sem mérito, no painel de Extintos.',
        badge: 'Painel de Extintos',
        tone: 'warn',
    },
    {
        name: 'Funcionário / Atividade',
        desc: 'Restringe a lista de tarefas do setor RECURSOS e os gráficos de produção.',
        badge: 'Setor RECURSOS',
        tone: 'ok',
    },
    {
        name: 'Situação / Status (Atividades)',
        desc: 'Situação calculada (em andamento, vencida…) e status bruto das tarefas do setor RECURSOS.',
        badge: 'Setor RECURSOS',
        tone: 'ok',
    },
    {
        name: 'Situação do processo',
        desc: 'Ativo, Suspenso/Sobrestado ou Arquivado — a situação do processo, não da tarefa.',
        badge: 'Processo',
        tone: 'neutral',
    },
]

// Os 8 tipos de resultado da Matriz de Julgamento (mesmo texto no Recursal NG).
const RESULTADOS: { name: string; tone: Tone; desc: ReactNode }[] = [
    { name: 'Mantido Ganho', tone: 'ok', desc: '1G e 2G no mesmo patamar de procedência.' },
    { name: 'Ganho Ampliado', tone: 'ok', desc: '2G reconhece mais do que o 1G havia dado.' },
    { name: 'Revertido Ganho', tone: 'ok', desc: '1G improcedente/extinto, 2G reverte para procedente.' },
    { name: 'Ganho Reduzido', tone: 'warn', desc: '2G reconhece menos do que o 1G.' },
    { name: 'Extinção (Permite Reajuizar)', tone: 'warn', desc: '2G extingue sem mérito.' },
    {
        name: 'Instrução Retomada',
        tone: 'info',
        desc: '2G anula a sentença (Sentença Anulada), processo volta à instrução.',
    },
    { name: 'Mantido Perda', tone: 'danger', desc: '1G e 2G ambos improcedentes.' },
    {
        name: 'Revertido Perda',
        tone: 'danger',
        desc: '1G procedente (ou extinto sem mérito), 2G reverte para improcedente.',
    },
]

const GRAFICOS: { name: string; desc: ReactNode; badge?: string }[] = [
    {
        name: 'Por atividade',
        desc: 'Volume de tarefas por nome de atividade do catálogo dinâmico — clique para filtrar.',
        badge: 'Clique para filtrar',
    },
    {
        name: 'Demandas por Funcionário',
        desc: (
            <>
                Empilhado (Cumprido/Não Cumprido), contado por quem <em>encerrou</em> a tarefa (não por quem estava
                atribuído) — quem executa o fechamento pode divergir do responsável atribuído.
            </>
        ),
        badge: 'Quem encerrou',
    },
    {
        name: 'Produção Recursal mês a mês',
        desc: 'Histórico de "Encerrado Cumprido" por dia, com drilldown de mês para dia.',
        badge: 'Mês → dia',
    },
    {
        name: 'Média Resolvidos por Funcionário',
        desc: 'Barras simples com a média de tarefas cumpridas por dia com conclusão, por colaborador, no período.',
        badge: 'Barras',
    },
    {
        name: 'Lista de tarefas',
        desc: 'Sempre aparece, paginada. Com filtro de funcionário, atividade, status ou situação ativo, a legenda avisa que a lista está filtrada.',
        badge: 'Paginada',
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
            header={
                <DocCallout caps title="Estoque × Entrada" badge="ID_FASE = 8">
                    <p>
                        Os gráficos de distribuição (subfase, matéria, competência, vara) têm um alternador que troca a
                        base de cálculo:
                    </p>
                    <DocGrid cols={2}>
                        <DocMini label="Total (estoque)">
                            Todo processo com <Hl mono>ID_FASE</Hl> = 8 hoje, sem filtro de data — "quanto está parado
                            na Recursal agora".
                        </DocMini>
                        <DocMini label="Entrada no período">
                            Processos cuja{' '}
                            <Hl tone="info" mono>
                                DT_ENTRADA_RECURSAL
                            </Hl>{' '}
                            cai dentro do período selecionado — "quanto chegou na Recursal nesse intervalo".
                        </DocMini>
                    </DocGrid>
                </DocCallout>
            }
        >
            <DocSection
                id="como-funciona"
                title="01 — Como o dashboard funciona"
                subtitle="Fase Recursal, escritório LA e o catálogo dinâmico de atividades"
                badge="Catálogo dinâmico"
            >
                <DocFeature
                    title="A base: fase Recursal da LA e o catálogo do setor RECURSOS"
                    tone="accent"
                    icon="layers"
                    badge="Setor 16"
                    framed
                >
                    <p>
                        A base é todo processo do escritório LA (Luis Albert) atualmente na fase Recursal (
                        <Code>ID_FASE</Code> = 8). Quando o processo tem um agendamento aberto no setor{' '}
                        <strong>RECURSOS</strong> (<Code>id_setor</Code> = 16), esse agendamento só é considerado válido
                        se a atividade pertencer ao catálogo do setor — carregado dinamicamente do banco a cada ciclo,
                        não é uma lista fixa no código. Isso significa que uma atividade nova cadastrada no setor
                        aparece automaticamente nos gráficos, sem precisar de deploy.
                    </p>
                </DocFeature>
                <DocChange status="15/09/2026" tone="ok" area="Correção" title="Catálogo de atividades dinâmico">
                    <p>
                        Corrigido em 15/09/2026: até então, o catálogo de atividades do setor RECURSOS (LA) era uma
                        lista fixa no código (28 atividades), diferente do NG (que já era dinâmico). Essa lista ficou
                        desatualizada e fez tarefas de atividades novas — "ELABORAR CONTRARRAZÕES APELAÇÃO", "ELABORAR
                        CONTRARRAZOES INOMINADO", "DILIGÊNCIA HT/NHT" e "REVISAR MEMORIAIS HT/NHT" — sumirem
                        silenciosamente dos KPIs e gráficos, mesmo estando ativas no LexFlow. Achado ao investigar uma
                        divergência real: o dashboard mostrava 140 tarefas encerradas por uma funcionária num período em
                        que o relatório nativo do LexFlow mostrava 149. Agora os dois escritórios usam o mesmo mecanismo
                        dinâmico (NG: <Code>id_setor</Code> = 149, ~65 atividades; LA: <Code>id_setor</Code> = 16, ~30
                        atividades) — uma atividade nova cadastrada em qualquer um dos dois setores passa a contar
                        automaticamente, sem exigir alteração de código.
                    </p>
                </DocChange>
                <DocCallout tone="ok" icon="check-circle" title="Cada processo conta uma única vez">
                    <p>
                        Todas as contagens de processo passam por deduplicação — a query de origem pode gerar mais de
                        uma linha por processo (ex.: mais de uma parte adversa), e isso é corrigido antes de qualquer
                        soma ou contagem.
                    </p>
                </DocCallout>
            </DocSection>

            <DocSection
                id="indicadores"
                title="02 — Estoque e extintos"
                subtitle="Os cartões de resumo da seção 'Estoque e extintos' do dashboard"
                badge="Estoque × período"
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
                        name="Valor dos acórdãos em recursal"
                        icon="dollar"
                        what="Valor de causa/acordo de todo o estoque atual da fase Recursal."
                        counts="Soma de VALOR_CAUSA_ACORDO dos processos hoje com ID_FASE = 8 — estoque atual, sem período."
                        calc='Mesma base do "Total em recursal" — soma em vez de contagem. Na v1 o card se chamava "Valor entrada acórdão Recursal", mas já mostrava este número.'
                        interpret="Dimensiona financeiramente o estoque da fase, não o fluxo de entrada do período."
                    />
                </DocGrid>

                <DocCallout tone="warn" icon="alert" title="Extintos em 2º grau: base diferente do resto da página">
                    <p>
                        O painel de <strong>Extintos em 2º grau</strong>, ao lado do gráfico "Recursal por subfases",
                        não lê a base do Recursal (agendamentos/processos na fase 8) — usa a mesma base do dashboard{' '}
                        <strong>Controle de Processos</strong>, incluindo processos{' '}
                        <strong>arquivados e suspensos</strong>, não só os ainda ativos na Recursal. Por isso um
                        processo pode aparecer aqui mesmo depois de já ter saído da fase.
                    </p>
                </DocCallout>
                <DocGrid>
                    <MetricCard
                        name="Extintos com mérito (2º grau)"
                        icon="scale"
                        what="Processos cujo acórdão de 2º grau é uma decisão de mérito."
                        counts="Todo ID de mérito do 2G (esquema novo, 1-8) exceto Extinto Sem Mérito (7)."
                        calc="Contagem e soma de VALOR_CAUSA_ACORDO filtrando DATA_ACORDAO no período."
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
                <DocGrid cols={2}>
                    <DocFeature title="De onde vem o ID de mérito" tone="info" icon="db" badge="15/09/2026">
                        <p>
                            O "ID de mérito" vem da coluna nova <Code>id_acordao_merito_grau2</Code> quando preenchida;
                            quando vazia, é traduzido pelo nome do status antigo (<Code>status_segundo_grau</Code>) para
                            o ID equivalente no esquema novo — mesma lógica em toda a Matriz de Julgamento (ver seção
                            "Decisões 1º e 2º grau" abaixo). Migrado de <Code>ID_2G</Code> bruto para esse esquema em
                            15/09/2026.
                        </p>
                    </DocFeature>
                    <DocFeature title="Taxa de Provimento (2º grau)" tone="ok" icon="percent" badge="positivos ÷ total">
                        <Formula>positivos / total × 100</Formula>
                        <p>
                            <strong>Positivos</strong> = procedente, parcialmente procedente (com ou sem proveito
                            econômico), sentença anulada e extinto sem mérito; <strong>total</strong> = todos os
                            acórdãos 2G do período (com mérito + sem mérito). <strong>Improcedente</strong> — incluindo
                            "Improcedente por Prescrição/Decadência" — é o único grupo fora do numerador, mas continua
                            no denominador.
                        </p>
                    </DocFeature>
                </DocGrid>
                <DocCallout tone="violet" icon="dollar" title="Diferença para o Controle de Processos">
                    <p>
                        A coluna de valor aqui é <Code>VALOR_CAUSA_ACORDO</Code> (valor do acordo/decisão), diferente do
                        painel equivalente em Controle de Processos, que soma <Code>VALOR_DE_CAUSA</Code> (valor de
                        causa inicial) — mesma base de processos, coluna de dinheiro diferente porque respondem
                        perguntas diferentes.
                    </p>
                </DocCallout>
            </DocSection>

            <DocSection
                id="decisoes"
                title="03 — Decisões 1º e 2º grau"
                subtitle="Cruzamento sentença × acórdão via Matriz de Julgamento"
                badge="Clique para filtrar"
            >
                <p>
                    Os dois gráficos horizontais ("1º grau" e "2º grau") mostram a contagem bruta por status, filtrando
                    por <Hl mono>DATA_SENTENCA</Hl> (1G) ou <Hl mono>DATA_ACORDAO</Hl> (2G) no período. Os cartões de
                    "Decisões" acima deles já aplicam o cruzamento — a <strong>Matriz de Julgamento</strong>, que
                    combina o mérito de 1G com o de 2G para chegar a um dos 8 tipos de resultado ("Resultado Mapeado").
                </p>
                <DocGrid cols={2}>
                    {RESULTADOS.map((r) => (
                        <DocFeature key={r.name} title={r.name} tone={r.tone}>
                            <p>{r.desc}</p>
                        </DocFeature>
                    ))}
                </DocGrid>
                <DocCallout tone="info" icon="scale" title="Escala de mérito do esquema novo" badge="7 × 9">
                    <p>
                        <strong>1º grau</strong> tem 7 valores (Procedente Com/Sem PE, Parc. Procedente Com/Sem PE,
                        Improcedente, Improcedente por Prescrição/Decadência, Extinto Sem Mérito).{' '}
                        <strong>2º grau</strong> tem os mesmos 7 + <strong>Sentença Anulada</strong> (exclusivo do 2G).
                        A matriz cruza as 7 linhas (1G) × 9 colunas (2G, incluindo "sem recurso" quando não há acórdão)
                        definidas na planilha "Matriz de Julgamento — 1º x 2º Grau". A janela "Matriz de classificação"
                        da tela mostra só as 7 × 8 combinações com acórdão — a coluna "sem recurso" não aparece nela.
                    </p>
                </DocCallout>
                <DocChange status="15/09/2026" tone="neutral" area="Histórico" title="Migração do esquema antigo">
                    <p>
                        Migrado em 15/09/2026 do esquema antigo (10 tipos, baseados em <Code>status_primeiro_grau</Code>
                        /<Code>status_segundo_grau</Code>) para este novo cruzamento por mérito — mesma mudança aplicada
                        ao Recursal NG, no mesmo módulo compartilhado (<Code>matriz_julgamento</Code>). O ID de mérito
                        vem das colunas novas do LexFlow (<Code>id_sentenca_merito_grau1</Code>/
                        <Code>id_acordao_merito_grau2</Code>) quando preenchidas; quando vazias, é traduzido pelo nome
                        do status antigo — cobertura validada em {'>'}99,9% de correspondência contra a base histórica.
                        Não há mais diferença de implementação entre NG e LA nesta matriz.
                    </p>
                </DocChange>
                <p className="muted small">
                    Clicar em uma barra dos gráficos de 1º ou 2º grau, ou em uma célula da matriz (botão "Matriz de
                    classificação" no cabeçalho da seção), aplica o filtro correspondente à página inteira.
                </p>
                <DocFeature title="Ranking de Juízes e Relatores" tone="violet" icon="users" badge="Clique no nome">
                    <p>
                        Taxa de sucesso por magistrado — juiz responsável pela sentença (1G) e relator responsável pelo
                        acórdão (2G) — calculada sobre as decisões do período. Clicar em um nome filtra a página inteira
                        por aquele magistrado.
                    </p>
                </DocFeature>
            </DocSection>

            <DocSection
                id="distribuicao"
                title="04 — Matérias, competência e vara"
                subtitle="Distribuição do estoque ou da entrada no período, por dimensão"
                badge="Estoque / Entrada"
            >
                <DocCallout tone="info" icon="pieChart" title="Alternador próprio de Estoque/Entrada">
                    <p>
                        Os três gráficos (matéria, competência e vara) compartilham um alternador Estoque/Entrada
                        próprio, independente do alternador do gráfico "Recursal por subfases" (seção 02 — Estoque e
                        extintos). Total mostra a distribuição de todo o estoque atual na fase Recursal; Entrada no
                        período restringe aos processos cuja entrada caiu no intervalo selecionado. Clicar numa fatia ou
                        barra filtra a página inteira por aquele valor.
                    </p>
                </DocCallout>
            </DocSection>

            <DocSection
                id="atividades"
                title="05 — Atividades no período (setor RECURSOS)"
                subtitle="KPIs de fila de trabalho e o alternador 'Por prazo / Concluídas'"
                badge="Por prazo / Concluídas"
            >
                <DocCallout tone="info" icon="refresh" title='Alternador "Por prazo" / "Concluídas"'>
                    <p>
                        O alternador no cabeçalho da seção troca a base dos 5 cartões de KPI (Total, Em andamento,
                        Vencidas, Vencem hoje e Concluídas) sem nenhuma chamada nova à API — o backend já devolve os
                        dois conjuntos de números no mesmo payload, e o frontend só troca qual conjunto é exibido.
                    </p>
                    <DocGrid cols={2}>
                        <DocMini label="Por prazo (padrão)">Mostra a fila considerando o prazo de cada tarefa.</DocMini>
                        <DocMini label="Concluídas">
                            Mostra a mesma fila considerando o fechamento (Cumprido/Não Cumprido) no período.
                        </DocMini>
                    </DocGrid>
                </DocCallout>
                <DocGrid>
                    <MetricCard
                        name="Total / Em andamento / Vencidas / Vencem hoje"
                        icon="clock"
                        what="Volume de tarefas do setor RECURSOS e sua situação de prazo — a base muda com o alternador."
                        counts='Por prazo (padrão): Total = abertas ("Recebido"/"Visualizado") com PRAZO no período; Em andamento = o mesmo que Total; Vencidas/Vencem hoje = abertas com PRAZO no período antes de hoje / igual a hoje. Concluídas: Total = criadas no período; Em andamento = abertas entre as criadas no período; Vencidas/Vencem hoje comparam o PRAZO com a data de hoje.'
                        calc="Contagens diretas sobre os agendamentos do setor, filtrados pelo catálogo dinâmico de atividades (id_setor = 16)."
                        interpret="Fila de trabalho corrente — não é o mesmo recorte do estoque/entrada da fase Recursal acima."
                    />
                    <MetricCard
                        name="Concluídas"
                        icon="check"
                        what="Tarefas do setor encerradas — a base muda com o alternador."
                        counts='"Encerrado Cumprido" ou "Encerrado Não Cumprido". Na visão Concluídas, com DATA_HORA_CONCLUSAO no período; na visão Por prazo, com PRAZO no período (contagem separada do Total).'
                        calc="Contagem direta dos registros encerrados no período."
                        interpret="Produção de fechamento do setor — é a mesma contagem usada na comparação com relatórios nativos do LexFlow (ex.: filtro de funcionário/período/status)."
                        caveat="Datas com fuso são convertidas para America/Manaus antes de comparar com o período — tarefas fechadas entre 20h e 23h59 (Manaus) contam no dia local correto. A regra é geral, vale para todos os dashboards (NG inclusive); datas sem fuso ficam como vieram."
                    />
                </DocGrid>
                <DocCallout tone="violet" icon="layers" title="Diferença para o Recursal NG" badge="Sem comissão">
                    <p>
                        A LA não tem cartão de <strong>Cancelados</strong> nem seção de <strong>Comissionamento</strong>{' '}
                        — ambos existem apenas no Recursal NG, onde há um roster fixo de colaboradores e regras próprias
                        de remuneração por atividade. A LA também não tem <strong>Meta de Provimento Mensal</strong> — a
                        Taxa de Provimento (2º grau) já aparece no painel de Extintos, na seção 02 — Estoque e extintos,
                        mas sem uma meta numérica fixa associada.
                    </p>
                </DocCallout>

                <DocGrid cols={2}>
                    {GRAFICOS.map((g) => (
                        <DocFeature key={g.name} title={g.name} tone="info" badge={g.badge} badgeMono={false}>
                            <p>{g.desc}</p>
                        </DocFeature>
                    ))}
                </DocGrid>
            </DocSection>

            <DocSection id="exportacao" title="06 — Exportação" subtitle="Relatório Personalizado (CSV/XLSX)">
                <DocFeature title="Relatório Personalizado" tone="info" icon="sheet" badge="CSV / XLSX" framed>
                    <p>
                        Exportação com até 28 campos selecionáveis (identificação, processo, status judicial, valores,
                        datas, atividades). Leva os filtros da página, <strong>menos</strong> Extintos 2º grau,
                        Funcionário e Situação (Atividades) e o período — como na janela da v1. Módulo genérico, criado
                        originalmente para este dashboard e hoje reutilizado também no Recursal NG.
                    </p>
                </DocFeature>
                <p className="muted small">
                    A LA não tem Relatório de Comissão (PDF/CSV) — essa exportação é exclusiva do Recursal NG, por conta
                    da regra de comissionamento própria daquele setor.
                </p>
            </DocSection>

            <DocSection id="filtros" title="07 — Filtros disponíveis" subtitle="Como personalizar a página inteira">
                <DocGrid cols={2}>
                    {FILTERS.map((f) => (
                        <DocFeature key={f.name} title={f.name} tone={f.tone} badge={f.badge} badgeMono={false}>
                            <p>{f.desc}</p>
                        </DocFeature>
                    ))}
                </DocGrid>
                <DocCallout tone="info" icon="filter" title='Os filtros se combinam em "E"'>
                    <p>
                        Ao clicar num gráfico para filtrar sua própria dimensão, a API é chamada sem esse filtro
                        específico (os demais permanecem), para que a barra/fatia clicada continue visível como opção.
                    </p>
                </DocCallout>
            </DocSection>
        </DocPage>
    )
}
