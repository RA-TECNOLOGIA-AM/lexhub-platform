import { useState, type KeyboardEvent, type MouseEvent, type ReactNode } from 'react'
import { BarList } from '../../../components/charts/BarList.tsx'
import { ChartCard, ChartEmpty } from '../../../components/charts/ChartCard.tsx'
import { ComarcaMapa } from '../../../components/charts/ComarcaMapa.tsx'
import { LineChart, type LineSeries } from '../../../components/charts/LineChart.tsx'
import { PieChart } from '../../../components/charts/PieChart.tsx'
import { DashSection } from '../../../components/dashboard/DashSection.tsx'
import { DeltaPill, HeroStat, InfoTip } from '../../../components/dashboard/StatCard.tsx'
import { CountUp } from '../../../components/ui/CountUp.tsx'
import { Segmented } from '../../../components/ui/Segmented.tsx'
import { topN } from '../../../lib/charts.ts'
import { fmt } from '../../../lib/format.ts'
import { DadosFaltando } from '../julgados-acordaos/DadosFaltando.tsx'
import {
    CATEGORIAS,
    MESES_NOME_COMPLETO,
    STATUS_EMBARGOS,
    acordaosPorAno,
    composicao,
    coresDosAnos,
    mapaDaUnidade,
    taxaDoAno,
    type AnoAcordaos,
    type Categoria,
} from '../julgados-acordaos/julgados.ts'
import { LegendaCategorias, RelatoresRanking } from '../julgados-acordaos/RelatoresRanking.tsx'
import { TaxaProcedencia } from '../julgados-acordaos/TaxaProcedencia.tsx'
import type { ContentProps } from '../types.ts'
import { lerJulgadosSentencas, type Escopo, type Estudo } from './fields.ts'
import { valorDoFiltro, type SentencasFilterKey } from './filters.ts'
import { avisosSentencas } from './sentencas.ts'
import { SentencasLista } from './SentencasLista.tsx'
import type { JulgadosSentencasResponse, PontoJulgados } from './types.ts'
// As grades e as peças da página são as mesmas do Julgados Acórdãos.
import '../julgados-acordaos/julgados.css'

// Os textos (rótulos, explicações do "i" e legendas) são os da página da v1, palavra por palavra.
const VS = 'vs período anterior'

// O ano do calendário (o dos gráficos por ano que fica laranja e contínuo), lido quando a página carrega.
const ANO_ATUAL = new Date().getFullYear()

// Número que pode faltar na resposta ('—'), com a contagem animada quando vem.
const valor = (v: number | null, format: (n: number) => string) =>
    v === null ? '—' : <CountUp value={v} format={format} />

// Dias como na v1 ('12 dias'; sem o número, '–').
const dias = (v: number | null) => (v === null ? '–' : `${fmt.int(Math.round(v))} dias`)

// Do maior para o menor (a página da v1 ordenava assim antes de desenhar).
const ordenados = (itens: PontoJulgados[]) => topN(itens, itens.length)

// A cor de cada fatia na ordem dada (a mesma paleta da pizza da casa).
const comCor = (itens: PontoJulgados[]) => itens.map((p, i) => ({ ...p, color: `var(--pie-${(i % 10) + 1})` }))

// Matérias com fatia e rótulo próprios na pizza; as demais somam em "Outras" (com 30+ matérias os rótulos não cabem).
const MATERIAS_NA_PIZZA = 8

// "Sem data de ajuizamento" é o nome que a API manda (e o valor do filtro); na pizza aparece curto, para o
// rótulo caber em volta da rosca como nas outras pizzas.
const SEM_ANO = 'Sem data de ajuizamento'
const SEM_ANO_CURTO = 'Sem data'
const anoNaTela = (name: string) => (name.toUpperCase() === SEM_ANO.toUpperCase() ? SEM_ANO_CURTO : name)
const anoDoFiltro = (name: string) => (name === SEM_ANO_CURTO ? SEM_ANO : name)

const TAXA_TITULO: Record<Categoria, string> = {
    procedente: 'Taxa de procedência mês a mês',
    improcedente: 'Taxa de improcedência mês a mês',
    extinto: 'Taxa de extinção mês a mês',
}

// Seletor de categoria dos gráficos por ano (Procedentes / Improcedentes / Extintos).
function SeletorCategoria({
    label,
    value,
    onChange,
}: {
    label: string
    value: Categoria
    onChange: (c: Categoria) => void
}) {
    return (
        <label className="field-select">
            <span className="sr-only">{label}</span>
            <select value={value} onChange={(e) => onChange(e.target.value as Categoria)}>
                {CATEGORIAS.map((c) => (
                    <option key={c.value} value={c.value}>
                        {c.label}
                    </option>
                ))}
            </select>
        </label>
    )
}

// O "i" com a explicação ao lado de outra ação do cabeçalho do cartão (como o headerAction + info da v1).
function Acoes({ info, children }: { info?: string; children?: ReactNode }) {
    return (
        <span className="jl-acoes">
            {children}
            {info && <InfoTip text={info} />}
        </span>
    )
}

// Card que liga o filtro ao clicar em qualquer parte dele, como o StatCard da v1 (onCardClick). O "i" só explica.
function CardClicavel({ ativo, onClick, children }: { ativo: boolean; onClick?: () => void; children: ReactNode }) {
    if (!onClick) return <>{children}</>
    const clicar = (e: MouseEvent<HTMLDivElement>) => {
        if ((e.target as HTMLElement).closest('.tip')) return
        onClick()
    }
    const tecla = (e: KeyboardEvent<HTMLDivElement>) => {
        if (e.target !== e.currentTarget || (e.key !== 'Enter' && e.key !== ' ')) return
        e.preventDefault()
        onClick()
    }
    return (
        <div
            className={ativo ? 'jl-click on' : 'jl-click'}
            role="button"
            tabIndex={0}
            aria-pressed={ativo}
            title="Clique para filtrar a página"
            onClick={clicar}
            onKeyDown={tecla}
        >
            {children}
        </div>
    )
}

// Seletor do escopo dos estudos (Extinção e Improcedências): toda a base ou só a entrada no período.
function SeletorEscopo({ label, value, onChange }: { label: string; value: Escopo; onChange: (e: Escopo) => void }) {
    return (
        <Segmented
            label={label}
            options={[
                { value: 'estoque', label: 'Total (estoque)' },
                { value: 'entrada', label: 'Entrada no período' },
            ]}
            value={value}
            onChange={onChange}
        />
    )
}

// O Julgados Sentenças (LexFlow: NG, LA e RJ), com as seções, os cards e os gráficos da página da v1
// (julgados_sentenca_{NG,LA,RJ}.tsx), na mesma ordem, no layout do Julgados Acórdãos da V2. Carregar, erros,
// cabeçalho (Exportar, Atualizar, documentação), período e a janela Filtros ficam no DashboardView. Clicar num card
// de categoria, numa fatia, num juiz ou numa barra liga ou desliga o filtro correspondente
// (toggleJulgadosSentencaFilterValue da v1). Os nomes dos campos mudam por unidade: quem escolhe é fields.ts.
export function JulgadosSentencasContent({
    data,
    filters = {},
    onToggleFilter,
}: ContentProps<JulgadosSentencasResponse>) {
    const [anoEscolhido, setAnoEscolhido] = useState<number | null>(null)
    const [categoriaAnual, setCategoriaAnual] = useState<Categoria>('procedente')
    const [categoriaTaxa, setCategoriaTaxa] = useState<Categoria>('procedente')
    const [escopoExtincao, setEscopoExtincao] = useState<Escopo>('estoque')
    const [escopoImprocedencia, setEscopoImprocedencia] = useState<Escopo>('estoque')

    const j = lerJulgadosSentencas(data)
    if (j.unit === null) {
        return <ChartEmpty>Julgados Sentenças só existe para as unidades NG, LA e RJ.</ChartEmpty>
    }
    const { n, comparativo: c } = j

    // Clique num gráfico: o valor limpo (UF em maiúsculas), sem filtro vazio.
    const filtrar = (key: SentencasFilterKey) =>
        onToggleFilter &&
        ((name: string) => {
            const v = valorDoFiltro(key, name)
            if (v) onToggleFilter(key, v)
        })
    const categorias = filters.categoria_julgados ?? []
    const porCategoria = filtrar('categoria_julgados')
    const cardCategoria = (categoria: Categoria, card: ReactNode) => (
        <CardClicavel ativo={categorias.includes(categoria)} onClick={porCategoria && (() => porCategoria(categoria))}>
            {card}
        </CardClicavel>
    )

    const comp = composicao(n)
    // Só as fatias com embargo, na ordem da API (como na v1).
    const embargos = STATUS_EMBARGOS.map((s) => ({
        name: s.name,
        value: j.embargosResultado.find((p) => p.name.toLowerCase() === s.name.toLowerCase())?.value ?? 0,
        color: s.color,
    })).filter((e) => e.value > 0)
    const totalEmbargos = embargos.reduce((s, e) => s + e.value, 0)

    // Histórico (os anos desde 2024): o ano do "mês a mês" é o escolhido ou o mais recente.
    const anos = acordaosPorAno(j.porMes)
    const ano = anos.find((a) => a.ano === anoEscolhido) ?? anos[anos.length - 1]
    const cores = coresDosAnos(
        anos.map((a) => a.ano),
        ANO_ATUAL,
    )
    const porAno = (valores: (a: AnoAcordaos) => (number | null)[]): LineSeries[] =>
        anos.map((a, i) => ({ label: String(a.ano), ...cores[i], values: valores(a) }))
    const tooltipMes = { heading: 'Mês', title: (i: number) => MESES_NOME_COMPLETO[i] }

    const mapa = mapaDaUnidade(j.unit)
    const totalMateria = j.porMateria.reduce((s, p) => s + p.value, 0)
    const materias = comCor(ordenados(j.porMateria))
    const anosAjuizamento = comCor(j.porAnoAjuizamento.map((p) => ({ ...p, name: anoNaTela(p.name) })))
    const porAnoAjuizamento = filtrar('ano_ajuizamento_julgados')
    const totalAjuizamento = anosAjuizamento.reduce((s, p) => s + p.value, 0)

    // Estudos de Extinção e das Improcedências: estoque (base inteira já sentenciada) ou entrada (só o período).
    const extEstoque = escopoExtincao === 'estoque'
    const impEstoque = escopoImprocedencia === 'estoque'

    return (
        <div className="dsecs jl">
            <DadosFaltando
                avisos={avisosSentencas(n)}
                itens={j.dadosFaltando}
                base="sentenças"
                relatorio="campos-faltando"
                filters={filters}
            />

            <DashSection
                index={1}
                eyebrow="Visão geral"
                title="Sentença (1º Grau)"
                subtitle="Processos com sentença proferida no período selecionado."
            >
                <div className="stack">
                    {/* Os seis cards (3 × 2) à esquerda e a pizza dos embargos à direita, na altura das duas linhas. */}
                    <div className="grid jl-topo">
                        <div className="grid grid-stat-3 jl-cards">
                            <HeroStat
                                label="Total de Sentenças"
                                icon="scale"
                                tone="accent"
                                value={valor(n.total, fmt.int)}
                                below={<DeltaPill value={c.total} suffix={VS} plain />}
                                hint="Processos com sentença no período, comparados ao período anterior de mesma duração"
                            />
                            {cardCategoria(
                                'procedente',
                                <HeroStat
                                    label="Procedentes"
                                    icon="check-circle"
                                    tone="ok"
                                    outline={categorias.includes('procedente')}
                                    value={valor(n.procedentes, fmt.int)}
                                    below={<DeltaPill value={c.procedentes} suffix={VS} plain />}
                                    hint="Status 1G procedente (total ou parcial, com ou sem proveito econômico), comparados ao período anterior de mesma duração. Clique para filtrar a página."
                                />,
                            )}
                            {cardCategoria(
                                'improcedente',
                                <HeroStat
                                    label="Improcedentes"
                                    icon="x-circle"
                                    tone="danger"
                                    outline={categorias.includes('improcedente')}
                                    value={valor(n.improcedentes, fmt.int)}
                                    below={<DeltaPill value={c.improcedentes} betterWhenDown suffix={VS} plain />}
                                    hint="Status 1G improcedente, comparados ao período anterior de mesma duração. Clique para filtrar a página."
                                />,
                            )}
                            {cardCategoria(
                                'extinto',
                                <HeroStat
                                    label="Extintos"
                                    icon="ban"
                                    tone="warn"
                                    outline={categorias.includes('extinto')}
                                    value={valor(n.extintos, fmt.int)}
                                    below={<DeltaPill value={c.extintos} suffix={VS} plain />}
                                    hint="Status 1G extinto sem mérito, comparados ao período anterior de mesma duração. Clique para filtrar a página."
                                />,
                            )}
                            <HeroStat
                                label="Média até a sentença"
                                icon="clock"
                                tone="info"
                                value={dias(n.tempoMedio)}
                                below={<DeltaPill value={c.tempoMedio} betterWhenDown suffix={VS} plain />}
                                hint="Média de dias entre a distribuição (ajuizamento) e a sentença, para as sentenças do período, comparada ao período anterior de mesma duração."
                            />
                            <HeroStat
                                label="Valor sentenças procedentes"
                                icon="dollar"
                                tone="ok"
                                value={valor(n.valorProcedentes, fmt.brl)}
                                below={<DeltaPill value={c.valorProcedentes} suffix={VS} plain />}
                                hint="Soma do valor de causa (VALOR_CAUSA_SENTENCA) das sentenças procedentes no período, comparada ao período anterior de mesma duração."
                            />
                        </div>

                        {/* Mesmo desenho da Distribuição por rubrica do Comercial (LexPre), como no Julgados Acórdãos. */}
                        <ChartCard
                            className="jl-pie-centro"
                            title="Resultado dos embargos"
                            subtitle={`${fmt.int(totalEmbargos)} sentença(s) de embargos no período · clique na fatia para filtrar`}
                            action={
                                <Acoes info="Sentenças de embargos com data no período (eixo: data da sentença de embargos, não da sentença original), pelo Status Resultante da matriz (mérito antes dos embargos × resultado lançado). Com data e sem resultado lançado: “Sem resultado lançado”. Clique para filtrar." />
                            }
                            footer={
                                <>
                                    Tempo médio entre a sentença e a sentença de embargos:{' '}
                                    <strong className="num">{dias(n.embargosTempoMedio)}</strong>
                                </>
                            }
                        >
                            {embargos.length > 0 ? (
                                <PieChart
                                    items={embargos}
                                    size={220}
                                    centerLabel="embargos"
                                    labels
                                    labelsTwoLines
                                    legendWhenNarrow
                                    sort={false}
                                    selected={filters.resultado_embargos_julgados}
                                    onSelect={filtrar('resultado_embargos_julgados')}
                                    selectLabel="Filtrar pelo resultado dos embargos"
                                />
                            ) : (
                                <ChartEmpty>Sem dados para o período selecionado.</ChartEmpty>
                            )}
                        </ChartCard>
                    </div>

                    <TaxaProcedencia
                        c={comp}
                        grau="1G"
                        plural="sentenças"
                        singular="sentença"
                        naoClassificados="não classificada(s)"
                    />

                    <div className="grid jl-tres">
                        <ChartCard
                            title="Ranking de Juízes"
                            subtitle="Sentenças (1G) no período · clique para filtrar"
                            action={<LegendaCategorias />}
                        >
                            <div className="jl-scroll">
                                <RelatoresRanking
                                    rows={j.ranking}
                                    selected={filters.juiz_julgados}
                                    onSelect={filtrar('juiz_julgados')}
                                />
                            </div>
                        </ChartCard>
                        <ChartCard
                            className="jl-pie-centro"
                            title="Sentenças por matéria"
                            subtitle={`${fmt.int(totalMateria)} sentença(s) no período · clique na fatia para filtrar`}
                        >
                            {materias.length > 0 ? (
                                <PieChart
                                    items={materias}
                                    max={MATERIAS_NA_PIZZA}
                                    labelMaxChars={14}
                                    centerLabel="sentenças"
                                    labels
                                    labelsTwoLines
                                    legendWhenNarrow
                                    selected={filters.materia_julgados}
                                    onSelect={filtrar('materia_julgados')}
                                    selectLabel="Filtrar pela matéria"
                                />
                            ) : (
                                <ChartEmpty>Sem dados para o período selecionado.</ChartEmpty>
                            )}
                        </ChartCard>
                        <ChartCard
                            className="jl-pie-centro"
                            title="Ano de Ajuizamento — Total em Sentenças"
                            subtitle={`${fmt.int(totalAjuizamento)} sentença(s) no período · clique na fatia para filtrar`}
                        >
                            {anosAjuizamento.length > 0 ? (
                                <PieChart
                                    items={anosAjuizamento}
                                    centerLabel="sentenças"
                                    sort={false}
                                    labels
                                    labelsTwoLines
                                    legendWhenNarrow
                                    selected={filters.ano_ajuizamento_julgados?.map(anoNaTela)}
                                    onSelect={porAnoAjuizamento && ((name) => porAnoAjuizamento(anoDoFiltro(name)))}
                                    selectLabel="Filtrar pelo ano de ajuizamento"
                                />
                            ) : (
                                <ChartEmpty>Sem dados para o período selecionado.</ChartEmpty>
                            )}
                        </ChartCard>
                    </div>

                    <div className="grid jl-dois">
                        <ChartCard
                            title="Sentenças por competência"
                            action={
                                <Acoes info="Sentenças no período, agrupadas por competência. Clique para filtrar." />
                            }
                        >
                            <div className="jl-scroll">
                                <BarList
                                    items={ordenados(j.porCompetencia)}
                                    showShare
                                    wrapNames
                                    selected={filters.competencia_julgados}
                                    onSelect={filtrar('competencia_julgados')}
                                    selectLabel="Filtrar pela competência"
                                />
                            </div>
                        </ChartCard>
                        <ChartCard
                            title="Sentenças por comarca"
                            action={<Acoes info="Sentenças no período, agrupadas por comarca. Clique para filtrar." />}
                        >
                            <div className="jl-scroll">
                                <BarList
                                    items={ordenados(j.porComarca)}
                                    showShare
                                    wrapNames
                                    selected={filters.comarca_julgados}
                                    onSelect={filtrar('comarca_julgados')}
                                    selectLabel="Filtrar pela comarca"
                                />
                            </div>
                        </ChartCard>
                    </div>

                    <ChartCard
                        title="Sentenças mês a mês"
                        action={
                            ano && (
                                <label className="field-select">
                                    <span className="sr-only">Ano</span>
                                    <select value={ano.ano} onChange={(e) => setAnoEscolhido(Number(e.target.value))}>
                                        {anos.map((a) => (
                                            <option key={a.ano} value={a.ano}>
                                                {a.ano}
                                            </option>
                                        ))}
                                    </select>
                                </label>
                            )
                        }
                    >
                        <LineChart
                            height={320}
                            legend
                            labels={MESES_NOME_COMPLETO}
                            tooltip={tooltipMes}
                            series={
                                ano
                                    ? CATEGORIAS.map((k) => ({ label: k.label, color: k.color, values: ano[k.value] }))
                                    : []
                            }
                        />
                    </ChartCard>

                    <div className="grid jl-dois">
                        <ChartCard
                            title="Sentenças por ano"
                            action={
                                <SeletorCategoria
                                    label="Categoria do gráfico Sentenças por ano"
                                    value={categoriaAnual}
                                    onChange={setCategoriaAnual}
                                />
                            }
                        >
                            <LineChart
                                height={320}
                                legend
                                labels={MESES_NOME_COMPLETO}
                                tooltip={tooltipMes}
                                series={porAno((a) => a[categoriaAnual])}
                            />
                        </ChartCard>
                        <ChartCard
                            title={TAXA_TITULO[categoriaTaxa]}
                            action={
                                <Acoes info="Por mês e ano: sentenças da categoria escolhida ÷ (procedentes + improcedentes + extintos), mesma base do card Taxa de procedência. Meses sem sentença decidida ficam sem ponto.">
                                    <SeletorCategoria
                                        label="Categoria da taxa mês a mês"
                                        value={categoriaTaxa}
                                        onChange={setCategoriaTaxa}
                                    />
                                </Acoes>
                            }
                        >
                            <LineChart
                                height={320}
                                legend
                                labels={MESES_NOME_COMPLETO}
                                format={fmt.pct}
                                tooltip={tooltipMes}
                                series={porAno((a) => taxaDoAno(a, categoriaTaxa))}
                            />
                        </ChartCard>
                    </div>

                    <SentencasLista itens={j.lista} />
                </div>
            </DashSection>

            <DashSection
                index={2}
                eyebrow="Extinção"
                title="Estudos de Extinção"
                subtitle="Comarca, valor de causa e juízes por trás das sentenças extintas — total já sentenciado na base ou só o que entrou no período selecionado no topo da página."
                action={
                    <SeletorEscopo
                        label="Escopo dos Estudos de Extinção"
                        value={escopoExtincao}
                        onChange={setEscopoExtincao}
                    />
                }
            >
                <EstudoSentencas
                    estudo={j.extincao[escopoExtincao]}
                    total={extEstoque ? n.extincaoTotalEstoque : n.extintos}
                    valorCausa={extEstoque ? n.extincaoValorEstoque : n.extincaoValor}
                    totalNoEscopo={extEstoque ? n.totalEstoque : n.total}
                    revertidos={extEstoque ? n.extincaoRevertidaEstoque : n.extincaoRevertida}
                    mapa={mapa}
                    comarcas={j.comarcaOpcoes}
                    filters={filters}
                    filtrar={filtrar}
                    textos={{
                        totalTitulo: 'Total de Extinções',
                        totalIcone: 'ban',
                        totalTom: 'warn',
                        totalHint: extEstoque
                            ? 'Sentenças extintas em toda a base já sentenciada (estoque).'
                            : 'Sentenças extintas no período selecionado.',
                        valorTitulo: 'Valor de causa Inicial das Extinções',
                        valorHint: 'Soma do valor de causa das sentenças extintas no período selecionado.',
                        mapaTitulo: 'Extinções por comarca',
                        mapaInfo:
                            'Quantidade e valor de causa (inicial) das sentenças extintas por comarca, no escopo selecionado. Clique para filtrar.',
                        mapaInfoDetalhada:
                            'Cor e tamanho do município pela quantidade de sentenças extintas (raiz quadrada); passe o mouse para ver quantidade e valor. Clique num município para filtrar a página pela comarca correspondente.',
                        motivoTitulo: 'Motivo das extinções',
                        motivoInfo:
                            'Sentenças extintas, agrupadas pelo motivo informado, no escopo selecionado. Clique para filtrar.',
                        juizTitulo: 'Juízes que mais extinguem',
                        juizInfo: 'Sentenças extintas por juiz (1G), no escopo selecionado. Clique para filtrar.',
                    }}
                />
            </DashSection>

            <DashSection
                index={3}
                eyebrow="Improcedência"
                title="Estudo das Improcedências"
                subtitle="Comarca, valor de causa, motivo e juízes por trás das sentenças improcedentes — total já sentenciado na base ou só o que entrou no período selecionado no topo da página."
                action={
                    <SeletorEscopo
                        label="Escopo do Estudo das Improcedências"
                        value={escopoImprocedencia}
                        onChange={setEscopoImprocedencia}
                    />
                }
            >
                <EstudoSentencas
                    estudo={j.improcedencia[escopoImprocedencia]}
                    total={impEstoque ? n.improcedenciaTotalEstoque : n.improcedentes}
                    valorCausa={impEstoque ? n.improcedenciaValorEstoque : n.improcedenciaValor}
                    totalNoEscopo={impEstoque ? n.totalEstoque : n.total}
                    revertidos={impEstoque ? n.improcedenciaRevertidaEstoque : n.improcedenciaRevertida}
                    mapa={mapa}
                    comarcas={j.comarcaOpcoes}
                    filters={filters}
                    filtrar={filtrar}
                    textosMapa={{
                        categoriaPlural: 'improcedentes',
                        revertidosDescricao: 'com acórdão procedente ou parcialmente procedente',
                        revertidosFrase: 'vira procedente no 2ºG.',
                    }}
                    textos={{
                        totalTitulo: 'Total de Improcedências',
                        totalIcone: 'x-circle',
                        totalTom: 'danger',
                        totalHint: impEstoque
                            ? 'Sentenças improcedentes em toda a base já sentenciada (estoque).'
                            : 'Sentenças improcedentes no período selecionado.',
                        valorTitulo: 'Valor de causa Inicial das Improcedências',
                        valorHint: 'Soma do valor de causa inicial das sentenças improcedentes no escopo selecionado.',
                        mapaTitulo: 'Improcedências por comarca',
                        mapaInfo:
                            'Quantidade e valor de causa (inicial) das sentenças improcedentes por comarca, no escopo selecionado. Clique para filtrar.',
                        mapaInfoDetalhada:
                            'Cor e tamanho do município pela quantidade de sentenças improcedentes (raiz quadrada); passe o mouse para ver quantidade e valor. Clique num município para filtrar a página pela comarca correspondente. Revertidas em 2G = improcedentes cujo acórdão foi procedente ou parcialmente procedente (com ou sem proveito econômico); sentença anulada não conta.',
                        motivoTitulo: 'Motivo das improcedências',
                        motivoInfo:
                            'Sentenças improcedentes, agrupadas pelo motivo informado no 1º grau, no escopo selecionado. Clique para filtrar.',
                        juizTitulo: 'Juízes que mais julgam improcedente',
                        juizInfo: 'Sentenças improcedentes por juiz (1G), no escopo selecionado. Clique para filtrar.',
                    }}
                />
            </DashSection>
        </div>
    )
}

type TextosEstudo = {
    totalTitulo: string
    totalIcone: 'ban' | 'x-circle'
    totalTom: 'warn' | 'danger'
    totalHint: string
    valorTitulo: string
    valorHint: string
    mapaTitulo: string
    mapaInfo: string
    mapaInfoDetalhada: string
    motivoTitulo: string
    motivoInfo: string
    juizTitulo: string
    juizInfo: string
}

// Um estudo da v1 (Extinção ou Improcedências), no escopo escolhido: os dois cards (total e valor de causa), o mapa
// por comarca (com a 3ª coluna das revertidas em 2G) e as barras por motivo e por juiz. Clicar filtra a página.
function EstudoSentencas({
    estudo,
    total,
    valorCausa,
    totalNoEscopo,
    revertidos,
    mapa,
    comarcas,
    filters,
    filtrar,
    textos,
    textosMapa,
}: {
    estudo: Estudo
    total: number | null
    valorCausa: number | null
    totalNoEscopo: number | null
    revertidos: number | null
    mapa: ReturnType<typeof mapaDaUnidade>
    comarcas: string[]
    filters: ContentProps<JulgadosSentencasResponse>['filters']
    filtrar: (key: SentencasFilterKey) => ((name: string) => void) | undefined
    textos: TextosEstudo
    textosMapa?: Parameters<typeof ComarcaMapa>[0]['textos']
}) {
    const f = filters ?? {}
    const porComarca = ordenados(estudo.porComarca)
    const valorPorComarca = ordenados(estudo.porComarca.map((p) => ({ ...p, value: p.valorCausa ?? 0 })))
    return (
        <div className="stack">
            <div className="grid jl-dois">
                <HeroStat
                    label={textos.totalTitulo}
                    icon={textos.totalIcone}
                    tone={textos.totalTom}
                    value={valor(total, fmt.int)}
                    hint={textos.totalHint}
                />
                <HeroStat
                    label={textos.valorTitulo}
                    icon="dollar"
                    tone="ok"
                    value={valor(valorCausa, fmt.brl)}
                    hint={textos.valorHint}
                />
            </div>

            <ComarcaMapa
                title={textos.mapaTitulo}
                geo={mapa.geo}
                quantidade={porComarca}
                valor={valorPorComarca}
                comarcas={comarcas}
                selected={f.comarca_julgados}
                onSelect={filtrar('comarca_julgados')}
                capital={mapa.capital}
                totalJulgados={totalNoEscopo ?? 0}
                revertidos={revertidos ?? 0}
                textos={textosMapa}
                height={520}
                viewWidth={1320}
                info={textos.mapaInfo}
                infoDetalhada={textos.mapaInfoDetalhada}
            />

            <div className="grid jl-dois">
                <ChartCard title={textos.motivoTitulo} action={<Acoes info={textos.motivoInfo} />}>
                    <div className="jl-scroll">
                        <BarList
                            items={ordenados(estudo.porMotivo)}
                            showShare
                            wrapNames
                            selected={f.motivo_extincao_julgados}
                            onSelect={filtrar('motivo_extincao_julgados')}
                            selectLabel="Filtrar pelo motivo"
                        />
                    </div>
                </ChartCard>
                <ChartCard title={textos.juizTitulo} action={<Acoes info={textos.juizInfo} />}>
                    <div className="jl-scroll">
                        <BarList
                            items={ordenados(estudo.porJuiz)}
                            showShare
                            wrapNames
                            selected={f.juiz_julgados}
                            onSelect={filtrar('juiz_julgados')}
                            selectLabel="Filtrar pelo juiz"
                        />
                    </div>
                </ChartCard>
            </div>
        </div>
    )
}
