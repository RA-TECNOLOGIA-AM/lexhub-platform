import type { ReactNode } from 'react'
import {
    Code,
    DocCallout,
    DocChange,
    DocFeature,
    DocGrid,
    DocLink,
    DocMini,
    DocPage,
    DocPill,
    DocSection,
    DocTable,
    Hl,
    type Tone,
    type TocItem,
} from '../components/DocParts.tsx'

// Guia do Julgados Acórdãos: um só para NG, LA e RJ (o cálculo é o mesmo; muda o escritório e o bloco STJ/STF do NG).
// Texto da v1: LexHub/src/pages/documentacao/JulgadosAcordao.tsx, conferido com o cálculo copiado da v1
// (apps/api/src/app/analyses/{NG,LA,RJ}/julgados_acordao*.py e common/matriz_julgamento.py).

const TOC: TocItem[] = [
    { id: 'visao-geral', label: 'Visão geral' },
    { id: 'classificacao', label: 'Classificação de mérito' },
    { id: 'filtros', label: 'Filtros interativos' },
    { id: 'motivo-extincao', label: 'Motivo das extinções' },
    { id: 'nao-classificados', label: 'Não classificados' },
    { id: 'embargos', label: 'Embargos e reversão' },
    { id: 'ranking', label: 'Ranking de Relatores' },
    { id: 'exportacao', label: 'Exportação de relatório' },
    { id: 'notas', label: 'Notas e pendências' },
]

// Unidade, escritório, eixo de data, tabela de mérito e módulo de cálculo (app/analyses/).
const UNIDADES: { unit: string; office: string; module: string }[] = [
    { unit: 'NG', office: '20', module: 'NG/julgados_acordao.py' },
    { unit: 'LA', office: '21', module: 'LA/julgados_acordao_LA.py' },
    { unit: 'RJ', office: '27', module: 'RJ/julgados_acordao_RJ.py' },
]

// Dimensão, parâmetro na URL e onde se clica.
const FILTROS: string[][] = [
    ['Matéria', 'materia_julgados', 'gráfico de pizza'],
    ['Relator (2G)', 'relator_julgados', 'ranking'],
    ['Comarca', 'comarca_julgados', 'barra'],
    ['Competência', 'competencia_julgados', 'barra'],
    ['Categoria', 'categoria_julgados', 'cards de Procedentes / Improcedentes / Extintos'],
    ['UF', 'uf_julgados', 'seletor no cabeçalho'],
    ['Motivo da extinção', 'motivo_extincao_julgados', 'barra (só extintos)'],
    ['Ano de ajuizamento', 'ano_ajuizamento_julgados', 'donut'],
    ['Resultado dos embargos', 'resultado_embargos_julgados', 'pizza (ver Embargos e reversão)'],
]

// Escala de mérito 2G: valor, descrição e categoria (null = não classificado).
const MERITO: { id: string; label: string; cat: string | null; only2g?: boolean }[] = [
    { id: '1', label: 'Procedente com proveito econômico', cat: 'Procedente' },
    { id: '2', label: 'Procedente sem proveito econômico', cat: 'Procedente' },
    { id: '3', label: 'Parc. procedente com proveito econômico', cat: 'Procedente' },
    { id: '4', label: 'Parc. procedente sem proveito econômico', cat: 'Procedente' },
    { id: '5', label: 'Improcedente', cat: 'Improcedente' },
    { id: '6', label: 'Improcedente por prescrição/decadência', cat: 'Improcedente' },
    { id: '7', label: 'Extinto sem mérito', cat: 'Extinto' },
    { id: '8', label: 'Sentença anulada', cat: null, only2g: true },
]

const CAT_TONE: Record<string, Tone> = { Procedente: 'ok', Improcedente: 'danger', Extinto: 'warn' }

const REVISAR = '⚠ Revisar Classificação'

// Cor de cada Status Resultante na matriz dos embargos.
const STATUS_TONE: Record<string, Tone> = {
    'Revertido Ganho': 'ok',
    'Ganho Ampliado': 'ok',
    'Ganho Reduzido': 'info',
    'Status Mantido': 'neutral',
    'Revertido Perda': 'danger',
    [REVISAR]: 'warn',
}

// Matriz do Status Resultante dos embargos (mj.classificar_status_embargos).
const MATRIZ_EMBARGOS: string[][] = [
    ['Procedente (com ou sem PE)', 'Reverteu Procedência', REVISAR],
    ['', 'Reverteu Improcedência', 'Revertido Perda'],
    ['', 'Aumentou a Condenação', 'Ganho Ampliado'],
    ['', 'Reduziu a Condenação', 'Ganho Reduzido'],
    ['Parcialmente procedente', 'Reverteu Procedência', 'Ganho Ampliado'],
    ['', 'Reverteu Improcedência', 'Revertido Perda'],
    ['', 'Aumentou a Condenação', 'Ganho Ampliado'],
    ['', 'Reduziu a Condenação', 'Ganho Reduzido'],
    ['Improcedente / prescrição', 'Reverteu Procedência', 'Revertido Ganho'],
    ['', 'Reverteu Improcedência', REVISAR],
    ['', 'Aumentou a Condenação', REVISAR],
    ['', 'Reduziu a Condenação', REVISAR],
    ['Qualquer mérito', 'Pendência Saneada / Prejudicados / Rejeitados / Não Conhecidos', 'Status Mantido'],
    ['Extinto, Sentença Anulada ou sem mérito', 'Demais resultados', REVISAR],
]

const MATRIZ_ROWS: ReactNode[][] = MATRIZ_EMBARGOS.map(([vigente, resultado, status]) => [
    vigente ? <strong key="v">{vigente}</strong> : '',
    resultado,
    <DocPill key="s" tone={STATUS_TONE[status] ?? 'neutral'}>
        {status}
    </DocPill>,
])

// Âncora para outra seção deste guia.
function Secao({ id, children }: { id: string; children: ReactNode }) {
    return (
        <a className="doc-link" href={`#${id}`}>
            {children}
        </a>
    )
}

export function JulgadosAcordaosDoc() {
    return (
        <DocPage
            title="Julgados — Acórdãos"
            tags={['NG', 'LA', 'RJ']}
            note="Mesmo cálculo nas três unidades, 1 query só"
            toc={TOC}
            intro={
                <>
                    Como o dashboard de Acórdãos (2º grau) classifica um resultado pela Matriz de Julgamento (mérito),
                    por que só o Acórdão tem um card "Não classificados", como calcula o ranking de relatores e o
                    resultado dos embargos, e de onde vem o nome do relator. A lógica é a mesma no NG, no LA e no RJ —
                    muda só o escritório de origem dos dados (e o bloco de recursos ao STJ/STF, que só existe no NG).
                </>
            }
            header={
                <DocCallout caps title="Uma query, três unidades" badge="DATA_ACORDAO">
                    <p>
                        As três unidades usam o mesmo eixo de data (<Hl mono>DATA_ACORDAO</Hl>) e a mesma tabela de
                        mérito (
                        <Hl tone="info" mono>
                            acordao_merito_segundo_grau
                        </Hl>
                        ); muda o escritório e o módulo de cálculo:
                    </p>
                    <DocGrid cols={3}>
                        {UNIDADES.map((u) => (
                            <DocMini key={u.unit} label={`${u.unit} · escritório ${u.office}`}>
                                <Code>{u.module}</Code>
                            </DocMini>
                        ))}
                    </DocGrid>
                </DocCallout>
            }
        >
            <DocSection
                id="visao-geral"
                title="01 — Visão geral"
                subtitle="Um dashboard em cada unidade (NG, LA e RJ), uma query só por trás de todos"
                badge="NG · LA · RJ"
            >
                <DocCallout icon="db" title="O recorte por escritório é feito depois da query">
                    <p>
                        A query <Code>julgados</Code> (na v1, compartilhada também com os dashboards de Sentenças) traz
                        processos de <strong>todos os escritórios</strong> — não tem filtro de escritório no SQL. O
                        recorte por escritório (NG = 20, LA = 21, RJ = 27) é feito depois, em Python, por{' '}
                        <Code>_base_julgados_NG()</Code> / <Code>_base_julgados_LA()</Code> /{' '}
                        <Code>_base_julgados_RJ()</Code> — uma função por módulo, chamada dentro de cada
                        KPI/ranking/gráfico. Na tela, LA aparece como LAAM e RJ como LARJ.
                    </p>
                </DocCallout>
                <DocGrid cols={2}>
                    <DocFeature title="Um dashboard só na V2" tone="accent" icon="layers" badge="julgados-acordaos">
                        <p>
                            Na V2 os três são o mesmo dashboard (<Code>julgados-acordaos</Code>), com o cálculo da v1
                            copiado sem mudança para <Code>app/analyses/</Code>; a unidade escolhida no seletor define
                            qual módulo roda. O módulo do RJ é uma réplica do LA (06/11/2026), só com o escritório
                            trocado.
                        </p>
                    </DocFeature>
                    <DocFeature title="Fallback do mérito" tone="info" icon="history" badge="status_segundo_grau">
                        <p>
                            Quando a coluna de mérito nova está vazia, a classificação lê do status antigo (
                            <Code>status_segundo_grau</Code>) — ver{' '}
                            <Secao id="classificacao">Classificação de mérito</Secao>.
                        </p>
                    </DocFeature>
                    <DocFeature title='O card "Total"' tone="ok" icon="check-circle" badge="Todos com acórdão">
                        <p>
                            O card "Total" conta todos os processos com acórdão no período, sem exigir status
                            classificável. Procedentes/Improcedentes/Extintos/Não classificados são subconjuntos desse
                            total (ver seção <Secao id="nao-classificados">Não classificados</Secao>).
                        </p>
                    </DocFeature>
                    <DocFeature title="Dashboard irmão" tone="violet" icon="scale" badge="1º grau">
                        <p>
                            Dashboard irmão na V2: <DocLink to="julgados-sentencas">Julgados — Sentenças</DocLink> (1º
                            grau) — mesma query e boa parte da mesma lógica, mas sem o card "Não classificados", com
                            ranking de juízes em vez de relatores e com um card extra de tempo médio até a sentença.
                        </p>
                    </DocFeature>
                </DocGrid>
                <DocGrid cols={2}>
                    <DocChange status="06/11/2026" tone="danger" area="Regra" title="Agravos fora das análises" framed>
                        <p>
                            Processos cujo número CNJ termina em <Code>0000</Code>, <Code>9000</Code>, <Code>9001</Code>{' '}
                            ou <Code>9002</Code> (código de origem nos 4 últimos dígitos) são recursos de agravo e não
                            entram em nenhuma contagem deste dashboard: totais, procedentes/improcedentes/extintos, taxa
                            de procedência, gráficos, rankings, embargos, Estudo das Improcedências e o relatório
                            exportado. A regra vale só para números com os 20 dígitos do padrão (números malformados
                            nunca são excluídos) e fica em <Code>app/analyses/common/julgados_agravo.py</Code>, aplicada
                            no filtro de base do escritório (<Code>_base_julgados_NG/LA/RJ</Code>).
                        </p>
                    </DocChange>
                    <DocChange
                        status="06/11/2026"
                        tone="warn"
                        area="Regra"
                        title="Faixa de atenção mostra o histórico todo"
                        framed
                    >
                        <p>
                            A faixa de atenção (dados faltando) não segue mais o período selecionado: conta tudo o que
                            falta preencher no histórico do escritório, respeitando só os demais filtros da página
                            (matéria, relator, comarca etc.). Além dos campos vazios (relator, matéria, comarca,
                            competência, UF, valor do acórdão), ela avisa dois casos de inconsistência:{' '}
                            <strong>mérito lançado sem data do acórdão</strong> — o processo não entra em nenhuma
                            contagem, porque o eixo do dashboard é <Code>DATA_ACORDAO</Code> — e{' '}
                            <strong>data do acórdão sem mérito</strong> — entra no total, mas cai em "Não
                            classificados". Os dois aparecem na lista clicável com o número do processo.
                        </p>
                    </DocChange>
                </DocGrid>
                <DocChange
                    status="11/11/2026"
                    tone="ok"
                    area="Novo · NG, LA e RJ"
                    title="Estudo das Improcedências"
                    framed
                >
                    <p>
                        Seção 02 do dashboard, montada como o estudo da Sentença, com os acórdãos improcedentes: total e
                        valor de causa inicial, mapa por comarca (Capital × Interior, "a cada 10 acórdãos, X são
                        improcedentes" e, no tooltip, o tempo médio sentença → acórdão da comarca no histórico todo do
                        escritório), motivo informado no 2º grau, ranking de relatores e alternador Total (estoque) /
                        Entrada no período. No NG, a 3ª coluna da legenda do mapa, no lugar de "revertidas", mostra
                        quantos <strong>subiram ao STJ (Recurso Especial) ou ao STF (Recurso Extraordinário)</strong> —
                        improcedente no 2G ou sobe ou é arquivado —, pela subfase ATUAL do processo (id 151 = Recurso
                        Especial → STJ; id 152 = Recurso Extraordinário → STF, coluna <Code>ID_SUBFASE</Code> da query).
                        Em 11/11/2026 nenhum processo estava (nem tinha passado) por essas subfases, então o bloco
                        começou zerado. No LA e no RJ a seção é a mesma, <strong>sem</strong> o bloco de recursos ao
                        STJ/STF (lá a subida ao tribunal superior funciona de outro jeito — ajuste pendente); o mapa é o
                        de estado único (Amazonas no LA, Rio de Janeiro no RJ).
                    </p>
                </DocChange>
            </DocSection>

            <DocSection
                id="classificacao"
                title="02 — Classificação de mérito (Matriz de Julgamento)"
                subtitle="Migrado em 15/09/2026: acórdão de mérito passou a ter campo próprio"
                badge="8 valores"
            >
                <DocCallout icon="flow" title="Tabela própria, lógica compartilhada">
                    <p>
                        O acórdão de mérito lê de uma tabela própria — <Code>acordao_merito_segundo_grau</Code> — com a
                        mesma escala de 7 valores da Sentença, mais um 8º valor exclusivo ("Sentença Anulada"). A lógica
                        de leitura e classificação é compartilhada com a Sentença e a Recursal (NG e LA) no módulo{' '}
                        <Code>app/analyses/common/matriz_julgamento.py</Code>, para não duplicar regra entre módulos.
                    </p>
                </DocCallout>
                <DocGrid cols={2}>
                    <DocFeature
                        title="Mérito 2G — 8 valores (7 comuns com a Sentença + 1 exclusivo)"
                        tone="accent"
                        icon="list"
                        framed
                    >
                        <ul>
                            {MERITO.map((m) => (
                                <li key={m.id}>
                                    <Code>{m.id}</Code> {m.label}
                                    {m.only2g && <em> (exclusivo do 2G)</em>} →{' '}
                                    {m.cat ? (
                                        <DocPill tone={CAT_TONE[m.cat]}>{m.cat}</DocPill>
                                    ) : (
                                        <DocPill>não classificado</DocPill>
                                    )}
                                </li>
                            ))}
                        </ul>
                    </DocFeature>
                    <DocFeature
                        title="Compatibilidade com o esquema antigo"
                        tone="info"
                        icon="history"
                        badge="STATUS_2G"
                        framed
                    >
                        <p>
                            Enquanto o preenchimento novo não cobre 100% da base, cada linha ainda pode cair de volta no{' '}
                            <Code>STATUS_2G</Code> antigo (IDs 17-25): quando <Code>id_acordao_merito_grau2</Code> está
                            vazio, o nome do status antigo é traduzido para o ID de mérito equivalente por{' '}
                            <strong>nome</strong> normalizado (não por ID — o esquema antigo já teve uma renomeação de
                            IDs antes desta migração). "Acordo Homologado" (eixo próprio, fora de escopo) e "Encerrado
                            1G" (equivale a sem recurso) não têm tradução — viram mérito nulo. Validado contra os
                            processos com os dois campos preenchidos: a tradução bate em {'>'}99,9% dos casos.
                        </p>
                    </DocFeature>
                </DocGrid>
                <DocChange status="15/09/2026" tone="neutral" area="Histórico" title="Migração do campo de mérito">
                    <p>
                        Antes desta data, a classificação lia direto de <Code>status_segundo_grau</Code> (IDs 17-25, sem
                        escala de mérito dedicada). A migração trocou a fonte primária pelo novo campo de mérito,
                        mantendo o fallback por nome descrito acima para não quebrar dados históricos. Junto com essa
                        migração vieram os campos de <strong>Embargos</strong> — ver{' '}
                        <Secao id="embargos">Embargos e reversão</Secao>.
                    </p>
                </DocChange>
            </DocSection>

            <DocSection
                id="filtros"
                title="03 — Filtros interativos"
                subtitle="Cumulativos: E entre dimensões, OU dentro de cada uma"
                tone="info"
                badge="Clicável"
            >
                <DocCallout tone="info" icon="filter" title="Clique liga ou desliga o valor">
                    <p>
                        Clicar numa fatia/barra de gráfico ou num card de categoria liga ou desliga aquele valor no
                        filtro correspondente; os filtros ativos aparecem no topo da página e podem ser removidos um a
                        um.
                    </p>
                </DocCallout>
                <DocTable head={['Dimensão', 'Parâmetro', 'Onde se clica']} rows={FILTROS} code={[1]} />
                <p className="muted small">
                    A lógica de filtro não muda por escritório: <Code>JulgadosAcordaoFiltros</Code> (variantes{' '}
                    <Code>JulgadosAcordaoFiltrosLA</Code> e <Code>JulgadosAcordaoFiltrosRJ</Code>), com comparação por{' '}
                    <Code>casefold()</Code>.
                </p>
            </DocSection>

            <DocSection
                id="motivo-extincao"
                title="04 — Motivo das extinções"
                subtitle="Ao lado de competência e comarca"
                tone="warn"
                badge="Só extintos"
            >
                <DocGrid cols={2}>
                    <DocFeature title="De onde vem o motivo" tone="warn" icon="ban" badge="id_motivo_status_grau2">
                        <p>
                            Quando um processo é marcado como extinto no LexFlow, abre-se um campo livre para o
                            colaborador registrar o motivo — esse texto vem de <Code>id_motivo_status_grau2</Code>, que
                            aponta para <Code>motivo_status_grau.description</Code> (tabela escopada por escritório e
                            grau).
                        </p>
                    </DocFeature>
                    <DocFeature title="Só acórdãos extintos" tone="neutral" icon="filter" badge="mérito 7">
                        <p>
                            O agrupador pré-filtra a base para só os acórdãos extintos (mesmo critério do card
                            "Extintos": mérito <Code>7</Code>) antes de agrupar por motivo — um acórdão procedente nunca
                            aparece aqui, mesmo que tenha algum texto residual no campo.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="nao-classificados"
                title="05 — Não classificados"
                subtitle="Não é erro de soma — é um resultado real fora das 3 categorias de mérito"
                badge="Só no Acórdão"
            >
                <DocCallout icon="alert" title="Mérito 8 ou não resolvido">
                    <p>
                        Card ao lado de Procedentes/Improcedentes/Extintos. Conta os processos com acórdão no período
                        cujo mérito 2G é <Code>8</Code> (Sentença Anulada) ou não resolvido (nem coluna nova, nem status
                        antigo traduzível) — a Sentença não tem esse card porque a escala de mérito 1G cobre 100% das
                        variações possíveis (ver <Secao id="classificacao">Classificação de mérito</Secao>).
                    </p>
                </DocCallout>

                <DocGrid cols={2}>
                    <DocFeature title="Mês corrente (ago/2026)" tone="accent" icon="calendar">
                        <DocTable
                            head={['Unidade', 'Total', 'Classificados', 'Não classif.', '%']}
                            rows={[
                                ['LA', '384', '382', '2', '0,5%'],
                                ['NG', '220', '194', '26', '11,8%'],
                            ]}
                        />
                    </DocFeature>
                    <DocFeature title="Histórico completo (todo o banco)" tone="info" icon="history">
                        <DocTable
                            head={['Unidade', 'Total', 'Classificados', 'Não classif.', '%']}
                            rows={[
                                ['LA', '11.531', '9.709', '1.822', '15,8%'],
                                ['NG', '2.896', '2.379', '517', '17,8%'],
                            ]}
                        />
                    </DocFeature>
                </DocGrid>
                <p className="muted small">
                    Não é um mês atípico — a proporção histórica (16–18%) é parecida com o NG do mês corrente (11,8%); o
                    LA do mês corrente (0,5%) está atipicamente baixo, não é o padrão geral.
                </p>

                <DocChange status="06/10/2026" tone="ok" area="Novidade" title='Card "Média sentença → acórdão"' framed>
                    <p>
                        Ao lado de "Não classificados": média de dias entre <Code>DATA_SENTENCA</Code> (1G) e{' '}
                        <Code>DATA_ACORDAO</Code>, para os acórdãos do período (eixo <Code>DATA_ACORDAO</Code>) com as
                        duas datas e acórdão ≥ sentença; sem par válido o acórdão fica fora da média (não conta como 0).
                        Comparativo vs período anterior de mesma duração, com cores invertidas (subir = pior). Campos{' '}
                        <Code>julgados_acordao_tempo_medio_dias_NG/LA/RJ</Code> e{' '}
                        <Code>comparativo_julgados_acordao_tempo_medio_dias_NG/LA/RJ</Code>. Setembro/2026: NG ≈ 183
                        dias, LA ≈ 177 dias.
                    </p>
                </DocChange>
            </DocSection>

            <DocSection
                id="embargos"
                title="06 — Embargos e reversão"
                subtitle="Adicionado em 15/09/2026"
                tone="violet"
                badge="Status Resultante"
            >
                <DocCallout tone="violet" icon="undo" title="Data e resultado do embargo">
                    <p>
                        Quando um acórdão de mérito sai improcedente (ou improcedente por prescrição/decadência), a
                        parte pode opor embargos tentando reverter o resultado. O campo de data{' '}
                        <Code>acordao_embargos</Code> marca quando isso aconteceu e o campo de resultado (
                        <Code>id_acordao_embargos_grau2</Code> → <Code>acordao_embargos_segundo_grau</Code>) diz o que
                        foi decidido; o dashboard mostra, para os embargos do período, o Status Resultante de cada um.
                    </p>
                </DocCallout>

                <DocGrid cols={2}>
                    <DocFeature title="Embargado" tone="info" icon="calendar" badge="ACORDAO_EMBARGOS" framed>
                        <p>
                            Acórdão com data de embargo (<Code>ACORDAO_EMBARGOS</Code>) dentro do período selecionado —
                            o eixo é a data do acórdão de embargos, não a <Code>DATA_ACORDAO</Code> usada pelos outros
                            cards (ver o ajuste de 06/10/2026 abaixo). Sem período, entram todos os embargados,
                            inclusive os com resultado lançado e sem data de embargo.
                        </p>
                    </DocFeature>
                    <DocFeature title="Revertido" tone="ok" icon="refresh" badge="Revertido Ganho" framed>
                        <p>
                            Embargado cujo Status Resultante (matriz abaixo) é <strong>Revertido Ganho</strong>: era
                            improcedente antes dos embargos e o resultado lançado foi "Reverteu Procedência". Até
                            06/10/2026 era uma estimativa pelo mérito atual (ver histórico no fim da seção).
                        </p>
                    </DocFeature>
                </DocGrid>

                <DocChange
                    status="06/10/2026"
                    tone="ok"
                    area="Novidade"
                    title="Resultado oficial dos embargos (matriz de Status Resultante)"
                    framed
                >
                    <p>
                        O resultado do embargo (<Code>id_acordao_embargos_grau2</Code> →{' '}
                        <Code>acordao_embargos_segundo_grau</Code>) começou a ser preenchido e ganhou 2 valores novos:{' '}
                        <strong>REJEITADOS</strong> e <strong>NÃO CONHECIDOS</strong>, que dão sempre "Status Mantido",
                        em qualquer acórdão de mérito. A pizza "Resultado dos embargos" (e o filtro e a coluna do
                        relatório) passou a mostrar o <strong>Status Resultante</strong> da matriz abaixo, que cruza o
                        mérito vigente <strong>antes</strong> dos embargos com o resultado lançado. Casamento por nome:
                        as tabelas de 1G e 2G têm IDs diferentes para os valores novos.
                    </p>
                </DocChange>

                <DocTable
                    head={['Status vigente (antes dos embargos)', 'Resultado dos embargos', 'Status Resultante']}
                    rows={MATRIZ_ROWS}
                />

                <DocCallout tone="warn" icon="alert" title="O mérito de hoje já é o pós-embargo">
                    <p>
                        O LexFlow atualiza <Code>id_acordao_merito_grau2</Code> na mesma edição em que lança o resultado
                        do embargo (validado no <Code>processo_audit</Code>: num caso "Reverteu Improcedência", o mérito
                        foi de Procedente para Improcedente no mesmo instante). Por isso o "antes" vem do histórico: a
                        query <Code>julgados</Code> traz <Code>ID_ACORDAO_MERITO_2G_PRE_EMBARGOS</Code> = último valor
                        do mérito no <Code>processo_audit</Code> antes do lançamento do resultado atual (sem histórico,
                        o mérito atual). Calculado só para os processos com resultado lançado, sem custo perceptível na
                        query. Embargado <strong>sem</strong> resultado lançado cai na fatia "Sem resultado lançado"
                        (ver abaixo). Em 06/10/2026 — NG: 70 com resultado lançado — 66 Status Mantido, 2 Ganho
                        Ampliado, 1 Ganho Reduzido, 1 Revertido Perda; LA: nenhum ainda.
                    </p>
                </DocCallout>

                <DocGrid cols={2}>
                    <DocChange
                        status="06/10/2026"
                        tone="info"
                        area="Ajuste"
                        title='Eixo de data dos embargos e fatia "Sem resultado lançado"'
                    >
                        <p>
                            A pizza "Resultado dos embargos" e os contadores Embargados/Revertidos passaram a usar como
                            período a <strong>data do acórdão de embargos</strong> (<Code>ACORDAO_EMBARGOS</Code>), não
                            a data do acórdão original (<Code>DATA_ACORDAO</Code>), que costuma ser de meses antes —
                            mesmo ajuste feito na Sentença. Embargo com data e sem resultado lançado vira uma fatia
                            própria, <strong>"Sem resultado lançado"</strong>, sem estimativa. Setembro/2026 NG: 19 com
                            resultado (15 Prejudicados, 2 Não Conhecidos, 2 Rejeitados — todos Status Mantido) e 305 sem
                            resultado. A estimativa pelo mérito atual descrita abaixo <strong>não é mais usada</strong>.
                            Sem período selecionado, entram todos os embargados, inclusive os com resultado e sem data
                            de embargo.
                        </p>
                    </DocChange>
                    <DocChange
                        status="06/10/2026"
                        tone="ok"
                        area="Novidade"
                        title="Tempo médio acórdão → acórdão de embargos"
                    >
                        <p>
                            Abaixo da pizza "Resultado dos embargos": média de dias entre <Code>DATA_ACORDAO</Code> e a
                            data do acórdão de embargos (<Code>ACORDAO_EMBARGOS</Code>), no mesmo recorte da pizza
                            (embargo com data no período), só com as duas datas e embargo ≥ acórdão. Campo{' '}
                            <Code>julgados_acordao_embargos_tempo_medio_dias_NG/LA/RJ</Code>. Setembro/2026 NG: 20,6
                            dias.
                        </p>
                    </DocChange>
                </DocGrid>

                <DocChange
                    status="15/09 → 06/10/2026"
                    tone="neutral"
                    area="Histórico"
                    title="Estimativa usada antes do resultado oficial"
                >
                    <p>
                        O campo de <em>resultado</em> do embargo (<Code>id_acordao_embargos_grau2</Code>, valores como
                        "REVERTEU PROCEDÊNCIA"/"REVERTEU IMPROCEDÊNCIA") ficou 100% vazio até out/2026 — só a data de
                        embargo era preenchida. Como proxy, assumia-se que o campo de mérito é atualizado para refletir
                        o resultado pós-embargo: embargado com mérito atual procedente = "Revertido"; não-procedente =
                        "Mantido" (checado ao vivo contra o banco em 15/09/2026 antes de implementar). Contagem pela
                        estimativa em 15/09/2026, sem filtro de período: NG 497 embargados (146 revertidos, 351
                        mantidos); LA 10 (3 revertidos, 7 mantidos). Desde 06/10/2026 o resultado oficial é lido
                        diretamente (ver acima).
                    </p>
                </DocChange>

                <DocCallout tone="neutral" icon="pieChart" title='Na tela: a pizza "Resultado dos embargos"'>
                    <p>
                        Na tela, o resultado dos embargos aparece na pizza "Resultado dos embargos", na mesma fileira
                        dos cards (Total, Procedentes, Improcedentes, Extintos, Não classificados, Média sentença →
                        acórdão), com as fatias na ordem Revertido Ganho, Ganho Ampliado, Ganho Reduzido, Status
                        Mantido, Revertido Perda, Revisar Classificação e Sem resultado lançado — clicável, filtra a
                        página igual aos outros gráficos (<Code>resultado_embargos_julgados</Code>). Os contadores
                        Embargados e Revertidos (com comparativo vs período anterior) também vêm calculados na resposta
                        do dashboard. Liminar (<Code>id_liminar_grau2</Code>) ficou fora de escopo — 100% vazio no banco
                        e sem coluna de data equivalente à de embargos.
                    </p>
                </DocCallout>
            </DocSection>

            <DocSection
                id="ranking"
                title="07 — Ranking de Relatores"
                subtitle="Exige nome preenchido E mérito classificável"
                tone="info"
                badge="Taxa de procedência"
            >
                <DocCallout tone="info" icon="users" title="Duas condições por linha">
                    <p>
                        O ranking exige <strong>duas</strong> condições por linha: nome preenchido (
                        <Code>RELATOR_2G</Code>) <em>e</em> mérito classificável — a mesma regra da seção{' '}
                        <Secao id="nao-classificados">Não classificados</Secao>. A ordem é pela taxa de procedência do
                        relator (procedentes ÷ acórdãos classificados dele), da maior para a menor; no empate, quem tem
                        mais acórdãos vem antes.
                    </p>
                </DocCallout>

                <DocCallout
                    tone="warn"
                    icon="alert"
                    title="Fonte do nome é o campo de texto livre do processo, não o cadastro (FK)"
                >
                    <p>
                        <Code>RELATOR_2G</Code> vem de <Code>processo.relator_2g</Code>, um campo de texto livre. A
                        tabela <Code>processo</Code> também tem uma FK para o cadastro normalizado (
                        <Code>relator_segundo_grau</Code>), mas ela <strong>não é usada</strong> aqui: por decisão de
                        negócio, o texto livre é a fonte oficial para todas as análises de relator nesses dashboards
                        (ver histórico abaixo).
                    </p>
                </DocCallout>

                <DocTable
                    head={['Unidade', 'Classificados (set/2026)', 'Com relator', '% faltando']}
                    rows={[
                        ['LA', '353', '353', '0,0%'],
                        ['NG', '208', '207', '0,5%'],
                    ]}
                />

                <p className="muted small">
                    O aviso de relator faltando na faixa de atenção do topo da página reflete essa mesma lacuna, mas
                    conta sobre o histórico todo do escritório (desde 06/11/2026), não só a base classificada do
                    período. Como a fonte agora é o texto livre — mais preenchido que o cadastro —, a lacuna é bem menor
                    do que era quando o cadastro (FK) era a fonte oficial.
                </p>

                <DocChange
                    status="26/09 → 28/09/2026"
                    tone="neutral"
                    area="Histórico"
                    title="Idas e vindas entre cadastro (FK) e texto livre"
                >
                    <p>
                        Em 26/09/2026 foi implementado um fallback pro texto livre (<Code>relator_2g</Code>) quando o
                        cadastro (FK) estava vazio, depois <strong>revertido</strong> no mesmo dia a pedido do usuário:
                        a regra passou a ser "só cadastro, nunca texto livre, nem na query base". Em 28/09/2026 o
                        usuário <strong>reverteu de novo</strong>, no sentido oposto: agora é o texto livre (
                        <Code>processo.juiz_1g</Code>/<Code>processo.relator_2g</Code>) a fonte oficial para juiz e
                        relator em todas as análises destes dashboards, e o cadastro (FK,{' '}
                        <Code>juiz_primeiro_grau</Code>/<Code>relator_segundo_grau</Code>) não é mais usado. A query{' '}
                        <Code>julgados</Code> foi ajustada para selecionar <Code>p.juiz_1g</Code>/
                        <Code>p.relator_2g</Code> diretamente, sem os JOINs para as tabelas de cadastro.
                    </p>
                </DocChange>
            </DocSection>

            <DocSection
                id="exportacao"
                title="08 — Exportação de relatório"
                subtitle="Botão 'Exportar' do dashboard (para quem tem permissão de exportar)"
                badge="CSV ou XLSX"
            >
                <DocCallout icon="sheet" title="Um passo só: escolha de campos">
                    <p>
                        Diálogo de um passo só — escolha de campos — que gera CSV ou XLSX no servidor, usando exatamente
                        o mesmo recorte de escritório, filtros e período já aplicados na tela. Nenhum filtro é
                        reconfigurado dentro do diálogo. Só entram acórdãos com data do acórdão (
                        <Code>DATA_ACORDAO</Code>) no período — o mesmo eixo dos cards.
                    </p>
                </DocCallout>
                <DocGrid cols={2}>
                    <DocFeature title="Endpoint" tone="info" icon="plug" badge="GET">
                        <p>
                            <Code>{'GET /orgs/{org}/units/{unidade}/dashboards/julgados-acordaos/export'}</Code>{' '}
                            (parâmetros <Code>from</Code>, <Code>to</Code>, <Code>format</Code>, <Code>campos</Code> e
                            os filtros da página). Na v1 eram três rotas, uma por escritório (
                            <Code>/api/dashboard/julgados_acordaos_NG|LA|RJ/export</Code>), com os mesmos campos.
                        </p>
                    </DocFeature>
                    <DocFeature title="Campos exportáveis" tone="accent" icon="list" badge="Query julgados">
                        <p>
                            Campos exportáveis vêm da query <Code>julgados</Code> (número do processo, matéria,
                            competência, comarca, UF, fase, subfase, câmara/turma, relator (2G), acórdão de mérito,
                            valor do acórdão, motivo da extinção, data de distribuição, data do acórdão, data e status
                            do acórdão de embargos), mais <strong>uma coluna calculada</strong>: "Status Resultante dos
                            Embargos" — ver abaixo.
                        </p>
                    </DocFeature>
                </DocGrid>

                <DocChange status="15/09/2026" tone="ok" area="Novidade" title="Campos de embargos no relatório">
                    <p>
                        Adicionados os campos "Data do Acórdão de Embargos" e "Status do Acórdão de Embargos" ao
                        relatório, espelhando <Code>ACORDAO_EMBARGOS</Code> (data) e{' '}
                        <Code>STATUS_ACORDAO_EMBARGOS</Code> (status, via JOIN com{' '}
                        <Code>acordao_embargos_segundo_grau</Code>) — mesmos campos usados em{' '}
                        <Secao id="embargos">Embargos e reversão</Secao>.
                    </p>
                </DocChange>

                <DocCallout tone="warn" icon="alert" title="Coluna de status: preenchimento parcial">
                    <p>
                        Em 15/09/2026 o campo oficial de resultado do embargo estava 100% vazio no banco, e a coluna
                        "Status do Acórdão de Embargos" saía em branco em <strong>todas</strong> as linhas — ela foi
                        adicionada mesmo assim porque é um campo real da query. Desde out/2026 o LexFlow preenche esse
                        dado, ainda em parte da base: a coluna traz o resultado lançado quando existe e fica vazia nos
                        demais.
                    </p>
                </DocCallout>

                <DocChange
                    status="16/09 · revista 06/10/2026"
                    tone="violet"
                    area="Coluna calculada"
                    title='"Status Resultante dos Embargos"'
                    framed
                >
                    <p>
                        Para quem baixa o relatório saber o desfecho do embargo, o campo{' '}
                        <strong>"Status Resultante dos Embargos"</strong> (slug <Code>resultado_embargos_estimado</Code>
                        ) traz o mesmo Status Resultante da pizza "Resultado dos embargos": a matriz oficial (mérito
                        antes dos embargos × resultado lançado) quando há resultado, "Sem resultado lançado" quando só
                        há a data de embargo, e vazio para os acórdãos não embargados. Calculado no momento da
                        exportação (<Code>_anotar_resultado_embargos_export</Code>, em{' '}
                        <Code>app/analyses/v1_julgados_export.py</Code>), reusando o mesmo getter do dashboard — não é
                        uma coluna nova no banco. Na primeira versão (16/09/2026) a coluna se chamava "Resultado do
                        Embargo (estimado)" e trazia "Revertido"/"Mantido" pela estimativa do mérito atual.
                    </p>
                </DocChange>

                <DocChange
                    status="26/08/2026"
                    tone="neutral"
                    area="Histórico"
                    title="Corrigido o recorte de escritório"
                >
                    <p>
                        Na primeira versão, o export aplicava os filtros de matéria/relator/etc. mas esquecia o recorte
                        de escritório (<Code>_base_julgados_NG</Code>/<Code>_base_julgados_LA</Code>), que na tela só é
                        aplicado dentro das funções de KPI/gráfico. Resultado: exportar do NG trazia junto acórdãos da
                        LA (e vice-versa) que batessem com o mesmo filtro. Reproduzido com dados reais — matéria "ANP",
                        01–13/08: dashboard mostrava 27 (correto, só NG), export trazia 36 (27 NG + 9 LA vazando).
                        Corrigido aplicando o mesmo recorte de escritório antes do filtro categórico, igual ao
                        dashboard; revalidado após o fix (27 e 9, separados por escritório).
                    </p>
                </DocChange>
            </DocSection>

            <DocSection
                id="notas"
                title="09 — Notas e pendências conhecidas"
                subtitle="Detalhes técnicos que ajudam a diagnosticar divergências futuras"
                tone="neutral"
            >
                <DocGrid cols={2}>
                    <DocFeature
                        title='Ranking e "não classificados" nunca somam ao total'
                        tone="ok"
                        icon="check-circle"
                        badge="Esperado"
                    >
                        <p>
                            É esperado, não bug: Total conta tudo no período; Procedentes + Improcedentes + Extintos +
                            Não classificados também soma o total; mas o ranking exclui adicionalmente quem não tem
                            relator — por isso soma menos que qualquer um dos dois.
                        </p>
                    </DocFeature>
                    <DocFeature
                        title="Comparação de maiúsculas e minúsculas nos filtros"
                        tone="info"
                        icon="filter"
                        badge="casefold()"
                    >
                        <p>
                            Matéria/comarca/competência/motivo comparam por <Code>casefold()</Code> (sem diferenciar
                            maiúsculas); UF é normalizada para maiúsculas antes de comparar. Um valor com espaço a mais
                            ou acento diferente no banco não é normalizado e vira uma opção separada no filtro.
                        </p>
                    </DocFeature>
                    <DocFeature title='Export não rotula "não classificado"' tone="warn" icon="alert" badge="CSV/XLSX">
                        <p>
                            O CSV/XLSX não tem uma coluna calculada de categoria: a coluna "Acórdão de Mérito" mostra o
                            nome do mérito lançado no campo novo (ex.: SENTENÇA ANULADA, que cai em "Não classificados")
                            ou fica vazia quando o campo novo não está preenchido — inclusive nos processos que o
                            dashboard classificou pelo status antigo. Quem audita o relatório precisa saber que esses
                            valores não dizem sozinhos se o acórdão é Procedente/Improcedente/Extinto.
                        </p>
                    </DocFeature>
                    <DocFeature
                        title="Relator vem do texto livre do processo, não do cadastro (FK)"
                        tone="neutral"
                        icon="users"
                        badge="relator_2g"
                    >
                        <p>
                            Ver <Secao id="ranking">Ranking de Relatores</Secao> — <Code>processo.relator_2g</Code>{' '}
                            (texto livre) é a fonte oficial por decisão de negócio; o cadastro normalizado (
                            <Code>relator_segundo_grau</Code>) não é usado em nenhuma análise.
                        </p>
                    </DocFeature>
                </DocGrid>
                <DocGrid cols={2}>
                    <DocChange
                        status="29/09/2026"
                        tone="neutral"
                        area="Histórico"
                        title="Corrigida a fonte do valor de causa"
                    >
                        <p>
                            <Code>VALOR_CAUSA_ACORDO</Code> (card "Valor acórdãos procedentes" da v1) vinha de{' '}
                            <Code>processo.valor_causa_va</Code> — um campo separado do valor de causa inicial,
                            majoritariamente vazio e, quando preenchido, divergente do valor inicial em ~93% dos casos.
                            Corrigido para usar <Code>processo.valor_causa</Code> (mesmo valor protocolado, sincronizado
                            automaticamente do protocolo) — mesma correção aplicada na Sentença (
                            <Code>VALOR_CAUSA_SENTENCA</Code>).
                        </p>
                    </DocChange>
                    <DocChange
                        status="21/10/2026"
                        tone="ok"
                        area="Atualização"
                        title="Card de valor passou a ser o valor do acórdão"
                    >
                        <p>
                            Na V2 o card "Valor acórdãos procedentes" não aparece na tela: o backend ainda calcula o
                            valor, mas ele só sai no relatório e no aviso de dados faltando. Na v1, o card passou a
                            somar <Code>VALOR_ACORDAO</Code> (<Code>processo.valor_causa_va</Code>, descrito no banco
                            como "Novo Valor da Causa do Valor Acordão"), o valor fixado no acórdão, dos acórdãos
                            procedentes do período; a variação compara esse mesmo valor com o período anterior. O valor
                            de causa inicial deixou de aparecer no card. Motivo: o relatório baixado (coluna "Valor do
                            Acórdão") somava R$ 574 mil no NG em out/2026 e o card, que usava o valor inicial, mostrava
                            R$ 195 mil — eram campos diferentes. Os dois passaram a bater. O histórico ao lado continua
                            válido para o valor de causa inicial (<Code>VALOR_CAUSA_ACORDO</Code>):{' '}
                            <Code>valor_causa_va</Code> não é um valor de causa "errado", e sim outro dado, o valor do
                            acórdão.
                        </p>
                        <p>
                            No mesmo período: (1) o relatório de exportação ganhou a coluna "Valor do Acórdão" (slug{' '}
                            <Code>valor_acordao</Code>), em reais — na v1, número com formato R$ no XLSX (somável) e
                            texto "R$ 1.234,56" no CSV; na V2, texto "R$ 1.234,56" nos dois formatos; (2) a barra de
                            aviso no topo passou a contar acórdãos procedentes com proveito econômico (mérito 1 ou 3)
                            sem valor do acórdão (vazio ou zero), e esses processos entram na lista clicável com o campo
                            "Valor do acórdão".
                        </p>
                    </DocChange>
                </DocGrid>
            </DocSection>
        </DocPage>
    )
}
