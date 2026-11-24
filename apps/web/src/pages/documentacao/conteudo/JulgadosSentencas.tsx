import type * as React from 'react'
import {
    Code,
    DiffBox,
    DocCard,
    DocGrid,
    DocLink,
    DocPage,
    DocSection,
    DocTable,
    InfoBox,
    WatchBox,
    type TocItem,
} from '../components/DocParts.tsx'

// Guia trazido da v1: LexHub/src/pages/documentacao/JulgadosSentenca.tsx (convertido para as peças da V2).

const mono = (text: string) => <Code>{text}</Code>

const TOC: TocItem[] = [
    { id: 'visao-geral', label: 'Visão geral' },
    { id: 'classificacao', label: 'Classificação de mérito' },
    { id: 'filtros', label: 'Filtros interativos' },
    { id: 'tempo-medio', label: 'Tempo médio até a sentença' },
    { id: 'embargos', label: 'Embargos e reversão' },
    { id: 'ranking', label: 'Ranking de Juízes' },
    { id: 'estudos-extincao', label: 'Estudos de Extinção' },
    { id: 'exportacao', label: 'Exportação de relatório' },
    { id: 'notas', label: 'Notas e pendências' },
]

export function JulgadosSentencasDoc() {
    return (
        <DocPage
            title="Julgados — Sentenças"
            tags={['NG', 'LA']}
            note="2 dashboards, 1 query só"
            toc={TOC}
            intro={
                <>
                    Como os dashboards de Sentenças (1º Grau, LA e NG) classificam um resultado pela Matriz de
                    Julgamento (mérito), calculam o ranking de juízes, o tempo médio até a sentença e a reversão por
                    embargos, e por que a grande maioria dos processos não tem juiz preenchido no banco — validado com
                    dados reais, não é bug de tela.
                </>
            }
        >
            <DocSection
                id="visao-geral"
                title="Visão geral"
                subtitle="2 dashboards na tela (LA e NG), uma query só por trás dos dois"
            >
                <InfoBox>
                    A query <Code>julgados</Code> (compartilhada com os dashboards de Acórdãos) traz processos de{' '}
                    <strong>todos os escritórios</strong> — não tem filtro de escritório no SQL. O recorte por
                    escritório (LA = 21, NG = 20) é feito depois, em Python, por <Code>_base_julgados_LA()</Code> /{' '}
                    <Code>_base_julgados_NG()</Code> — uma função por módulo, chamada dentro de cada
                    KPI/ranking/gráfico.
                </InfoBox>
                <DocTable
                    head={['Dashboard', 'Grau', 'Eixo de data', 'Tabela de mérito', 'Módulo backend']}
                    rows={(
                        [
                            {
                                Dashboard: (
                                    <>
                                        Julgados Sentenças <span className="doc-tag">LA</span>
                                    </>
                                ),
                                Grau: '1G',
                                'Eixo de data': mono('DATA_SENTENCA'),
                                'Tabela de mérito': mono('sentenca_merito_primeiro_grau'),
                                'Módulo backend': mono('LA/julgados_sentenca_LA.py'),
                            },
                            {
                                Dashboard: (
                                    <>
                                        Julgados Sentenças <span className="doc-tag">NG</span>
                                    </>
                                ),
                                Grau: '1G',
                                'Eixo de data': mono('DATA_SENTENCA'),
                                'Tabela de mérito': mono('sentenca_merito_primeiro_grau'),
                                'Módulo backend': mono('NG/julgados_sentenca.py'),
                            },
                        ] as Record<string, React.ReactNode>[]
                    ).map((r) =>
                        ['Dashboard', 'Grau', 'Eixo de data', 'Tabela de mérito', 'Módulo backend'].map((c) => r[c]),
                    )}
                />
                <p>
                    Fallback: quando a coluna de mérito nova está vazia, a classificação lê do status antigo (
                    {mono('status_primeiro_grau')}) — ver <a href="#classificacao">Classificação de mérito</a>.
                </p>
                <p>
                    O card "Total" conta todos os processos sentenciados no período, sem exigir status classificável.
                    Procedentes/Improcedentes/Extintos são subconjuntos desse total. Ao contrário do Acórdão, a Sentença
                    não tem um card "Não classificados" — a escala de mérito 1G cobre 100% das variações possíveis (ver
                    próxima seção), então o resíduo é só mérito ainda não lançado.
                </p>
                <p>
                    Documentação irmã: <DocLink to="julgados-acordaos">Julgados — Acórdãos</DocLink> (2º Grau) — mesma
                    query e boa parte da mesma lógica, mas com card "Não classificados", ranking de relatores em vez de
                    juízes e sem o card de tempo médio.
                </p>
            </DocSection>

            <DocSection
                id="classificacao"
                title="Classificação de mérito (Matriz de Julgamento)"
                subtitle="Migrado em 15/09/2026: sentença de mérito passou a ter campo próprio"
            >
                <InfoBox>
                    A sentença de mérito agora lê de uma tabela nova e dedicada —{' '}
                    {mono('sentenca_merito_primeiro_grau')} — com uma escala de 7 valores. A lógica de leitura e
                    classificação é compartilhada com o Acórdão e a Recursal (LA/NG) no módulo{' '}
                    {mono('app/analyses/common/matriz_julgamento.py')}, para não duplicar regra entre módulos (o Acórdão
                    usa a mesma escala, mais um 8º valor exclusivo — ver a doc de Acórdãos).
                </InfoBox>

                <DocGrid>
                    <DocCard title="Mérito 1G — 7 valores, todos com mérito julgado">
                        <ul>
                            <li>
                                {mono('1')} Procedente com proveito econômico → <strong>Procedente</strong>
                            </li>
                            <li>
                                {mono('2')} Procedente sem proveito econômico → <strong>Procedente</strong>
                            </li>
                            <li>
                                {mono('3')} Parc. procedente com proveito econômico → <strong>Procedente</strong>
                            </li>
                            <li>
                                {mono('4')} Parc. procedente sem proveito econômico → <strong>Procedente</strong>
                            </li>
                            <li>
                                {mono('5')} Improcedente → <strong>Improcedente</strong>
                            </li>
                            <li>
                                {mono('6')} Improcedente por prescrição/decadência → <strong>Improcedente</strong>
                            </li>
                            <li>
                                {mono('7')} Extinto sem mérito → <strong>Extinto</strong>
                            </li>
                        </ul>
                    </DocCard>
                    <DocCard title="Compatibilidade com o esquema antigo">
                        Enquanto o preenchimento novo não cobre 100% da base, cada linha ainda pode cair de volta no{' '}
                        {mono('STATUS_1G')} antigo (IDs 17-23): quando {mono('id_sentenca_merito_grau1')} está vazio, o
                        nome do status antigo é traduzido para o ID de mérito equivalente por <strong>nome</strong>{' '}
                        normalizado (não por ID — o esquema antigo já teve uma renomeação de IDs antes desta migração).
                        "Acordo Homologado" (eixo próprio, fora de escopo) e "Encerrado 1G" (equivale a sem recurso) não
                        têm tradução — viram mérito nulo. Validado contra os 17.185 processos com os dois campos
                        preenchidos: a tradução bate em {'>99,9%'} dos casos.
                    </DocCard>
                </DocGrid>

                <DiffBox title="Histórico — migração de 15/09/2026">
                    Antes desta data, a classificação lia direto de {mono('status_primeiro_grau')} (IDs 17-23, sem
                    escala de mérito dedicada). A migração trocou a fonte primária pelo novo campo de mérito, mantendo o
                    fallback por nome descrito acima para não quebrar dados históricos. Junto com essa migração vieram
                    os campos de <strong>Embargos</strong> — ver seção abaixo.
                </DiffBox>
            </DocSection>

            <DocSection
                id="filtros"
                title="Filtros interativos"
                subtitle="Cumulativos: AND entre dimensões, OR dentro de cada uma"
            >
                <InfoBox>
                    Clicar numa fatia/barra de gráfico ou num card de categoria alterna (toggle) aquele valor no filtro
                    correspondente; os filtros ativos aparecem como chips removíveis no topo da página.
                </InfoBox>
                <DocTable
                    head={['Dimensão', 'Query param', 'Onde se clica']}
                    rows={(
                        [
                            {
                                Dimensão: 'Matéria',
                                'Query param': mono('materia_julgados'),
                                'Onde se clica': 'gráfico de pizza',
                            },
                            { Dimensão: 'Juiz (1G)', 'Query param': mono('juiz_julgados'), 'Onde se clica': 'ranking' },
                            { Dimensão: 'Comarca', 'Query param': mono('comarca_julgados'), 'Onde se clica': 'barra' },
                            {
                                Dimensão: 'Competência',
                                'Query param': mono('competencia_julgados'),
                                'Onde se clica': 'barra',
                            },
                            {
                                Dimensão: 'Categoria',
                                'Query param': mono('categoria_julgados'),
                                'Onde se clica': 'stat cards',
                            },
                            {
                                Dimensão: 'UF',
                                'Query param': mono('uf_julgados'),
                                'Onde se clica': 'dropdown no cabeçalho',
                            },
                            {
                                Dimensão: 'Motivo da extinção',
                                'Query param': mono('motivo_extincao_julgados'),
                                'Onde se clica': 'barra (só extintos)',
                            },
                            {
                                Dimensão: 'Ano de ajuizamento',
                                'Query param': mono('ano_ajuizamento_julgados'),
                                'Onde se clica': 'donut',
                            },
                            {
                                Dimensão: 'Resultado dos embargos',
                                'Query param': mono('resultado_embargos_julgados'),
                                'Onde se clica': 'donut (ver seção Embargos)',
                            },
                        ] as Record<string, React.ReactNode>[]
                    ).map((r) => ['Dimensão', 'Query param', 'Onde se clica'].map((c) => r[c]))}
                />
                <p>
                    Frontend: <Code>lib/julgadosSentencaFilters.ts</Code> (arquivo compartilhado com a LA — a lógica de
                    filtro não muda por escritório). Backend: <Code>JulgadosSentencaFiltros</Code> (+ variante{' '}
                    <Code>*LA</Code>), comparação por <Code>casefold()</Code>.
                </p>
            </DocSection>

            <DocSection
                id="tempo-medio"
                title="Tempo médio até a sentença"
                subtitle="Distribuição → sentença, em dias corridos"
            >
                <InfoBox>
                    Mede o intervalo entre <Code>DATA_AJUIZAMENTO</Code> (fonte: <Code>p.distribuicao</Code> — data de
                    distribuição do processo) e <Code>DATA_SENTENCA</Code>. Só entram na média pares com as duas datas
                    preenchidas e sentença ≥ ajuizamento; sem par válido, o processo é excluído (não conta como zero).
                </InfoBox>
                <p>
                    Não existe equivalente no Acórdão — o pedido original era especificamente "tempo desde a
                    distribuição até a sentença". Card com variação percentual invertida: crescimento de dias é ruim
                    (mais devagar), então a variação aparece em vermelho quando sobe.
                </p>
                <p>Amostra do mês corrente (ago/2026): LA ≈ 125 dias (n≈260), NG ≈ 141 dias (n≈245).</p>
            </DocSection>

            <DocSection id="embargos" title="Embargos e reversão" subtitle="Adicionado em 15/09/2026">
                <InfoBox>
                    Quando uma sentença de mérito sai improcedente (ou improcedente por prescrição/decadência), a parte
                    pode opor embargos tentando reverter o resultado. Um campo novo de data —{' '}
                    {mono('sentenca_embargos')} — marca quando isso aconteceu; o dashboard mostra quantas sentenças do
                    período foram embargadas e, dessas, quantas reverteram.
                </InfoBox>

                <DocGrid>
                    <DocCard title="Embargado">
                        Sentença cuja data de embargo ({mono('SENTENCA_EMBARGOS')}) está preenchida, dentro do mesmo
                        período filtrado por {mono('DATA_SENTENCA')} usado pelos outros cards da página.
                    </DocCard>
                    <DocCard title="Revertido (proxy, não campo oficial)">
                        Embargada <strong>e</strong> o mérito atual do processo ({mono('ID_SENTENCA_MERITO_1G')}) está
                        no conjunto Procedente. "Mantido" é o complemento: embargada cujo mérito atual continua
                        não-procedente.
                    </DocCard>
                </DocGrid>

                <DiffBox title="Novidade — 06/10/2026: resultado oficial dos embargos (matriz de Status Resultante)">
                    O resultado do embargo ({mono('id_sentenca_embargos_grau1')} →{' '}
                    {mono('sentenca_embargos_primeiro_grau')}) começou a ser preenchido e ganhou 2 valores novos:{' '}
                    <strong>REJEITADOS</strong> e <strong>NÃO CONHECIDOS</strong>, que dão sempre "Status Mantido", em
                    qualquer sentença de mérito. A pizza "Resultado dos embargos" (e o filtro e a coluna do relatório)
                    passou a mostrar o <strong>Status Resultante</strong> da matriz abaixo, que cruza o mérito vigente{' '}
                    <strong>antes</strong> dos embargos com o resultado lançado. Casamento por nome: as tabelas de 1G e
                    2G têm IDs diferentes para os valores novos.
                </DiffBox>

                <DocTable
                    head={['Status vigente (antes dos embargos)', 'Resultado dos embargos', 'Status Resultante']}
                    rows={(
                        [
                            {
                                'Status vigente (antes dos embargos)': 'Procedente (com ou sem PE)',
                                'Resultado dos embargos': 'Reverteu Procedência',
                                'Status Resultante': '⚠ Revisar Classificação',
                            },
                            {
                                'Status vigente (antes dos embargos)': '',
                                'Resultado dos embargos': 'Reverteu Improcedência',
                                'Status Resultante': 'Revertido Perda',
                            },
                            {
                                'Status vigente (antes dos embargos)': '',
                                'Resultado dos embargos': 'Aumentou a Condenação',
                                'Status Resultante': 'Ganho Ampliado',
                            },
                            {
                                'Status vigente (antes dos embargos)': '',
                                'Resultado dos embargos': 'Reduziu a Condenação',
                                'Status Resultante': 'Ganho Reduzido',
                            },
                            {
                                'Status vigente (antes dos embargos)': 'Parcialmente procedente',
                                'Resultado dos embargos': 'Reverteu Procedência',
                                'Status Resultante': 'Ganho Ampliado',
                            },
                            {
                                'Status vigente (antes dos embargos)': '',
                                'Resultado dos embargos': 'Reverteu Improcedência',
                                'Status Resultante': 'Revertido Perda',
                            },
                            {
                                'Status vigente (antes dos embargos)': '',
                                'Resultado dos embargos': 'Aumentou a Condenação',
                                'Status Resultante': 'Ganho Ampliado',
                            },
                            {
                                'Status vigente (antes dos embargos)': '',
                                'Resultado dos embargos': 'Reduziu a Condenação',
                                'Status Resultante': 'Ganho Reduzido',
                            },
                            {
                                'Status vigente (antes dos embargos)': 'Improcedente / prescrição',
                                'Resultado dos embargos': 'Reverteu Procedência',
                                'Status Resultante': 'Revertido Ganho',
                            },
                            {
                                'Status vigente (antes dos embargos)': '',
                                'Resultado dos embargos': 'Reverteu Improcedência',
                                'Status Resultante': '⚠ Revisar Classificação',
                            },
                            {
                                'Status vigente (antes dos embargos)': '',
                                'Resultado dos embargos': 'Aumentou a Condenação',
                                'Status Resultante': '⚠ Revisar Classificação',
                            },
                            {
                                'Status vigente (antes dos embargos)': '',
                                'Resultado dos embargos': 'Reduziu a Condenação',
                                'Status Resultante': '⚠ Revisar Classificação',
                            },
                            {
                                'Status vigente (antes dos embargos)': 'Qualquer mérito',
                                'Resultado dos embargos':
                                    'Pendência Saneada / Prejudicados / Rejeitados / Não Conhecidos',
                                'Status Resultante': 'Status Mantido',
                            },
                            {
                                'Status vigente (antes dos embargos)': 'Extinto, Sentença Anulada ou sem mérito',
                                'Resultado dos embargos': 'Demais resultados',
                                'Status Resultante': '⚠ Revisar Classificação',
                            },
                        ] as Record<string, React.ReactNode>[]
                    ).map((r) =>
                        ['Status vigente (antes dos embargos)', 'Resultado dos embargos', 'Status Resultante'].map(
                            (c) => r[c],
                        ),
                    )}
                />

                <WatchBox title="O mérito de hoje já é o pós-embargo">
                    O LexFlow atualiza {mono('id_sentenca_merito_grau1')} na mesma edição em que lança o resultado do
                    embargo (validado no {mono('processo_audit')}: num caso "Reverteu Improcedência", o mérito foi de
                    Procedente para Improcedente no mesmo instante). Por isso o "antes" vem do histórico: a query{' '}
                    {mono('julgados')}
                    traz {mono('ID_SENTENCA_MERITO_1G_PRE_EMBARGOS')} = último valor do mérito no{' '}
                    {mono('processo_audit')} antes do lançamento do resultado atual (sem histórico, o mérito atual).
                    Calculado só para os processos com resultado lançado, sem custo perceptível na query. Embargado{' '}
                    <strong>sem</strong> resultado lançado continua na estimativa antiga (abaixo), rotulado à parte como
                    "Revertido (estimado)"/"Mantido (estimado)". Em 06/10/2026 — NG: 93 com resultado lançado (todas
                    "Status Mantido": 83 Prejudicados, 5 Pendência Saneada, 5 Não Conhecidos); LA: nenhuma ainda.
                </WatchBox>

                <DiffBox title='Ajuste — 06/10/2026: eixo de data dos embargos e fatia "Sem resultado lançado"'>
                    A pizza "Resultado dos embargos" e os contadores Embargados/Revertidos passaram a usar como período
                    a <strong>data da sentença de embargos</strong> ({mono('SENTENCA_EMBARGOS')}), não a data da
                    sentença original ({mono('DATA_SENTENCA')}), que costuma ser de meses antes. Exemplo que motivou:
                    setembro/2026 no NG tem 13 sentenças de embargos com resultado lançado (datas 01–18/09, sentenças
                    originais de mar–jun), e o gráfico mostrava 10 processos <em>diferentes</em> (sentenças proferidas
                    em setembro). Embargo com data e sem resultado lançado vira uma fatia própria,{' '}
                    <strong>"Sem resultado lançado"</strong>, sem estimativa (setembro/2026 NG: 182). A estimativa pelo
                    mérito atual descrita abaixo <strong>não é mais usada</strong> (nem no Acórdão, que recebeu o mesmo
                    ajuste). Sem período selecionado, entram todas as embargadas, inclusive as com resultado e sem data
                    de embargo.
                </DiffBox>

                <DiffBox title="Novidade — 06/10/2026: tempo médio sentença → embargos">
                    Abaixo da pizza "Resultado dos embargos": média de dias entre {mono('DATA_SENTENCA')} e a data da
                    sentença de embargos ({mono('SENTENCA_EMBARGOS')}), no mesmo recorte da pizza (embargo com data no
                    período), só com as duas datas e embargo ≥ sentença. Campo{' '}
                    {mono('julgados_sentenca_embargos_tempo_medio_dias_NG/LA')}. Setembro/2026 NG: 182,8 dias (205
                    sentenças, conferido direto no banco).
                </DiffBox>

                <WatchBox title="Histórico: estimativa (não é mais usada desde 06/10/2026)">
                    A planilha de origem também previu um campo de <em>resultado</em> do embargo —{' '}
                    {mono('id_sentenca_embargos_grau1')}, apontando para a tabela{' '}
                    {mono('sentenca_embargos_primeiro_grau')} (valores como "REVERTEU PROCEDÊNCIA"/"REVERTEU
                    IMPROCEDÊNCIA") — mas esse campo ficou 100% vazio até out/2026, só a data de embargo era preenchida.
                    Como proxy, assume-se que o campo de mérito é atualizado para refletir o resultado pós-embargo
                    quando ele ocorre — checado ao vivo contra o banco em 15/09/2026 antes de implementar. Se o campo
                    oficial passar a ser preenchido, a lógica de "Revertido" deve trocar para lê-lo diretamente em vez
                    do proxy.
                </WatchBox>

                <h3 className="doc-h3">Contagem em 15/09/2026 (sem filtro de período)</h3>
                <DocTable
                    head={['Dashboard', 'Embargadas', 'Revertidas', 'Mantidas']}
                    rows={(
                        [
                            {
                                Dashboard: <span className="doc-tag">NG</span>,
                                Embargadas: '489',
                                Revertidas: '110',
                                Mantidas: '379',
                            },
                            {
                                Dashboard: <span className="doc-tag">LA</span>,
                                Embargadas: '9',
                                Revertidas: '6',
                                Mantidas: '3',
                            },
                        ] as Record<string, React.ReactNode>[]
                    ).map((r) => ['Dashboard', 'Embargadas', 'Revertidas', 'Mantidas'].map((c) => r[c]))}
                />

                <p>
                    Na tela, "Embargados" e "Revertidos" aparecem como cards ao lado dos demais indicadores (Total,
                    Procedentes, Improcedentes, Extintos, Valor procedentes), e o gráfico de pizza "Resultado dos
                    embargos" mostra a proporção Revertido × Mantido, na mesma fileira dos cards — clicável, filtra a
                    página igual aos outros gráficos ({mono('resultado_embargos_julgados')}). Liminar (
                    {mono('id_liminar_grau1')}) ficou fora de escopo — 100% vazio no banco e sem coluna de data
                    equivalente à de embargos.
                </p>
            </DocSection>

            <DocSection id="ranking" title="Ranking de Juízes" subtitle="Exige nome preenchido E mérito classificável">
                <InfoBox>
                    O ranking exige <strong>duas</strong> condições por linha: nome preenchido (<Code>JUIZ_1G</Code>){' '}
                    <em>e</em> mérito classificável (todos os 7 valores contam — não há "não classificados" na
                    Sentença).
                </InfoBox>

                <WatchBox title="Fonte do nome é o campo de texto livre do processo, não o cadastro (FK)">
                    <Code>JUIZ_1G</Code> vem de <Code>processo.juiz_1g</Code>, um campo de texto livre. A tabela{' '}
                    <Code>processo</Code> também tem uma FK para o cadastro normalizado (<Code>juiz_primeiro_grau</Code>
                    ), mas ela <strong>não é usada</strong> aqui: por decisão de negócio, o texto livre é a fonte
                    oficial para todas as análises de juiz nesses dashboards (<span>ver</span> histórico abaixo).
                </WatchBox>

                <DocTable
                    head={['Dashboard', 'Total (set/2026)', 'Com juiz', '% faltando']}
                    rows={(
                        [
                            {
                                Dashboard: <span className="doc-tag">LA</span>,
                                'Total (set/2026)': '417',
                                'Com juiz': '417',
                                '% faltando': '0,0%',
                            },
                            {
                                Dashboard: <span className="doc-tag">NG</span>,
                                'Total (set/2026)': '377',
                                'Com juiz': '376',
                                '% faltando': '0,3%',
                            },
                        ] as Record<string, React.ReactNode>[]
                    ).map((r) => ['Dashboard', 'Total (set/2026)', 'Com juiz', '% faltando'].map((c) => r[c]))}
                />

                <p>
                    O aviso "Existem X processo(s) sem o nome do juiz!" no topo da página reflete essa mesma lacuna
                    (conta sobre a base inteira do período, não só a classificada). Como a fonte agora é o texto livre —
                    mais preenchido que o cadastro —, a lacuna é bem menor do que era quando o cadastro (FK) era a fonte
                    oficial.
                </p>

                <DiffBox title="Histórico — 26/09/2026 → 28/09/2026: idas e vindas entre cadastro (FK) e texto livre">
                    Em 26/09/2026 foi implementado um fallback pro texto livre ({mono('juiz_1g')}) quando o cadastro
                    (FK) estava vazio, depois <strong>revertido</strong> no mesmo dia a pedido do usuário: a regra
                    passou a ser "só cadastro, nunca texto livre, nem na query base". Em 28/09/2026 o usuário{' '}
                    <strong>reverteu de novo</strong>, no sentido oposto: agora é o texto livre (
                    {mono('processo.juiz_1g')}/{mono('processo.relator_2g')}) a fonte oficial para juiz e relator em
                    todas as análises destes dashboards, e o cadastro (FK, {mono('juiz_primeiro_grau')}/
                    {mono('relator_segundo_grau')}) não é mais usado. A query {mono('julgados')} foi ajustada para
                    selecionar {mono('p.juiz_1g')}/{mono('p.relator_2g')} diretamente, sem os JOINs para as tabelas de
                    cadastro.
                </DiffBox>
            </DocSection>

            <DocSection
                id="estudos-extincao"
                title="Estudos de Extinção"
                subtitle="Comarca, valor de causa e juiz por trás das sentenças extintas"
            >
                <InfoBox>
                    Seção dedicada (28/09/2026), abaixo da tabela de sentenças do período, com 3 análises sobre
                    sentenças extintas: por comarca (mapa coroplético com quantidade e valor de causa), por motivo e por
                    juiz. Pode ser recolhida com o botão "Ocultar"/"Mostrar" e é independente do resto da página — tem
                    seu próprio alternador de escopo.
                </InfoBox>

                <WatchBox title='Alternador "Total (estoque)" / "Entrada no período"'>
                    Cada uma das 3 análises (e os 2 cards de total/valor) tem duas versões:{' '}
                    <strong>Total (estoque)</strong> ignora o filtro de data do topo da página e soma <em>toda</em> a
                    base já sentenciada com {mono('DATA_SENTENCA')} preenchida; <strong>Entrada no período</strong> usa
                    o mesmo intervalo de data selecionado no resto da página. As duas vêm prontas na mesma resposta da
                    API — trocar o alternador não dispara uma nova requisição, é só troca de qual array já carregado é
                    exibido.
                </WatchBox>

                <DiffBox title="Histórico — 29/09/2026: comarca virou mapa coroplético">
                    Inicialmente "Extinções por comarca" e "Valor das extinções por comarca" eram 2 gráficos de barra
                    separados. Substituídos por um único mapa (<Code>ComarcaMapaMultiUfChart</Code> no NG,{' '}
                    <Code>ComarcaMapaChart</Code> no LA — o mesmo componente já usado no dashboard de Execução), que
                    mostra as duas informações juntas: cor/tamanho do município pela quantidade (raiz quadrada) e o
                    valor de causa no tooltip ao passar o mouse. NG usa a variante multi-UF (7 estados hoje: AC, AM, BA,
                    MA, PA, PB, RJ — cada comarca é casada com o estado certo por um voto de maioria de {mono('UF')} na
                    base completa do escritório); LA usa a variante de estado único (Amazonas, escritório é só AM).
                </DiffBox>

                <DiffBox title="Histórico — 29/09/2026: legenda ganhou comparativo Capital × Interior">
                    A legenda do mapa (abaixo do mapa em si) ganhou uma linha "Capital × Interior": soma da quantidade
                    de extinções na comarca capital de cada UF exibida vs. todas as outras comarcas (Interior), em
                    quantidade e percentual — calculado no frontend a partir dos mesmos dados já carregados pelo mapa
                    (nenhum campo novo de API). Capitais configuradas hoje: AM → Manaus, PA → Belém, PB → João Pessoa,
                    AC → Rio Branco, BA → Salvador, MA → São Luís, RJ → Rio de Janeiro (NG); LA usa só Manaus (única
                    capital possível, escritório é Amazonas). "Sem comarca" fica fora dos dois lados do comparativo.
                </DiffBox>

                <DiffBox title="Histórico — 29/09/2026: legenda ganhou % de extinções revertidas em 2G, e virou 3 colunas">
                    Quando uma sentença é extinta em 1G, o processo sobe para 2G tentando reverter a extinção. A legenda
                    ganhou um bloco (cor verde, distinta do laranja/cinza do Capital × Interior) mostrando que fração
                    das extinções do escopo já tiveram o acórdão do <strong>mesmo processo</strong> em 2G com mérito{' '}
                    {mono('Sentença Anulada')} (mérito 8, exclusivo do 2G na Matriz de Julgamento — ver{' '}
                    <a href="#classificacao">Classificação de mérito</a>) — indício de que a extinção foi revertida.
                    Como a query {mono('julgados')} já traz 1G e 2G na mesma linha (mesmo processo), não precisa de
                    cruzamento: é só ler {mono('ID_ACORDAO_MERITO_2G')} da mesma linha da sentença extinta. O
                    denominador é o total de extinções do escopo, <strong>incluindo</strong> as que ainda não têm
                    acórdão julgado em 2G — por isso o percentual tende a ser baixo (a maioria dos recursos ainda está
                    em andamento). Validado ao vivo no banco antes de implementar: de ~4.100 sentenças extintas (campo
                    novo, histórico completo, sem recorte de escritório), 838 já tinham acórdão julgado em 2G e 63 delas
                    eram "Sentença Anulada". A legenda passou a ter <strong>3 colunas</strong>: a 1ª com a legenda
                    original do mapa (bolinhas de cor, intensidade, total pintado, estados exibidos), a 2ª com Capital ×
                    Interior, a 3ª com este bloco de Revertidas em 2G — cada uma com sua própria frase de proporção ("a
                    cada 10 processos julgados, X são extintos" na 2ª; "a cada 10 processos extintos, Y tem sentença
                    anulada no 2ºG" na 3ª).
                </DiffBox>

                <DiffBox title="Histórico — 29/09/2026: tempo médio por comarca no tooltip do mapa">
                    O tooltip do mapa (ao passar o mouse num município) já existia no componente compartilhado com a
                    Execução e sabia mostrar "Tempo médio", mas o backend de Julgados Sentença nunca preenchia esse
                    campo — aparecia sempre vazio. Adicionado {mono('tempo_medio_dias')} em cada item de{' '}
                    {mono('julgados_extincao_por_comarca_NG')}/{mono('julgados_extincao_por_comarca_estoque_NG')}
                    (e equivalentes LA): média de dias entre {mono('DATA_AJUIZAMENTO')} e {mono('DATA_SENTENCA')} da
                    comarca, calculada sobre o histórico completo do escritório (todas as sentenças da comarca com as
                    duas datas preenchidas, sem filtro de categoria ou de período) — mesmo padrão de{' '}
                    {mono('group_execucao_por_comarca')}: é fixo por comarca e não muda com o alternador
                    estoque/entrada, serve de referência estável de "quanto tempo uma sentença dessa comarca costuma
                    levar". <Code>null</Code> quando a comarca não tem nenhuma sentença com as duas datas preenchidas.
                </DiffBox>

                <DocTable
                    head={['Análise', 'Campo (entrada)', 'Campo (estoque)']}
                    rows={(
                        [
                            {
                                Análise: 'Mapa de extinções por comarca (qtd. + valor)',
                                'Campo (entrada)': mono('julgados_extincao_por_comarca_NG'),
                                'Campo (estoque)': mono('julgados_extincao_por_comarca_estoque_NG'),
                            },
                            {
                                Análise: 'Motivo das extinções',
                                'Campo (entrada)': mono('julgados_por_motivo_extincao_NG'),
                                'Campo (estoque)': mono('julgados_extincao_por_motivo_estoque_NG'),
                            },
                            {
                                Análise: 'Juízes que mais extinguem',
                                'Campo (entrada)': mono('julgados_extincao_por_juiz_NG'),
                                'Campo (estoque)': mono('julgados_extincao_por_juiz_estoque_NG'),
                            },
                            {
                                Análise: 'Extinções revertidas em 2G (contagem)',
                                'Campo (entrada)': mono('julgados_extincao_revertida_2g_NG'),
                                'Campo (estoque)': mono('julgados_extincao_revertida_2g_estoque_NG'),
                            },
                        ] as Record<string, React.ReactNode>[]
                    ).map((r) => ['Análise', 'Campo (entrada)', 'Campo (estoque)'].map((c) => r[c]))}
                />
                <p>
                    O mapa usa o mesmo campo de comarca em dois papéis: {mono('julgados_extincao_por_comarca_NG')} vira
                    tanto a "quantidade" (cor/tamanho do município) quanto a fonte do "valor" (tooltip) — o valor não
                    tem um campo de resposta separado, é o mesmo array com {mono('valor_causa')} lido em vez de{' '}
                    {mono('value')}. O universo de comarcas conhecidas (para diferenciar "zero no filtro" de "fora da
                    base" no mapa) vem de {mono('julgados_comarca_opcoes_NG')}, histórico completo do escritório sem
                    filtro de data.
                </p>

                <p>
                    O card "Valor das Extinções" e o valor mostrado no tooltip do mapa somam{' '}
                    {mono('VALOR_CAUSA_SENTENCA')} ({mono('processo.valor_causa')}) — o valor <strong>inicial</strong>{' '}
                    da causa, o mesmo protocolado no início do processo e sincronizado automaticamente do protocolo, o
                    mesmo campo já usado no card "Valor sentenças procedentes" da seção acima. Não é um valor de
                    condenação ou de extinção em si (não existe esse campo separado no banco).
                </p>

                <DiffBox title="Histórico — 29/09/2026: corrigida a fonte do valor de causa">
                    Até essa data, {mono('VALOR_CAUSA_SENTENCA')} vinha de {mono('processo.valor_causa_vs')} — um campo{' '}
                    <strong>separado</strong> do valor de causa inicial, majoritariamente vazio (só 16.181 de ~100 mil
                    processos preenchidos) e, quando preenchido, divergente do valor inicial em{' '}
                    <strong>~93% dos casos</strong> (validado ao vivo no banco: muitas vezes {mono('0')} enquanto{' '}
                    {mono('processo.valor_causa')} tinha o valor real protocolado). Corrigido para usar{' '}
                    {mono('processo.valor_causa')} diretamente na query {mono('julgados')} — mesma correção aplicada em
                    Acórdãos ({mono('VALOR_CAUSA_ACORDO')}). O valor total de extinções (estoque) do NG saltou de ~R$
                    294 mil para ~R$ 56 milhões após a correção — o número antigo estava drasticamente subcontado, não é
                    uma mudança de critério.
                </DiffBox>

                <p>
                    No gráfico "Motivo das extinções", quando um processo é marcado como extinto no LexFlow, abre-se um
                    campo livre para o colaborador registrar o motivo — esse texto vem de{' '}
                    {mono('id_motivo_status_grau1')}, que aponta para {mono('motivo_status_grau.description')} (tabela
                    escopada por escritório e grau). O agrupador pré-filtra a base para só as sentenças extintas (mesmo
                    critério do card "Extintos": mérito {mono('7')}) antes de agrupar por motivo.
                </p>

                <p>
                    Clicar num município do mapa ou numa barra dos outros 2 gráficos desta seção filtra a página inteira
                    pelo mesmo mecanismo dos demais gráficos — comarca, motivo da extinção e juiz reaproveitam
                    exatamente os filtros interativos já existentes (<span>ver</span>{' '}
                    <a href="#filtros">Filtros interativos</a>), não são filtros novos.
                </p>

                <DiffBox title="Histórico — 28/09/2026: gráfico de motivo saiu da seção principal">
                    O gráfico "Motivo das extinções" existia antes na seção "Sentença (1º Grau)" (junto de "por
                    competência" e "por comarca"), sempre restrito ao período selecionado. Ele foi movido para esta
                    seção nova, onde ganhou a opção de ver o estoque completo além do período — a linha da grade
                    principal que tinha 3 colunas (competência/comarca/motivo) passou a ter 2 (competência/comarca).
                </DiffBox>
            </DocSection>

            <DocSection
                id="exportacao"
                title="Exportação de relatório"
                subtitle='Botão "Relatório" ao lado do seletor de UF'
            >
                <InfoBox>
                    Diálogo de um passo só — escolha de campos — que gera CSV ou XLSX no servidor, usando exatamente o
                    mesmo pipeline de filtro e período já aplicado na tela. Nenhum filtro é reconfigurado dentro do
                    diálogo.
                </InfoBox>
                <DocTable
                    head={['Dashboard', 'Endpoint']}
                    rows={(
                        [
                            { Dashboard: 'Sentença LA', Endpoint: mono('GET /api/dashboard/julgados_LA/export') },
                            { Dashboard: 'Sentença NG', Endpoint: mono('GET /api/dashboard/julgados_NG/export') },
                        ] as Record<string, React.ReactNode>[]
                    ).map((r) => ['Dashboard', 'Endpoint'].map((c) => r[c]))}
                />
                <p>
                    Campos exportáveis vêm da query <Code>julgados</Code> (número do processo, matéria, competência,
                    comarca, UF, fase, subfase, juiz, status bruto (1G), motivo da extinção, data de distribuição, data
                    da sentença, data e status da sentença de embargos), mais <strong>uma coluna calculada</strong>:
                    "Resultado do Embargo (estimado)" — ver abaixo.
                </p>

                <DiffBox title="Novidade — 15/09/2026">
                    Adicionados os campos "Data da Sentença de Embargos" (grupo "Datas") e "Status da Sentença de
                    Embargos" (grupo "Julgamento (1º Grau)") ao diálogo de exportação, espelhando{' '}
                    {mono('SENTENCA_EMBARGOS')} (data) e {mono('STATUS_SENTENCA_EMBARGOS')} (status, via novo JOIN com{' '}
                    {mono('sentenca_embargos_primeiro_grau')}) — mesmos campos usados pelos cards de{' '}
                    <a href="#embargos">Embargos e reversão</a>.
                </DiffBox>

                <WatchBox title="Coluna de status vem vazia hoje">
                    Como explicado na seção <a href="#embargos">Embargos e reversão</a>, o campo oficial de resultado do
                    embargo está 100% vazio no banco em 15/09/2026 — a coluna "Status da Sentença de Embargos" no
                    relatório vai sair em branco para <strong>todas</strong> as linhas até que o LexFlow comece a
                    preencher esse dado na origem. Ela foi adicionada mesmo assim porque é um campo real da query,
                    pronta para quando passar a ser preenchida.
                </WatchBox>

                <DiffBox title='Novidade — 16/09/2026: coluna calculada "Resultado do Embargo (estimado)"'>
                    Como o campo oficial de status está sempre vazio, quem baixava o relatório não conseguia dizer, só
                    pela data de embargo, se a sentença tinha revertido ou não. Adicionado o campo{' '}
                    <strong>"Resultado do Embargo (estimado)"</strong> (grupo "Julgamento (1º Grau)"), preenchido com
                    "Revertido"/"Mantido" para sentenças embargadas (vazio para as demais) — mesmo proxy usado nos cards
                    e no gráfico "Resultado dos embargos": embargada e mérito atual procedente = Revertido; embargada e
                    mérito atual não-procedente = Mantido. Calculado no momento da exportação (
                    {mono('_anotar_resultado_embargos_export')} em {mono('dashboard_routes.py')}), reusando o mesmo
                    getter do dashboard — não é uma coluna nova no banco.
                </DiffBox>

                <DiffBox title="Histórico — corrigido em 26/08/2026">
                    Na primeira versão, o export aplicava os filtros de matéria/juiz/etc. mas esquecia o recorte de
                    escritório (<Code>_base_julgados_NG</Code>/<Code>_base_julgados_LA</Code>), que na tela só é
                    aplicado dentro das funções de KPI/gráfico. Resultado: exportar do NG trazia junto sentenças da LA
                    (e vice-versa) que batessem com o mesmo filtro. Corrigido aplicando o mesmo recorte de escritório
                    antes do filtro categórico, igual ao dashboard.
                </DiffBox>

                <DiffBox title='Novidade — 21/10/2026: coluna "Valor da Sentença" e aviso de valor faltando'>
                    O relatório ganhou a coluna "Valor da Sentença" (slug {mono('valor_sentenca')},{' '}
                    {mono('VALOR_SENTENCA')} = {mono('processo.valor_causa_vs')}), o valor fixado na sentença —
                    diferente do valor de causa inicial. A coluna não tem descrição no banco; o significado foi
                    confirmado pelos dados (valor &gt; 0 em 2.600 de 2.867 Procedentes com PE e quase zero em
                    improcedentes/extintos). Sai como moeda: número com formato R$ no XLSX (somável) e texto "R$
                    1.234,56" no CSV. A barra de aviso no topo também passou a contar sentenças procedentes com proveito
                    econômico (mérito 1 ou 3) sem o valor da sentença (vazio ou zero), e esses processos entram na lista
                    clicável com o campo "Valor da sentença".
                </DiffBox>
            </DocSection>

            <DocSection
                id="notas"
                title="Notas e pendências conhecidas"
                subtitle="Detalhes técnicos que ajudam a diagnosticar divergências futuras"
            >
                <DocGrid>
                    <DocCard title="Ranking nunca soma ao total do card">
                        <p>
                            É esperado, não bug: <span>Total</span> conta tudo no período; o ranking exclui
                            adicionalmente quem não tem juiz — por isso soma menos que o total.
                        </p>
                    </DocCard>
                    <DocCard title="Comparação de casing nos filtros">
                        <p>
                            Matéria/comarca/competência/motivo comparam por <Code>casefold()</Code> (case insensitive);
                            UF é normalizada para maiúsculas antes de comparar. Um valor com espaço a mais ou acento
                            diferente no banco não é normalizado e vira uma opção separada no filtro.
                        </p>
                    </DocCard>
                    <DocCard title='"Revertido" nos embargos é estimado, não o campo oficial'>
                        <p>
                            Ver <a href="#embargos">Embargos e reversão</a> — o campo oficial (
                            {mono('id_sentenca_embargos_grau1')}) ainda está 100% vazio no banco. Se for preenchido no
                            futuro, a lógica de "Revertido" precisa migrar do proxy (mérito atual) para o campo oficial.
                        </p>
                    </DocCard>
                    <DocCard title="Juiz vem do texto livre do processo, não do cadastro (FK)">
                        <p>
                            Ver <a href="#ranking">Ranking de Juízes</a> — {mono('processo.juiz_1g')} (texto livre) é a
                            fonte oficial por decisão de negócio; o cadastro normalizado ({mono('juiz_primeiro_grau')})
                            não é usado em nenhuma análise. Não confundir com o campo de export "Status da Sentença de
                            Embargos", que é outra coisa.
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>
        </DocPage>
    )
}
