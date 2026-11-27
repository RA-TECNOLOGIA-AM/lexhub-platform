import type { ReactNode } from 'react'
import {
    Code,
    DocCallout,
    DocChange,
    DocChips,
    DocFeature,
    DocGrid,
    DocMini,
    DocPage,
    DocSection,
    DocTable,
    Formula,
    Hl,
    MetricCard,
    type Tone,
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

const FILTERS: { name: string; desc: string; badge: string; tone: Tone }[] = [
    {
        name: 'Data',
        desc: 'Período aplicado a entradas, decisões e Meta de Provimento Mensal.',
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

// Os 8 tipos de resultado da Matriz de Julgamento (mesmo texto no Recursal LA).
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
                subtitle="Fase Recursal, escritório NG e o catálogo dinâmico de atividades"
                badge="Catálogo dinâmico"
            >
                <DocFeature
                    title="A base: fase Recursal do NG e o catálogo do setor RECURSOS"
                    tone="accent"
                    icon="layers"
                    badge="Setor 149"
                    framed
                >
                    <p>
                        A base é todo processo do escritório NG (<Code>ID_ESCRITORIO</Code> = 20) atualmente na fase
                        Recursal (<Code>ID_FASE</Code> = 8). Quando o processo tem um agendamento aberto no setor{' '}
                        <strong>RECURSOS</strong> (ids de setor = 149), esse agendamento só é considerado válido se a
                        atividade pertencer ao catálogo do setor — carregado dinamicamente do banco a cada ciclo, não é
                        uma lista fixa no código. Isso significa que uma atividade nova cadastrada no setor aparece
                        automaticamente nos gráficos, sem precisar de deploy.
                    </p>
                </DocFeature>
                <DocCallout tone="violet" icon="layers" title="Diferença para o Recursal LA" badge="Só volume">
                    <p>
                        O Recursal LA usa o mesmo mecanismo de catálogo dinâmico (setor RECURSOS = <Code>id_setor</Code>{' '}
                        16), desde 15/09/2026 — antes disso a LA usava uma lista fixa no código, que ficou desatualizada
                        e fez tarefas de atividades novas ("ELABORAR CONTRARRAZÕES APELAÇÃO", "ELABORAR CONTRARRAZOES
                        INOMINADO", entre outras) sumirem silenciosamente dos KPIs. A diferença que permanece é só de
                        volume: o setor do NG tem 65+ atividades cadastradas, bem mais granular que as ~30 da LA —
                        reflexo de como cada escritório organiza o próprio fluxo de trabalho, não uma diferença de
                        implementação.
                    </p>
                </DocCallout>
                <DocCallout tone="ok" icon="check-circle" title="Cada processo conta uma única vez">
                    <p>
                        Todas as contagens de processo passam por deduplicação (<Code>_deduplicar_por_processo</Code>) —
                        a query de origem pode gerar mais de uma linha por processo (ex.: mais de uma parte adversa), e
                        isso é corrigido antes de qualquer soma ou contagem.
                    </p>
                </DocCallout>
            </DocSection>

            <DocSection
                id="indicadores"
                title="02 — Estoque e entrada"
                subtitle="Os cartões de resumo da seção 'Estoque e extintos'"
                badge="Estoque × período"
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
                        name="Valor dos acórdãos em recursal"
                        icon="dollar"
                        what="Valor de causa/acordo de todo o estoque atual da fase Recursal."
                        counts="Soma de VALOR_CAUSA_ACORDO dos processos hoje com ID_FASE = 8 — estoque atual, sem período."
                        calc='Mesma base do "Total em recursal" — soma em vez de contagem. Na v1 o card se chamava "Valor entrada acórdão Recursal", mas já mostrava este número.'
                        interpret="Dimensiona financeiramente o estoque da fase, não o fluxo de entrada do período."
                    />
                </DocGrid>
            </DocSection>

            <DocSection
                id="extintos-2g"
                title="03 — Extintos em 2º grau"
                subtitle="Com mérito, sem mérito e Taxa de Provimento"
                badge="Base do Controle de Processos"
            >
                <DocCallout tone="warn" icon="alert" title="Base diferente do resto da página">
                    <p>
                        Este painel não lê a base do Recursal (agendamentos/processos na fase 8) — usa a mesma base do
                        dashboard <strong>Controle de Processos</strong> (<Code>controle_processo_todas_situacoes</Code>
                        ), incluindo processos <strong>arquivados e suspensos</strong>, não só os ainda ativos na
                        Recursal. Por isso um processo pode aparecer aqui mesmo depois de já ter saído da fase.
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
                            acórdãos 2G do período (com mérito + sem mérito). <strong>Improcedente</strong> — incluindo,
                            desde a migração, "Improcedente por Prescrição/Decadência" — é o único grupo fora do
                            numerador, mas continua no denominador.
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
                title="04 — Decisões 1º e 2º grau"
                subtitle="Cruzamento sentença × acórdão via Matriz de Classificação"
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
                        /<Code>status_segundo_grau</Code>) para este novo cruzamento por mérito. O ID de mérito vem das
                        colunas novas do LexFlow (<Code>id_sentenca_merito_grau1</Code>/
                        <Code>id_acordao_merito_grau2</Code>) quando preenchidas; quando vazias, é traduzido pelo nome
                        do status antigo — cobertura validada em {'>'}99,9% de correspondência contra a base histórica.
                        É o mesmo módulo (<Code>matriz_julgamento</Code>), compartilhado entre NG e LA — não há mais
                        diferença de implementação entre os dois escritórios nesta matriz.
                    </p>
                </DocChange>
                <p className="muted small">
                    Clicar em uma barra dos gráficos de 1º ou 2º grau, ou em uma célula da matriz (botão "Matriz de
                    classificação" no topo da seção), aplica o filtro correspondente à página inteira.
                </p>
            </DocSection>

            <DocSection
                id="meta-provimento"
                title="05 — Meta de Provimento Mensal"
                subtitle="80 processos providos por mês — e por que a data do acórdão de embargos importa"
                badge="80 / mês"
            >
                <p>
                    Conta processos cujo acórdão de 2º grau caiu em uma das categorias "providas" contra uma meta fixa
                    de <strong>80 processos/mês</strong>.
                </p>
                <DocChips
                    label="Categorias providas:"
                    items={[
                        { label: 'Procedente (COM PE)', tone: 'ok' },
                        { label: 'Parc. Procedente (COM PE)', tone: 'ok' },
                        { label: 'Sentença Anulada', tone: 'info' },
                        { label: 'Procedente (SEM PE)', tone: 'ok' },
                    ]}
                />
                <p>
                    Um medidor (gauge) mostra o percentual atingido, com um marcador em 70%: abaixo de 70% fica
                    vermelho, e ao chegar a 100% muda de cor e ganha o selo "Meta atingida".
                </p>
                <DocGrid cols={2}>
                    <DocFeature
                        title="Data de referência: embargos primeiro"
                        tone="accent"
                        icon="calendar"
                        badge="DATA_ACORDAO_EMBARGOS"
                        framed
                    >
                        <p>
                            A data usada para posicionar o processo no período é <Code>DATA_ACORDAO_EMBARGOS</Code>{' '}
                            quando o processo teve embargos de declaração — é o acórdão dos embargos que define a
                            procedência final, não o acórdão original. Só cai para <Code>DATA_ACORDAO</Code> quando não
                            houve embargos.
                        </p>
                    </DocFeature>
                    <DocChange status="24/08/2026" tone="ok" area="Correção" title="Embargos passam a contar" framed>
                        <p>
                            Corrigido em 24/08/2026: antes, a meta só olhava <Code>DATA_ACORDAO</Code>, ignorando que um
                            novo recurso (embargos) pode mudar a data — e o resultado — da procedência. A mesma regra de
                            prioridade (embargos, com fallback no acórdão original) é usada nesta meta.
                        </p>
                    </DocChange>
                </DocGrid>
                <DocCallout tone="info" icon="dollar" title="Alimenta o comissionamento">
                    <p>
                        Este indicador também alimenta o comissionamento: <Code>meta_qualidade_atingida</Code> (usada no
                        bônus de R$ 200,00 da seção de Comissionamento) é exatamente{' '}
                        <Code>qtd_provimento_mensal ≥ 80</Code> no período selecionado no momento da exportação.
                    </p>
                </DocCallout>
            </DocSection>

            <DocSection
                id="atividades"
                title="06 — Atividades no período (setor RECURSOS)"
                subtitle="KPIs de fila de trabalho, o alternador 'Por prazo / Concluídas' e o cartão 'Cancelados'"
                badge="Por prazo / Concluídas"
            >
                <DocCallout tone="info" icon="refresh" title='Alternador "Por prazo" / "Concluídas"'>
                    <p>
                        O alternador no cabeçalho da seção troca a base dos 5 cartões de KPI (Total, Em andamento,
                        Vencidas, Vencem hoje e Concluídas) sem nenhuma chamada nova à API: o backend já devolve os dois
                        conjuntos de números no mesmo payload, e o frontend só troca qual conjunto é exibido. O cartão
                        "Cancelados" não muda com o alternador. A Meta de Provimento Mensal (ver acima) é renderizada
                        dentro desta mesma seção, logo abaixo dos cartões de KPI.
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
                        calc="Contagens diretas sobre os agendamentos do setor, filtrados pelo catálogo dinâmico de atividades."
                        interpret="Fila de trabalho corrente — não é o mesmo recorte do estoque/entrada da fase Recursal acima."
                    />
                    <MetricCard
                        name="Concluídas"
                        icon="check"
                        what="Tarefas do setor encerradas — a base muda com o alternador."
                        counts='"Encerrado Cumprido" ou "Encerrado Não Cumprido". Na visão Concluídas, com DATA_HORA_CONCLUSAO no período; na visão Por prazo, com PRAZO no período (contagem separada do Total).'
                        calc="Contagem direta dos registros encerrados no período."
                        interpret="Produção de fechamento do setor — mas não confundir com a contagem de erros da Comissão (ver seção abaixo)."
                    />
                    <MetricCard
                        name="Cancelados"
                        icon="ban"
                        what="Casos em que uma tarefa foi encerrada como erro e encaminhada para retrabalho."
                        counts='Tarefa de ORIGEM encerrada como "Cancelado" ou "Encerrado Não Cumprido" com motivo "RECURSO CANCELADO OU ALTERADO" ou "RECURSO ERRADO OU PERDIDO", cujo motivo_encaminhamento aponta para a família AVR-RETORNO ou RETORNO-CR.'
                        calc="Soma get_total_avr_retorno_recurso_cancelado_NG + get_total_retorno_cr_recurso_cancelado_NG, filtrando pela data de conclusão/cancelamento da tarefa de ORIGEM."
                        interpret="Mede quantos casos geraram retrabalho no período — ver o quadro de comparação na seção de Comissão para a diferença em relação à contagem de erros que efetivamente desconta comissão."
                    />
                </DocGrid>
            </DocSection>

            <DocSection
                id="comissao"
                title="07 — Comissionamento"
                subtitle="Quantidade + qualidade − erros, por colaborador do roster fixo"
                tone="ok"
                badge="Revisão manual"
            >
                <DocCallout tone="neutral" icon="users" title="Roster fixo no código" badge="Sem tabela de subsetor">
                    <p>
                        O roster do setor é fixo no código (não vem de uma tabela de "subsetor" — não existe uma no
                        banco). Giovanna aparece nos dois subsetores e comissiona pela atividade que efetivamente
                        concluir — a quantidade é contada pela atividade encerrada, não pelo subsetor da pessoa. Vivian
                        Alessandra Souza Fernandes é a líder do setor e está fora do relatório de comissão desde
                        11/2026.
                    </p>
                    <DocChips
                        label="Análise:"
                        items={[
                            { label: 'Alessandra Souza de Aquino', tone: 'info' },
                            { label: 'Anderton Matheus Aquino dos Santos', tone: 'info' },
                            { label: 'Giovanna Santos Gualberto da Costa', tone: 'violet' },
                        ]}
                    />
                    <DocChips
                        label="Confecção:"
                        items={[
                            { label: 'Giovanna Santos Gualberto da Costa', tone: 'violet' },
                            { label: 'Bárbara Vitória Arirama Bezerra', tone: 'accent' },
                            { label: 'Isa Fernanda Morais da Silva Sousa', tone: 'accent' },
                            { label: 'Náthaly Blanca Nunes de Sousa', tone: 'accent' },
                        ]}
                    />
                </DocCallout>

                <DocFeature title="Quantidade" tone="ok" icon="plus" badge="Por atividade">
                    <DocTable
                        head={['Subsetor', 'Valor', 'Conta quando']}
                        rows={[
                            [
                                'Análise',
                                <Hl key="v" tone="ok">
                                    R$ 0,50 / atividade
                                </Hl>,
                                <>
                                    "Encerrado Cumprido" <strong>ou</strong> "Encerrado Não Cumprido" — a análise de
                                    viabilidade é remunerada independente do resultado. Inclui "Análise Sentença -
                                    Embargos".
                                </>,
                            ],
                            [
                                'Confecção',
                                <Hl key="v" tone="ok">
                                    R$ 2,00 / atividade
                                </Hl>,
                                'Só "Encerrado Cumprido" — remunera o recurso de fato interposto.',
                            ],
                        ]}
                    />
                </DocFeature>

                <DocFeature
                    title="Erros — contagem direta na própria atividade de retorno"
                    tone="danger"
                    icon="minus"
                    badge="Desconto"
                >
                    <p>
                        Cada fechamento (Cumprido <em>ou</em> Não Cumprido, no período) da própria atividade{' '}
                        <strong>AVR-RETORNO</strong> (qualquer variante da família) conta{' '}
                        <strong>1 erro de Análise</strong>, atribuído a quem estava atribuído àquela tarefa de retorno —
                        não a quem cometeu o erro na tarefa que a originou. O mesmo vale para{' '}
                        <strong>RETORNO-CR</strong>, contando 1 erro de Confecção.
                    </p>
                    <DocTable
                        head={['Retorno', 'Subsetor descontado', 'Desconto']}
                        rows={[
                            [
                                'AVR-RETORNO — texto do fechamento contém "ALTERADO"',
                                'Análise',
                                <Hl key="v" tone="danger">
                                    R$ 0,50
                                </Hl>,
                            ],
                            [
                                'AVR-RETORNO — demais casos (inclusive sem texto)',
                                'Análise',
                                <Hl key="v" tone="danger">
                                    R$ 1,00
                                </Hl>,
                            ],
                            [
                                'RETORNO-CR — qualquer fechamento',
                                'Confecção',
                                <Hl key="v" tone="danger">
                                    R$ 4,00 (fixo)
                                </Hl>,
                            ],
                        ]}
                    />
                </DocFeature>

                <DocCallout tone="warn" icon="alert" title="Revisar antes de fechar a folha">
                    <p>
                        Levantamento de casos históricos mostrou que a maioria dos fechamentos de retorno tem uma causa{' '}
                        <em>não</em> imputável ao colaborador — renúncia do cliente, ausência em audiência sem
                        justificativa, trânsito em julgado, entre outras. O sistema não distingue isso automaticamente
                        com segurança, então a decisão foi: sempre aplicar o desconto pela regra acima,{' '}
                        <strong>mas mostrar o texto do motivo de cada desconto no relatório</strong> para o líder
                        decidir manualmente se ele deve ser mantido ou revertido antes de fechar a folha do mês.
                    </p>
                </DocCallout>

                <DocGrid cols={2}>
                    <DocFeature title="Meta batida" tone="ok" icon="target" badge="R$ 200,00" framed>
                        <p>
                            Para <strong>todo</strong> colaborador do roster, se a Meta de Provimento Mensal (80/mês)
                            foi atingida no período selecionado.
                        </p>
                    </DocFeature>
                    <DocFeature title="Zero retrabalho" tone="ok" icon="star" badge="R$ 100,00" framed>
                        <p>
                            Individual — só para quem não teve <strong>nenhum</strong> erro (Análise + Confecção) no
                            mês.
                        </p>
                    </DocFeature>
                </DocGrid>

                <DocFeature title="Fórmula do total por colaborador" tone="accent" icon="dollar">
                    <Formula>
                        total = (qtd_análise × R$0,50) + (qtd_confecção × R$2,00) − desconto_análise −
                        desconto_confecção + bônus_meta + bônus_zero_retrabalho
                    </Formula>
                </DocFeature>

                <DocCallout tone="violet" icon="layers" title='Não confundir com o cartão "Cancelados" da seção 06'>
                    <p>
                        Aquele cartão conta pelo <em>destino</em> apontado no <Code>motivo_encaminhamento</Code> da
                        tarefa de <em>origem</em> — é uma visão de fluxo de trabalho, para saber quantos casos foram
                        encaminhados para retrabalho. A comissão conta os{' '}
                        <em>fechamentos da própria atividade de retorno</em>, atribuídos a quem executou o retorno — é a
                        visão de responsabilidade individual que efetivamente desconta em reais. Os dois números podem —
                        e costumam — divergir. Validado com dados reais de agosto/2026: 1 fechamento de RETORNO-CR no
                        mês (Bárbara Vitória Arirama Bezerra, R$ 4,00) e 19 fechamentos de AVR-RETORNO (1 deles
                        identificado como "Recurso Alterado", R$ 0,50; os demais a R$ 1,00).
                    </p>
                </DocCallout>
            </DocSection>

            <DocSection
                id="exportacao"
                title="08 — Exportação"
                subtitle="Relatório Personalizado (CSV/XLSX) e Relatório de Comissão (PDF)"
            >
                <DocGrid cols={2}>
                    <DocFeature title="Relatório Personalizado" tone="info" icon="sheet" badge="CSV / XLSX" framed>
                        <p>
                            Exportação com até 28 campos selecionáveis (identificação, processo, status judicial,
                            valores, datas, atividades). Leva os filtros da página, <strong>menos</strong> Extintos 2º
                            grau, Funcionário e Situação (Atividades) e o período — como na janela da v1. Módulo
                            genérico, o mesmo do Recursal LA.
                        </p>
                    </DocFeature>
                    <DocFeature title="Relatório de Comissão" tone="ok" icon="file-down" badge="PDF" framed>
                        <p>
                            PDF com o resumo por colaborador (quantidade, bônus, descontos, total) e uma segunda tabela
                            de detalhamento — uma linha por desconto de erro, com o texto do motivo do fechamento, para
                            a revisão manual descrita na seção de Comissionamento.
                        </p>
                    </DocFeature>
                </DocGrid>
                <p className="muted small">
                    Na V2 a comissão vem no próprio retorno do dashboard (período da página e filtro de funcionário), só
                    para quem pode ver comissão, e o PDF é montado no navegador — não há mais um endpoint próprio de
                    exportação da comissão como o <Code>GET /recursal_NG/comissao/export</Code> da v1.
                </p>
            </DocSection>

            <DocSection id="filtros" title="09 — Filtros disponíveis" subtitle="Como personalizar a página inteira">
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
