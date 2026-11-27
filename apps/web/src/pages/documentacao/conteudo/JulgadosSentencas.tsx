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

// Guia trazido da v1: LexHub/src/pages/documentacao/JulgadosSentenca.tsx (convertido para as peças da V2).

const mono = (text: string) => <Code>{text}</Code>

const unit = (code: string) => (
    <DocPill tone="accent" mono>
        {code}
    </DocPill>
)

const TOC: TocItem[] = [
    { id: 'visao-geral', label: 'Visão geral' },
    { id: 'classificacao', label: 'Classificação de mérito' },
    { id: 'filtros', label: 'Filtros interativos' },
    { id: 'tempo-medio', label: 'Tempo médio até a sentença' },
    { id: 'embargos', label: 'Embargos e reversão' },
    { id: 'ranking', label: 'Ranking de Juízes' },
    { id: 'estudos-extincao', label: 'Estudos de Extinção' },
    { id: 'estudo-improcedencias', label: 'Estudo das Improcedências' },
    { id: 'exportacao', label: 'Exportação de relatório' },
    { id: 'notas', label: 'Notas e pendências' },
]

// Status Resultante da matriz de embargos -> cor do selo.
const RESULTANTE_TONE: Record<string, Tone> = {
    '⚠ Revisar Classificação': 'warn',
    'Revertido Perda': 'danger',
    'Revertido Ganho': 'ok',
    'Ganho Ampliado': 'ok',
    'Ganho Reduzido': 'info',
    'Status Mantido': 'neutral',
}

const resultante = (text: string) => <DocPill tone={RESULTANTE_TONE[text] ?? 'neutral'}>{text}</DocPill>

const MATRIZ_EMBARGOS: [string, string, string][] = [
    ['Procedente (com ou sem PE)', 'Reverteu Procedência', '⚠ Revisar Classificação'],
    ['', 'Reverteu Improcedência', 'Revertido Perda'],
    ['', 'Aumentou a Condenação', 'Ganho Ampliado'],
    ['', 'Reduziu a Condenação', 'Ganho Reduzido'],
    ['Parcialmente procedente', 'Reverteu Procedência', 'Ganho Ampliado'],
    ['', 'Reverteu Improcedência', 'Revertido Perda'],
    ['', 'Aumentou a Condenação', 'Ganho Ampliado'],
    ['', 'Reduziu a Condenação', 'Ganho Reduzido'],
    ['Improcedente / prescrição', 'Reverteu Procedência', 'Revertido Ganho'],
    ['', 'Reverteu Improcedência', '⚠ Revisar Classificação'],
    ['', 'Aumentou a Condenação', '⚠ Revisar Classificação'],
    ['', 'Reduziu a Condenação', '⚠ Revisar Classificação'],
    ['Qualquer mérito', 'Pendência Saneada / Prejudicados / Rejeitados / Não Conhecidos', 'Status Mantido'],
    ['Extinto, Sentença Anulada ou sem mérito', 'Demais resultados', '⚠ Revisar Classificação'],
]

const FILTROS: [string, string, string][] = [
    ['Matéria', 'materia_julgados', 'gráfico de pizza'],
    ['Juiz (1G)', 'juiz_julgados', 'ranking'],
    ['Comarca', 'comarca_julgados', 'barra'],
    ['Competência', 'competencia_julgados', 'barra'],
    ['Categoria', 'categoria_julgados', 'stat cards'],
    ['UF', 'uf_julgados', 'dropdown no cabeçalho'],
    ['Motivo da extinção', 'motivo_extincao_julgados', 'barra (só extintos)'],
    ['Ano de ajuizamento', 'ano_ajuizamento_julgados', 'donut'],
    ['Resultado dos embargos', 'resultado_embargos_julgados', 'donut (ver seção Embargos)'],
]

const ESTUDOS: [string, string, string][] = [
    [
        'Mapa de extinções por comarca (qtd. + valor)',
        'julgados_extincao_por_comarca_NG',
        'julgados_extincao_por_comarca_estoque_NG',
    ],
    ['Motivo das extinções', 'julgados_por_motivo_extincao_NG', 'julgados_extincao_por_motivo_estoque_NG'],
    ['Juízes que mais extinguem', 'julgados_extincao_por_juiz_NG', 'julgados_extincao_por_juiz_estoque_NG'],
    [
        'Extinções revertidas em 2G (contagem)',
        'julgados_extincao_revertida_2g_NG',
        'julgados_extincao_revertida_2g_estoque_NG',
    ],
]

// Um valor da escala de mérito 1G: número em fonte de código e o nome.
function Merito({ n, children }: { n: string; children: ReactNode }) {
    return (
        <li>
            {mono(n)} {children}
        </li>
    )
}

export function JulgadosSentencasDoc() {
    return (
        <DocPage
            title="Julgados — Sentenças"
            tags={['NG', 'LA', 'RJ']}
            note="Mesmo cálculo nas três unidades, 1 query só"
            toc={TOC}
            intro={
                <>
                    Como o dashboard de Sentenças (1º Grau, no NG, no LA e no RJ) classifica um resultado pela Matriz de
                    Julgamento (mérito), calcula o ranking de juízes, o tempo médio até a sentença e a reversão por
                    embargos, e por que a grande maioria dos processos não tem juiz preenchido no banco — validado com
                    dados reais, não é bug de tela.
                </>
            }
            header={
                <DocCallout caps title="Uma query, três unidades" badge="julgados">
                    <p>
                        A query <Code>julgados</Code> (compartilhada com os dashboards de Acórdãos) traz processos de{' '}
                        <strong>todos os escritórios</strong> — não tem filtro de escritório no SQL. O recorte por
                        escritório (NG = 20, LA = 21, RJ = 27) é feito depois, em Python, por{' '}
                        <Code>_base_julgados_NG()</Code> / <Code>_base_julgados_LA()</Code> /{' '}
                        <Code>_base_julgados_RJ()</Code> — uma função por módulo, chamada dentro de cada
                        KPI/ranking/gráfico. Na V2 é um dashboard só (<Code>julgados-sentencas</Code>); a unidade
                        escolhida no seletor define qual módulo roda. Na tela, LA aparece como LAAM e RJ como LARJ.
                    </p>
                    <DocGrid cols={3}>
                        <DocMini label="LA">
                            Escritório <Hl mono>21</Hl> · {mono('LA/julgados_sentenca_LA.py')}
                        </DocMini>
                        <DocMini label="NG">
                            Escritório <Hl mono>20</Hl> · {mono('NG/julgados_sentenca.py')}
                        </DocMini>
                        <DocMini label="RJ">
                            Escritório <Hl mono>27</Hl> · {mono('RJ/julgados_sentenca_RJ.py')}
                        </DocMini>
                    </DocGrid>
                </DocCallout>
            }
        >
            <DocSection
                id="visao-geral"
                title="01 — Visão geral"
                subtitle="Um dashboard em cada unidade (NG, LA e RJ), uma query só por trás de todos"
                badge="1º Grau"
            >
                <DocTable
                    head={['Dashboard', 'Grau', 'Eixo de data', 'Tabela de mérito', 'Módulo backend']}
                    rows={[
                        [
                            <>Julgados Sentenças {unit('LA')}</>,
                            '1G',
                            mono('DATA_SENTENCA'),
                            mono('sentenca_merito_primeiro_grau'),
                            mono('LA/julgados_sentenca_LA.py'),
                        ],
                        [
                            <>Julgados Sentenças {unit('NG')}</>,
                            '1G',
                            mono('DATA_SENTENCA'),
                            mono('sentenca_merito_primeiro_grau'),
                            mono('NG/julgados_sentenca.py'),
                        ],
                        [
                            <>Julgados Sentenças {unit('RJ')}</>,
                            '1G',
                            mono('DATA_SENTENCA'),
                            mono('sentenca_merito_primeiro_grau'),
                            mono('RJ/julgados_sentenca_RJ.py'),
                        ],
                    ]}
                />
                <DocGrid cols={2}>
                    <DocFeature title='O card "Total"' tone="info" icon="barChart" badge="Sem card Não classificados">
                        <p>
                            O card "Total" conta todos os processos sentenciados no período, sem exigir status
                            classificável. Procedentes/Improcedentes/Extintos são subconjuntos desse total. Ao contrário
                            do Acórdão, a Sentença não tem um card "Não classificados" — a escala de mérito 1G cobre
                            100% das variações possíveis (ver próxima seção), então o resíduo é só mérito ainda não
                            lançado.
                        </p>
                    </DocFeature>
                    <DocFeature
                        title="Fallback para o status antigo"
                        tone="warn"
                        icon="history"
                        badge="status_primeiro_grau"
                    >
                        <p>
                            Quando a coluna de mérito nova está vazia, a classificação lê do status antigo (
                            {mono('status_primeiro_grau')}) — ver <a href="#classificacao">Classificação de mérito</a>.
                        </p>
                    </DocFeature>
                </DocGrid>
                <DocCallout tone="neutral" icon="book" title="Documentação irmã">
                    <p>
                        <DocLink to="julgados-acordaos">Julgados — Acórdãos</DocLink> (2º Grau) — mesma query e boa
                        parte da mesma lógica, mas com card "Não classificados", ranking de relatores em vez de juízes e
                        sem o card de tempo médio.
                    </p>
                </DocCallout>
                <DocChange status="06/11/2026" tone="danger" area="Regra" title="Agravos fora das análises" framed>
                    Processos cujo número CNJ termina em <Code>0000</Code>, <Code>9000</Code>, <Code>9001</Code> ou{' '}
                    <Code>9002</Code> (código de origem nos 4 últimos dígitos) são recursos de agravo e não entram em
                    nenhuma contagem deste dashboard: totais, procedentes/improcedentes/extintos, gráficos, ranking,
                    embargos, estudos e o relatório exportado. A regra vale só para números com os 20 dígitos do padrão
                    (números malformados nunca são excluídos) e fica em{' '}
                    <Code>app/analyses/common/julgados_agravo.py</Code>, aplicada no filtro de base do escritório (
                    <Code>_base_julgados_NG/LA/RJ</Code>) — a mesma regra do Acórdão.
                </DocChange>
            </DocSection>

            <DocSection
                id="classificacao"
                title="02 — Classificação de mérito (Matriz de Julgamento)"
                subtitle="Migrado em 15/09/2026: sentença de mérito passou a ter campo próprio"
                badge="7 valores"
            >
                <DocCallout title="Tabela dedicada de mérito" badge="sentenca_merito_primeiro_grau">
                    <p>
                        A sentença de mérito agora lê de uma tabela nova e dedicada —{' '}
                        {mono('sentenca_merito_primeiro_grau')} — com uma escala de 7 valores. A lógica de leitura e
                        classificação é compartilhada com o Acórdão e a Recursal (LA/NG) no módulo{' '}
                        {mono('app/analyses/common/matriz_julgamento.py')}, para não duplicar regra entre módulos (o
                        Acórdão usa a mesma escala, mais um 8º valor exclusivo — ver a doc de Acórdãos).
                    </p>
                </DocCallout>

                <h3 className="doc-h3">Mérito 1G — 7 valores, todos com mérito julgado</h3>
                <DocGrid cols={3}>
                    <DocFeature title="Procedente" tone="ok" icon="check-circle" badge="1 a 4">
                        <ul>
                            <Merito n="1">Procedente com proveito econômico</Merito>
                            <Merito n="2">Procedente sem proveito econômico</Merito>
                            <Merito n="3">Parc. procedente com proveito econômico</Merito>
                            <Merito n="4">Parc. procedente sem proveito econômico</Merito>
                        </ul>
                    </DocFeature>
                    <DocFeature title="Improcedente" tone="danger" icon="x-circle" badge="5 e 6">
                        <ul>
                            <Merito n="5">Improcedente</Merito>
                            <Merito n="6">Improcedente por prescrição/decadência</Merito>
                        </ul>
                    </DocFeature>
                    <DocFeature title="Extinto" tone="neutral" icon="ban" badge="7">
                        <ul>
                            <Merito n="7">Extinto sem mérito</Merito>
                        </ul>
                    </DocFeature>
                </DocGrid>

                <DocFeature
                    title="Compatibilidade com o esquema antigo"
                    tone="info"
                    icon="refresh"
                    badge="STATUS_1G · IDs 17-23"
                    framed
                >
                    <p>
                        Enquanto o preenchimento novo não cobre 100% da base, cada linha ainda pode cair de volta no{' '}
                        {mono('STATUS_1G')} antigo (IDs 17-23): quando {mono('id_sentenca_merito_grau1')} está vazio, o
                        nome do status antigo é traduzido para o ID de mérito equivalente por <strong>nome</strong>{' '}
                        normalizado (não por ID — o esquema antigo já teve uma renomeação de IDs antes desta migração).
                        "Acordo Homologado" (eixo próprio, fora de escopo) e "Encerrado 1G" (equivale a sem recurso) não
                        têm tradução — viram mérito nulo. Validado contra os 17.185 processos com os dois campos
                        preenchidos: a tradução bate em <Hl tone="ok">{'>99,9%'}</Hl> dos casos.
                    </p>
                </DocFeature>

                <DocChange status="15/09/2026" tone="neutral" area="Histórico" title="Migração de 15/09/2026" framed>
                    Antes desta data, a classificação lia direto de {mono('status_primeiro_grau')} (IDs 17-23, sem
                    escala de mérito dedicada). A migração trocou a fonte primária pelo novo campo de mérito, mantendo o
                    fallback por nome descrito acima para não quebrar dados históricos. Junto com essa migração vieram
                    os campos de <strong>Embargos</strong> — ver seção abaixo.
                </DocChange>
            </DocSection>

            <DocSection
                id="filtros"
                title="03 — Filtros interativos"
                subtitle="Cumulativos: AND entre dimensões, OR dentro de cada uma"
                badge="Clique para filtrar"
            >
                <DocCallout tone="info" icon="filter" title="Clicar alterna o filtro">
                    <p>
                        Clicar numa fatia/barra de gráfico ou num card de categoria alterna (toggle) aquele valor no
                        filtro correspondente; os filtros ativos aparecem como chips removíveis no topo da página.
                    </p>
                </DocCallout>
                <DocTable
                    head={['Dimensão', 'Query param', 'Onde se clica']}
                    rows={FILTROS.map(([dim, param, onde]) => [dim, mono(param), onde])}
                />
                <p>
                    Frontend: <Code>pages/dashboards/julgados-sentencas/filters.ts</Code> (o mesmo para NG, LA e RJ — a
                    lógica de filtro não muda por escritório). Backend: <Code>JulgadosSentencaFiltros</Code>, comparação
                    por <Code>casefold()</Code>.
                </p>
            </DocSection>

            <DocSection
                id="tempo-medio"
                title="04 — Tempo médio até a sentença"
                subtitle="Distribuição → sentença, em dias corridos"
                badge="Dias corridos"
            >
                <DocCallout title="Do ajuizamento à sentença" badge="DATA_AJUIZAMENTO → DATA_SENTENCA" icon="clock">
                    <p>
                        Mede o intervalo entre <Code>DATA_AJUIZAMENTO</Code> (fonte: <Code>p.distribuicao</Code> — data
                        de distribuição do processo) e <Code>DATA_SENTENCA</Code>. Só entram na média pares com as duas
                        datas preenchidas e sentença ≥ ajuizamento; sem par válido, o processo é excluído (não conta
                        como zero).
                    </p>
                </DocCallout>
                <DocGrid cols={2}>
                    <DocFeature title="Variação invertida" tone="danger" icon="trend-up" badge="Subir é ruim">
                        <p>
                            Não existe equivalente no Acórdão — o pedido original era especificamente "tempo desde a
                            distribuição até a sentença". Card com variação percentual invertida: crescimento de dias é
                            ruim (mais devagar), então a variação aparece em vermelho quando sobe.
                        </p>
                    </DocFeature>
                    <DocFeature title="Amostra do mês corrente (ago/2026)" tone="info" icon="calendar">
                        <DocGrid cols={2}>
                            <DocMini label="LA">
                                <Hl mono>≈ 125 dias</Hl> (n≈260)
                            </DocMini>
                            <DocMini label="NG">
                                <Hl mono>≈ 141 dias</Hl> (n≈245)
                            </DocMini>
                        </DocGrid>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="embargos"
                title="05 — Embargos e reversão"
                subtitle="Adicionado em 15/09/2026"
                badge="Desde 15/09/2026"
            >
                <DocCallout title="Sentenças embargadas" badge="sentenca_embargos">
                    <p>
                        Quando uma sentença de mérito sai improcedente (ou improcedente por prescrição/decadência), a
                        parte pode opor embargos tentando reverter o resultado. Um campo novo de data —{' '}
                        {mono('sentenca_embargos')} — marca quando isso aconteceu; o dashboard mostra quantas sentenças
                        do período foram embargadas e, dessas, quantas reverteram.
                    </p>
                </DocCallout>

                <DocGrid cols={2}>
                    <DocFeature title="Embargado" tone="info" badge="SENTENCA_EMBARGOS">
                        <p>
                            Sentença com data de embargo ({mono('SENTENCA_EMBARGOS')}) dentro do período selecionado — o
                            eixo é a data da sentença de embargos, não a {mono('DATA_SENTENCA')} usada pelos outros
                            cards (ver o ajuste de 06/10/2026 abaixo).
                        </p>
                    </DocFeature>
                    <DocFeature title="Revertido" tone="ok" badge="Revertido Ganho">
                        <p>
                            Embargada cujo Status Resultante (matriz abaixo) é <strong>Revertido Ganho</strong>: era
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
                    O resultado do embargo ({mono('id_sentenca_embargos_grau1')} →{' '}
                    {mono('sentenca_embargos_primeiro_grau')}) começou a ser preenchido e ganhou 2 valores novos:{' '}
                    <strong>REJEITADOS</strong> e <strong>NÃO CONHECIDOS</strong>, que dão sempre "Status Mantido", em
                    qualquer sentença de mérito. A pizza "Resultado dos embargos" (e o filtro e a coluna do relatório)
                    passou a mostrar o <strong>Status Resultante</strong> da matriz abaixo, que cruza o mérito vigente{' '}
                    <strong>antes</strong> dos embargos com o resultado lançado. Casamento por nome: as tabelas de 1G e
                    2G têm IDs diferentes para os valores novos.
                </DocChange>

                <DocTable
                    head={['Status vigente (antes dos embargos)', 'Resultado dos embargos', 'Status Resultante']}
                    rows={MATRIZ_EMBARGOS.map(([vigente, res, status]) => [vigente, res, resultante(status)])}
                />

                <DocCallout tone="warn" icon="alert" title="O mérito de hoje já é o pós-embargo">
                    <p>
                        O LexFlow atualiza {mono('id_sentenca_merito_grau1')} na mesma edição em que lança o resultado
                        do embargo (validado no {mono('processo_audit')}: num caso "Reverteu Improcedência", o mérito
                        foi de Procedente para Improcedente no mesmo instante). Por isso o "antes" vem do histórico: a
                        query {mono('julgados')} traz {mono('ID_SENTENCA_MERITO_1G_PRE_EMBARGOS')} = último valor do
                        mérito no {mono('processo_audit')} antes do lançamento do resultado atual (sem histórico, o
                        mérito atual). Calculado só para os processos com resultado lançado, sem custo perceptível na
                        query. Embargado <strong>sem</strong> resultado lançado cai na fatia "Sem resultado lançado"
                        (ver abaixo). Em 06/10/2026 — NG: 93 com resultado lançado (todas "Status Mantido": 83
                        Prejudicados, 5 Pendência Saneada, 5 Não Conhecidos); LA: nenhuma ainda.
                    </p>
                </DocCallout>

                <DocChange
                    status="06/10/2026"
                    tone="info"
                    area="Ajuste"
                    title='Eixo de data dos embargos e fatia "Sem resultado lançado"'
                    framed
                >
                    A pizza "Resultado dos embargos" e os contadores Embargados/Revertidos passaram a usar como período
                    a <strong>data da sentença de embargos</strong> ({mono('SENTENCA_EMBARGOS')}), não a data da
                    sentença original ({mono('DATA_SENTENCA')}), que costuma ser de meses antes. Exemplo que motivou:
                    setembro/2026 no NG tem 13 sentenças de embargos com resultado lançado (datas 01–18/09, sentenças
                    originais de mar–jun), e o gráfico mostrava 10 processos <em>diferentes</em> (sentenças proferidas
                    em setembro). Embargo com data e sem resultado lançado vira uma fatia própria,{' '}
                    <strong>"Sem resultado lançado"</strong>, sem estimativa (setembro/2026 NG: 182). A estimativa pelo
                    mérito atual descrita no histórico abaixo <strong>não é mais usada</strong> (nem no Acórdão, que
                    recebeu o mesmo ajuste). Sem período selecionado, entram todas as embargadas, inclusive as com
                    resultado e sem data de embargo.
                </DocChange>

                <DocChange status="06/10/2026" tone="ok" area="Novidade" title="Tempo médio sentença → embargos" framed>
                    Abaixo da pizza "Resultado dos embargos": média de dias entre {mono('DATA_SENTENCA')} e a data da
                    sentença de embargos ({mono('SENTENCA_EMBARGOS')}), no mesmo recorte da pizza (embargo com data no
                    período), só com as duas datas e embargo ≥ sentença. Campo{' '}
                    {mono('julgados_sentenca_embargos_tempo_medio_dias_NG/LA')}. Setembro/2026 NG: 182,8 dias (205
                    sentenças, conferido direto no banco).
                </DocChange>

                <DocChange
                    status="15/09 → 06/10/2026"
                    tone="neutral"
                    area="Histórico"
                    title="Estimativa usada antes do resultado oficial"
                >
                    O campo de <em>resultado</em> do embargo ({mono('id_sentenca_embargos_grau1')} →{' '}
                    {mono('sentenca_embargos_primeiro_grau')}, valores como "REVERTEU PROCEDÊNCIA"/"REVERTEU
                    IMPROCEDÊNCIA") ficou 100% vazio até out/2026 — só a data de embargo era preenchida. Como proxy,
                    assumia-se que o campo de mérito é atualizado para refletir o resultado pós-embargo: embargada com
                    mérito atual procedente = "Revertido"; não-procedente = "Mantido" (checado ao vivo contra o banco em
                    15/09/2026 antes de implementar). Desde 06/10/2026 o resultado oficial é lido diretamente (ver
                    acima). A contagem abaixo é dessa estimativa.
                </DocChange>

                <h3 className="doc-h3">Contagem pela estimativa em 15/09/2026 (sem filtro de período)</h3>
                <DocTable
                    head={['Dashboard', 'Embargadas', 'Revertidas', 'Mantidas']}
                    rows={[
                        [unit('NG'), '489', '110', '379'],
                        [unit('LA'), '9', '6', '3'],
                    ]}
                />

                <DocCallout tone="neutral" icon="pieChart" title='Na tela: a pizza "Resultado dos embargos"'>
                    <p>
                        Na tela, o resultado dos embargos aparece na pizza "Resultado dos embargos", na mesma fileira
                        dos cards (Total de Sentenças, Procedentes, Improcedentes, Extintos, Média até a sentença, Valor
                        sentenças procedentes), com as fatias pelo Status Resultante e "Sem resultado lançado", e o
                        tempo médio sentença → embargos no rodapé — clicável, filtra a página igual aos outros gráficos
                        ({mono('resultado_embargos_julgados')}). Os contadores Embargados e Revertidos vêm calculados na
                        resposta do dashboard, mas não aparecem como cards. Liminar ({mono('id_liminar_grau1')}) ficou
                        fora de escopo — 100% vazio no banco e sem coluna de data equivalente à de embargos.
                    </p>
                </DocCallout>
            </DocSection>

            <DocSection
                id="ranking"
                title="06 — Ranking de Juízes"
                subtitle="Exige nome preenchido E mérito classificável"
                badge="2 condições"
            >
                <DocCallout title="Duas condições por linha" icon="users">
                    <p>
                        O ranking exige <strong>duas</strong> condições por linha: nome preenchido (<Code>JUIZ_1G</Code>
                        ) <em>e</em> mérito classificável (todos os 7 valores contam — não há "não classificados" na
                        Sentença).
                    </p>
                </DocCallout>

                <DocCallout
                    tone="warn"
                    icon="alert"
                    title="Fonte do nome é o campo de texto livre do processo, não o cadastro (FK)"
                >
                    <p>
                        <Code>JUIZ_1G</Code> vem de <Code>processo.juiz_1g</Code>, um campo de texto livre. A tabela{' '}
                        <Code>processo</Code> também tem uma FK para o cadastro normalizado (
                        <Code>juiz_primeiro_grau</Code>), mas ela <strong>não é usada</strong> aqui: por decisão de
                        negócio, o texto livre é a fonte oficial para todas as análises de juiz nesses dashboards (ver
                        histórico abaixo).
                    </p>
                </DocCallout>

                <DocTable
                    head={['Dashboard', 'Total (set/2026)', 'Com juiz', '% faltando']}
                    rows={[
                        [unit('LA'), '417', '417', '0,0%'],
                        [unit('NG'), '377', '376', '0,3%'],
                    ]}
                />

                <p>
                    O aviso "Existem X processo(s) sem o nome do juiz!" no topo da página reflete essa mesma lacuna
                    (conta sobre a base inteira do período, não só a classificada). Como a fonte agora é o texto livre —
                    mais preenchido que o cadastro —, a lacuna é bem menor do que era quando o cadastro (FK) era a fonte
                    oficial.
                </p>

                <DocChange
                    status="26/09 → 28/09/2026"
                    tone="neutral"
                    area="Histórico"
                    title="Idas e vindas entre cadastro (FK) e texto livre"
                    framed
                >
                    Em 26/09/2026 foi implementado um fallback pro texto livre ({mono('juiz_1g')}) quando o cadastro
                    (FK) estava vazio, depois <strong>revertido</strong> no mesmo dia a pedido do usuário: a regra
                    passou a ser "só cadastro, nunca texto livre, nem na query base". Em 28/09/2026 o usuário{' '}
                    <strong>reverteu de novo</strong>, no sentido oposto: agora é o texto livre (
                    {mono('processo.juiz_1g')}/{mono('processo.relator_2g')}) a fonte oficial para juiz e relator em
                    todas as análises destes dashboards, e o cadastro (FK, {mono('juiz_primeiro_grau')}/
                    {mono('relator_segundo_grau')}) não é mais usado. A query {mono('julgados')} foi ajustada para
                    selecionar {mono('p.juiz_1g')}/{mono('p.relator_2g')} diretamente, sem os JOINs para as tabelas de
                    cadastro.
                </DocChange>
            </DocSection>

            <DocSection
                id="estudos-extincao"
                title="07 — Estudos de Extinção"
                subtitle="Comarca, valor de causa e juiz por trás das sentenças extintas"
                badge="Estoque × período"
            >
                <DocCallout title="Seção dedicada às sentenças extintas" badge="28/09/2026">
                    <p>
                        Seção dedicada (28/09/2026), abaixo da tabela de sentenças do período, com 3 análises sobre
                        sentenças extintas: por comarca (mapa coroplético com quantidade e valor de causa), por motivo e
                        por juiz. Pode ser recolhida com o botão "Ocultar"/"Mostrar" e é independente do resto da página
                        — tem seu próprio alternador de escopo.
                    </p>
                </DocCallout>

                <DocGrid cols={2}>
                    <DocFeature title="Total (estoque)" tone="violet" icon="layers" badge="Ignora o calendário" framed>
                        <p>
                            Ignora o filtro de data do topo da página e soma <em>toda</em> a base já sentenciada com{' '}
                            {mono('DATA_SENTENCA')} preenchida.
                        </p>
                    </DocFeature>
                    <DocFeature title="Entrada no período" tone="info" icon="calendar" badge="Usa o calendário" framed>
                        <p>Usa o mesmo intervalo de data selecionado no resto da página.</p>
                    </DocFeature>
                </DocGrid>
                <DocCallout tone="warn" icon="alert" title='Alternador "Total (estoque)" / "Entrada no período"'>
                    <p>
                        Cada uma das 3 análises (e os 2 cards de total/valor) tem essas duas versões. As duas vêm
                        prontas na mesma resposta da API — trocar o alternador não dispara uma nova requisição, é só
                        troca de qual array já carregado é exibido.
                    </p>
                </DocCallout>

                <DocTable
                    head={['Análise', 'Campo (entrada)', 'Campo (estoque)']}
                    rows={ESTUDOS.map(([analise, entrada, estoque]) => [analise, mono(entrada), mono(estoque)])}
                />
                <p>
                    O mapa usa o mesmo campo de comarca em dois papéis: {mono('julgados_extincao_por_comarca_NG')} vira
                    tanto a "quantidade" (cor/tamanho do município) quanto a fonte do "valor" (tooltip) — o valor não
                    tem um campo de resposta separado, é o mesmo array com {mono('valor_causa')} lido em vez de{' '}
                    {mono('value')}. O universo de comarcas conhecidas (para diferenciar "zero no filtro" de "fora da
                    base" no mapa) vem de {mono('julgados_comarca_opcoes_NG')}, histórico completo do escritório sem
                    filtro de data.
                </p>

                <DocGrid cols={2}>
                    <DocFeature title="Valor das Extinções" tone="ok" icon="dollar" badge="VALOR_CAUSA_SENTENCA">
                        <p>
                            O card "Valor das Extinções" e o valor mostrado no tooltip do mapa somam{' '}
                            {mono('VALOR_CAUSA_SENTENCA')} ({mono('processo.valor_causa')}) — o valor{' '}
                            <strong>inicial</strong> da causa, o mesmo protocolado no início do processo e sincronizado
                            automaticamente do protocolo, o mesmo campo já usado no card "Valor sentenças procedentes"
                            da seção acima. Não é um valor de condenação ou de extinção em si (não existe esse campo
                            separado no banco).
                        </p>
                    </DocFeature>
                    <DocFeature title="Motivo das extinções" tone="info" icon="list" badge="Mérito 7">
                        <p>
                            No gráfico "Motivo das extinções", quando um processo é marcado como extinto no LexFlow,
                            abre-se um campo livre para o colaborador registrar o motivo — esse texto vem de{' '}
                            {mono('id_motivo_status_grau1')}, que aponta para {mono('motivo_status_grau.description')}{' '}
                            (tabela escopada por escritório e grau). O agrupador pré-filtra a base para só as sentenças
                            extintas (mesmo critério do card "Extintos": mérito {mono('7')}) antes de agrupar por
                            motivo.
                        </p>
                    </DocFeature>
                </DocGrid>

                <p>
                    Clicar num município do mapa ou numa barra dos outros 2 gráficos desta seção filtra a página inteira
                    pelo mesmo mecanismo dos demais gráficos — comarca, motivo da extinção e juiz reaproveitam
                    exatamente os filtros interativos já existentes (ver <a href="#filtros">Filtros interativos</a>),
                    não são filtros novos.
                </p>

                <h3 className="doc-h3">Histórico da seção</h3>
                <DocChange
                    status="28/09/2026"
                    tone="neutral"
                    area="Histórico"
                    title="Gráfico de motivo saiu da seção principal"
                >
                    O gráfico "Motivo das extinções" existia antes na seção "Sentença (1º Grau)" (junto de "por
                    competência" e "por comarca"), sempre restrito ao período selecionado. Ele foi movido para esta
                    seção nova, onde ganhou a opção de ver o estoque completo além do período — a linha da grade
                    principal que tinha 3 colunas (competência/comarca/motivo) passou a ter 2 (competência/comarca).
                </DocChange>
                <DocChange status="29/09/2026" tone="neutral" area="Histórico" title="Comarca virou mapa coroplético">
                    Inicialmente "Extinções por comarca" e "Valor das extinções por comarca" eram 2 gráficos de barra
                    separados. Substituídos por um único mapa (<Code>ComarcaMapaMultiUfChart</Code> no NG,{' '}
                    <Code>ComarcaMapaChart</Code> no LA — o mesmo componente já usado no dashboard de Execução), que
                    mostra as duas informações juntas: cor/tamanho do município pela quantidade (raiz quadrada) e o
                    valor de causa no tooltip ao passar o mouse. NG usa a variante multi-UF (7 estados hoje: AC, AM, BA,
                    MA, PA, PB, RJ — cada comarca é casada com o estado certo por um voto de maioria de {mono('UF')} na
                    base completa do escritório); LA usa a variante de estado único (Amazonas, escritório é só AM).
                </DocChange>
                <DocChange
                    status="29/09/2026"
                    tone="neutral"
                    area="Histórico"
                    title="Legenda ganhou comparativo Capital × Interior"
                >
                    A legenda do mapa (abaixo do mapa em si) ganhou uma linha "Capital × Interior": soma da quantidade
                    de extinções na comarca capital de cada UF exibida vs. todas as outras comarcas (Interior), em
                    quantidade e percentual — calculado no frontend a partir dos mesmos dados já carregados pelo mapa
                    (nenhum campo novo de API). Capitais configuradas hoje: AM → Manaus, PA → Belém, PB → João Pessoa,
                    AC → Rio Branco, BA → Salvador, MA → São Luís, RJ → Rio de Janeiro (NG); LA usa só Manaus (única
                    capital possível, escritório é Amazonas). "Sem comarca" fica fora dos dois lados do comparativo.
                </DocChange>
                <DocChange
                    status="29/09/2026"
                    tone="neutral"
                    area="Histórico"
                    title="Legenda ganhou % de extinções revertidas em 2G, e virou 3 colunas"
                >
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
                </DocChange>
                <DocChange
                    status="29/09/2026"
                    tone="neutral"
                    area="Histórico"
                    title="Tempo médio por comarca no tooltip do mapa"
                >
                    O tooltip do mapa (ao passar o mouse num município) já existia no componente compartilhado com a
                    Execução e sabia mostrar "Tempo médio", mas o backend de Julgados Sentença nunca preenchia esse
                    campo — aparecia sempre vazio. Adicionado {mono('tempo_medio_dias')} em cada item de{' '}
                    {mono('julgados_extincao_por_comarca_NG')}/{mono('julgados_extincao_por_comarca_estoque_NG')} (e
                    equivalentes LA): média de dias entre {mono('DATA_AJUIZAMENTO')} e {mono('DATA_SENTENCA')} da
                    comarca, calculada sobre o histórico completo do escritório (todas as sentenças da comarca com as
                    duas datas preenchidas, sem filtro de categoria ou de período) — mesmo padrão de{' '}
                    {mono('group_execucao_por_comarca')}: é fixo por comarca e não muda com o alternador
                    estoque/entrada, serve de referência estável de "quanto tempo uma sentença dessa comarca costuma
                    levar". <Code>null</Code> quando a comarca não tem nenhuma sentença com as duas datas preenchidas.
                </DocChange>
                <DocChange
                    status="29/09/2026"
                    tone="warn"
                    area="Correção"
                    title="Corrigida a fonte do valor de causa"
                    framed
                >
                    Até essa data, {mono('VALOR_CAUSA_SENTENCA')} vinha de {mono('processo.valor_causa_vs')} — um campo{' '}
                    <strong>separado</strong> do valor de causa inicial, majoritariamente vazio (só 16.181 de ~100 mil
                    processos preenchidos) e, quando preenchido, divergente do valor inicial em{' '}
                    <strong>~93% dos casos</strong> (validado ao vivo no banco: muitas vezes {mono('0')} enquanto{' '}
                    {mono('processo.valor_causa')} tinha o valor real protocolado). Corrigido para usar{' '}
                    {mono('processo.valor_causa')} diretamente na query {mono('julgados')} — mesma correção aplicada em
                    Acórdãos ({mono('VALOR_CAUSA_ACORDO')}). O valor total de extinções (estoque) do NG saltou de{' '}
                    <Hl tone="danger" mono>
                        ~R$ 294 mil
                    </Hl>{' '}
                    para{' '}
                    <Hl tone="ok" mono>
                        ~R$ 56 milhões
                    </Hl>{' '}
                    após a correção — o número antigo estava drasticamente subcontado, não é uma mudança de critério.
                </DocChange>
            </DocSection>

            <DocSection
                id="estudo-improcedencias"
                title="08 — Estudo das Improcedências"
                subtitle="Comarca, valor de causa, motivo e juiz por trás das sentenças improcedentes"
                badge="Estoque × período"
            >
                <DocCallout title="Mesmo desenho dos Estudos de Extinção, para as improcedentes">
                    <p>
                        Seção 03 do dashboard, montada como os <a href="#estudos-extincao">Estudos de Extinção</a>, com
                        as sentenças improcedentes: total e valor de causa inicial, mapa por comarca (Capital ×
                        Interior), motivo informado no 1º grau, "Juízes que mais julgam improcedente" e o mesmo
                        alternador Total (estoque) / Entrada no período, independente do resto da página.
                    </p>
                </DocCallout>
                <DocFeature title="Revertidas em 2G" tone="ok" icon="refresh" badge="Acórdão procedente" framed>
                    <p>
                        A 3ª coluna da legenda do mapa mostra as improcedentes cujo acórdão do mesmo processo foi{' '}
                        <strong>procedente ou parcialmente procedente</strong> (com ou sem proveito econômico) — "vira
                        procedente no 2ºG". Sentença anulada não conta. Como nos Estudos de Extinção, o denominador
                        inclui as improcedentes que ainda não têm acórdão.
                    </p>
                </DocFeature>
                <p>
                    Clicar num município, num motivo ou num juiz filtra a página inteira pelos mesmos filtros
                    interativos de sempre (ver <a href="#filtros">Filtros interativos</a>).
                </p>
            </DocSection>

            <DocSection
                id="exportacao"
                title="09 — Exportação de relatório"
                subtitle="Botão 'Exportar' do dashboard (para quem tem permissão de exportar)"
                badge="CSV · XLSX"
            >
                <DocCallout title="Diálogo de um passo só" icon="file-down">
                    <p>
                        Diálogo de um passo só — escolha de campos — que gera CSV ou XLSX no servidor, usando exatamente
                        o mesmo pipeline de filtro e período já aplicado na tela. Nenhum filtro é reconfigurado dentro
                        do diálogo.
                    </p>
                </DocCallout>
                <p>
                    Endpoint: <Code>{'GET /orgs/{org}/units/{unidade}/dashboards/julgados-sentencas/export'}</Code>{' '}
                    (parâmetros <Code>from</Code>, <Code>to</Code>, <Code>format</Code>, <Code>campos</Code> e os
                    filtros da página). Na v1 eram rotas por escritório (
                    <Code>/api/dashboard/julgados_NG|LA/export</Code>), com os mesmos campos.
                </p>
                <p>
                    Campos exportáveis vêm da query <Code>julgados</Code> (número do processo, matéria, competência,
                    comarca, UF, fase, subfase, juiz (1G), sentença de mérito, valor da sentença, motivo da extinção,
                    data de distribuição, data da sentença, data e status da sentença de embargos), mais{' '}
                    <strong>uma coluna calculada</strong>: "Status Resultante dos Embargos" — ver abaixo.
                </p>

                <DocChange status="15/09/2026" tone="ok" area="Novidade" title="Campos de embargos no relatório" framed>
                    Adicionados os campos "Data da Sentença de Embargos" (grupo "Datas") e "Status da Sentença de
                    Embargos" (grupo "Julgamento (1º Grau)") ao diálogo de exportação, espelhando{' '}
                    {mono('SENTENCA_EMBARGOS')} (data) e {mono('STATUS_SENTENCA_EMBARGOS')} (status, via novo JOIN com{' '}
                    {mono('sentenca_embargos_primeiro_grau')}) — mesmos campos usados pelos cards de{' '}
                    <a href="#embargos">Embargos e reversão</a>.
                </DocChange>

                <DocCallout tone="warn" icon="alert" title="Coluna de status: preenchimento parcial">
                    <p>
                        Em 15/09/2026 o campo oficial de resultado do embargo estava 100% vazio no banco, e a coluna
                        "Status da Sentença de Embargos" saía em branco em <strong>todas</strong> as linhas — ela foi
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
                    Para quem baixa o relatório saber o desfecho do embargo, o campo{' '}
                    <strong>"Status Resultante dos Embargos"</strong> (slug {mono('resultado_embargos_estimado')}, grupo
                    "Julgamento (1º Grau)") traz o mesmo Status Resultante da pizza "Resultado dos embargos": a matriz
                    oficial (mérito antes dos embargos × resultado lançado) quando há resultado, "Sem resultado lançado"
                    quando só há a data de embargo, e vazio para as sentenças não embargadas. Calculado no momento da
                    exportação ({mono('_anotar_resultado_embargos_export')}, em{' '}
                    {mono('app/analyses/v1_julgados_export.py')}), reusando o mesmo getter do dashboard — não é uma
                    coluna nova no banco. Na primeira versão (16/09/2026) a coluna se chamava "Resultado do Embargo
                    (estimado)" e trazia "Revertido"/"Mantido" pela estimativa do mérito atual.
                </DocChange>

                <DocChange status="26/08/2026" tone="warn" area="Correção" title="Export sem recorte de escritório">
                    Na primeira versão, o export aplicava os filtros de matéria/juiz/etc. mas esquecia o recorte de
                    escritório (<Code>_base_julgados_NG</Code>/<Code>_base_julgados_LA</Code>), que na tela só é
                    aplicado dentro das funções de KPI/gráfico. Resultado: exportar do NG trazia junto sentenças da LA
                    (e vice-versa) que batessem com o mesmo filtro. Corrigido aplicando o mesmo recorte de escritório
                    antes do filtro categórico, igual ao dashboard.
                </DocChange>

                <DocChange
                    status="21/10/2026"
                    tone="ok"
                    area="Novidade"
                    title='Coluna "Valor da Sentença" e aviso de valor faltando'
                    framed
                >
                    O relatório ganhou a coluna "Valor da Sentença" (slug {mono('valor_sentenca')},{' '}
                    {mono('VALOR_SENTENCA')} = {mono('processo.valor_causa_vs')}), o valor fixado na sentença —
                    diferente do valor de causa inicial. A coluna não tem descrição no banco; o significado foi
                    confirmado pelos dados (valor &gt; 0 em 2.600 de 2.867 Procedentes com PE e quase zero em
                    improcedentes/extintos). Sai como moeda: número com formato R$ no XLSX (somável) e texto "R$
                    1.234,56" no CSV. A barra de aviso no topo também passou a contar sentenças procedentes com proveito
                    econômico (mérito 1 ou 3) sem o valor da sentença (vazio ou zero), e esses processos entram na lista
                    clicável com o campo "Valor da sentença".
                </DocChange>
            </DocSection>

            <DocSection
                id="notas"
                title="10 — Notas e pendências conhecidas"
                subtitle="Detalhes técnicos que ajudam a diagnosticar divergências futuras"
                tone="neutral"
            >
                <DocGrid cols={2}>
                    <DocFeature title="Ranking nunca soma ao total do card" tone="info" icon="info" badge="Esperado">
                        <p>
                            É esperado, não bug: Total conta tudo no período; o ranking exclui adicionalmente quem não
                            tem juiz — por isso soma menos que o total.
                        </p>
                    </DocFeature>
                    <DocFeature
                        title="Comparação de casing nos filtros"
                        tone="neutral"
                        icon="filter"
                        badge="casefold()"
                    >
                        <p>
                            Matéria/comarca/competência/motivo comparam por <Code>casefold()</Code> (case insensitive);
                            UF é normalizada para maiúsculas antes de comparar. Um valor com espaço a mais ou acento
                            diferente no banco não é normalizado e vira uma opção separada no filtro.
                        </p>
                    </DocFeature>
                    <DocFeature
                        title='Embargo sem resultado é "Sem resultado lançado"'
                        tone="warn"
                        icon="alert"
                        badge="Sem estimativa"
                        badgeMono={false}
                    >
                        <p>
                            Ver <a href="#embargos">Embargos e reversão</a> — o resultado oficial (
                            {mono('id_sentenca_embargos_grau1')}) é lido desde 06/10/2026, mas ainda está preenchido só
                            em parte da base. Embargo com data e sem resultado lançado não é estimado: entra como "Sem
                            resultado lançado" na pizza, no filtro e no relatório.
                        </p>
                    </DocFeature>
                    <DocFeature
                        title="Juiz vem do texto livre do processo, não do cadastro (FK)"
                        tone="info"
                        icon="users"
                        badge="juiz_1g"
                    >
                        <p>
                            Ver <a href="#ranking">Ranking de Juízes</a> — {mono('processo.juiz_1g')} (texto livre) é a
                            fonte oficial por decisão de negócio; o cadastro normalizado ({mono('juiz_primeiro_grau')})
                            não é usado em nenhuma análise. Não confundir com o campo de export "Status da Sentença de
                            Embargos", que é outra coisa.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>
        </DocPage>
    )
}
