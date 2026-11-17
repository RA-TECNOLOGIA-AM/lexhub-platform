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
import { fmt, show } from '../../../lib/format.ts'
import type { ContentProps } from '../types.ts'
import { AcordaosLista } from './AcordaosLista.tsx'
import { DadosFaltando } from './DadosFaltando.tsx'
import { lerJulgadosAcordaos, type Escopo } from './fields.ts'
import { valorDoFiltro, type JulgadosFilterKey } from './filters.ts'
import {
    CATEGORIAS,
    MESES_NOME_COMPLETO,
    STATUS_EMBARGOS,
    acordaosPorAno,
    avisosDadosFaltando,
    composicao,
    coresDosAnos,
    mapaDaUnidade,
    taxaDoAno,
    totalDoAno,
    type AnoAcordaos,
    type Categoria,
} from './julgados.ts'
import { LegendaCategorias, RelatoresRanking } from './RelatoresRanking.tsx'
import { TaxaProcedencia } from './TaxaProcedencia.tsx'
import type { JulgadosAcordaosResponse, PontoJulgados } from './types.ts'
import './julgados.css'

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

// A cor de cada fatia na ordem dada (a mesma paleta da pizza da casa), para a legenda usar a mesma.
type Fatia = PontoJulgados & { color: string }
const comCor = (itens: PontoJulgados[]): Fatia[] => itens.map((p, i) => ({ ...p, color: `var(--pie-${(i % 10) + 1})` }))

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

// O Julgados Acórdãos (LexFlow: NG, LA e RJ), com as seções, os cards e os gráficos da página da v1
// (julgados_acordao_{NG,LA,RJ}.tsx), na mesma ordem. Carregar, erros, cabeçalho (Exportar, Atualizar, documentação),
// período e a janela Filtros ficam no DashboardView. Clicar num card de categoria, numa fatia, num relator ou numa
// barra liga ou desliga o filtro correspondente (toggleJulgadosAcordaoFilterValue da v1). Os nomes dos campos mudam
// por unidade: quem escolhe é fields.ts.
export function JulgadosAcordaosContent({
    data,
    filters = {},
    onToggleFilter,
}: ContentProps<JulgadosAcordaosResponse>) {
    const [anoEscolhido, setAnoEscolhido] = useState<number | null>(null)
    const [categoriaAnual, setCategoriaAnual] = useState<Categoria>('procedente')
    const [categoriaTaxa, setCategoriaTaxa] = useState<Categoria>('procedente')
    const [escopo, setEscopo] = useState<Escopo>('estoque')

    const j = lerJulgadosAcordaos(data)
    if (j.unit === null) {
        return <ChartEmpty>Julgados Acórdãos só existe para as unidades NG, LA e RJ.</ChartEmpty>
    }
    const { n, comparativo: c } = j

    // Clique num gráfico: o valor limpo (UF em maiúsculas), sem filtro vazio.
    const filtrar = (key: JulgadosFilterKey) =>
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

    // Estudo das Improcedências: estoque (base inteira já julgada) ou entrada (só o período).
    const estoque = escopo === 'estoque'
    const imp = j.improcedencia[escopo]
    const impTotal = estoque ? n.improcedenciaTotalEstoque : n.improcedentes
    const impValor = estoque ? n.improcedenciaValorEstoque : n.improcedenciaValor
    const totalNoEscopo = estoque ? n.totalEstoque : n.total
    const stj = (estoque ? n.improcedenciaStjEstoque : n.improcedenciaStj) ?? 0
    const stf = (estoque ? n.improcedenciaStfEstoque : n.improcedenciaStf) ?? 0
    // O mapa (como a v1): quantidade por comarca e, para a dica do cursor, o valor de causa.
    const mapa = mapaDaUnidade(j.unit)
    const impPorComarca = ordenados(imp.porComarca)
    const impValorPorComarca = ordenados(imp.porComarca.map((p) => ({ ...p, value: p.valorCausa ?? 0 })))

    const totalMateria = j.porMateria.reduce((s, p) => s + p.value, 0)
    // Cor fixa por fatia (a da pizza), para a legenda embaixo dizer qual é qual.
    const materias = comCor(ordenados(j.porMateria))
    const anosAjuizamento = comCor(j.porAnoAjuizamento)
    const ng = j.unit === 'NG'

    return (
        <div className="dsecs jl">
            <DadosFaltando avisos={avisosDadosFaltando(n)} itens={j.dadosFaltando} />

            <DashSection
                index={1}
                eyebrow="Visão geral"
                title="Acórdão (2º Grau)"
                subtitle="Processos com acórdão proferido no período selecionado."
            >
                <div className="stack">
                    <div className="grid grid-stat-3 jl-cards">
                        <HeroStat
                            label="Total de Acórdãos"
                            icon="scale"
                            tone="accent"
                            value={valor(n.total, fmt.int)}
                            below={<DeltaPill value={c.total} suffix={VS} plain />}
                            hint="Processos com acórdão no período, comparados ao período anterior de mesma duração"
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
                                hint="Status 2G procedente (total ou parcial, com ou sem proveito econômico), comparados ao período anterior de mesma duração. Clique para filtrar a página."
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
                                hint="Status 2G improcedente, comparados ao período anterior de mesma duração. Clique para filtrar a página."
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
                                hint="Status 2G extinto sem mérito, comparados ao período anterior de mesma duração. Clique para filtrar a página."
                            />,
                        )}
                        <HeroStat
                            label="Não classificados"
                            icon="info"
                            tone="neutral"
                            value={valor(n.naoClassificados, fmt.int)}
                            below={<DeltaPill value={c.naoClassificados} suffix={VS} plain />}
                            hint="Status 2G fora de Procedente/Improcedente/Extinto (ex.: sentença anulada, encerrado 1G, ou sem status lançado), comparados ao período anterior de mesma duração."
                        />
                        <HeroStat
                            label="Média sentença → acórdão"
                            icon="clock"
                            tone="info"
                            value={dias(n.tempoMedio)}
                            below={<DeltaPill value={c.tempoMedio} betterWhenDown suffix={VS} plain />}
                            hint="Média de dias entre a data da sentença (1G) e a data do acórdão, para os acórdãos do período com as duas datas, comparada ao período anterior de mesma duração."
                        />
                    </div>

                    {/* Largura toda, como a Distribuição por rubrica do Comercial (LexPre): rótulos em volta da
                        rosca (nome, quantidade e %), a fatia sob o cursor no meio e clique para filtrar. */}
                    <ChartCard
                        title="Resultado dos embargos"
                        subtitle={`${fmt.int(totalEmbargos)} acórdão(s) de embargos no período · clique na fatia para filtrar`}
                        action={
                            <Acoes info="Acórdãos de embargos com data no período (eixo: data do acórdão de embargos, não do acórdão original), pelo Status Resultante da matriz (mérito antes dos embargos × resultado lançado). Com data e sem resultado lançado: “Sem resultado lançado”. Clique para filtrar." />
                        }
                        footer={
                            <>
                                Tempo médio entre o acórdão e os embargos:{' '}
                                <strong className="num">{dias(n.embargosTempoMedio)}</strong>
                            </>
                        }
                    >
                        {embargos.length > 0 ? (
                            <PieChart
                                items={embargos}
                                centerLabel="embargos"
                                labels
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

                    <div className="grid jl-linha2">
                        <HeroStat
                            label={ng ? 'Valor acórdãos procedentes' : 'Valor dos acórdãos procedentes'}
                            icon="dollar"
                            tone="ok"
                            value={valor(n.valorFixado, fmt.brl)}
                            below={<DeltaPill value={c.valorFixado} suffix={VS} plain />}
                            hint='Soma do valor fixado no acórdão (VALOR_ACORDAO, o mesmo da coluna "Valor do Acórdão" do relatório) dos acórdãos procedentes no período, comparada ao período anterior de mesma duração.'
                        />
                        <TaxaProcedencia c={comp} className="jl-span3" />
                    </div>

                    <div className="grid jl-tres">
                        <ChartCard
                            title="Ranking de Relatores"
                            subtitle="Acórdãos (2G) no período · clique para filtrar"
                            action={<LegendaCategorias />}
                        >
                            <div className="jl-scroll">
                                <RelatoresRanking
                                    rows={j.ranking}
                                    selected={filters.relator_julgados}
                                    onSelect={filtrar('relator_julgados')}
                                />
                            </div>
                        </ChartCard>
                        <ChartCard
                            title="Acórdãos por matéria"
                            subtitle={`${fmt.int(totalMateria)} acórdão(s) no período · clique na fatia para filtrar`}
                        >
                            {materias.length > 0 ? (
                                <PieChart
                                    items={materias}
                                    size={260}
                                    labels
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
                            title="Ano de Ajuizamento — Total em Acórdãos"
                            action={
                                <Acoes info="Total de acórdãos do período (todas as categorias), agrupados pelo ano de ajuizamento (distribuição) do processo, com quantidade e valor de causa somado por ano. Clique para filtrar." />
                            }
                        >
                            <PieChart
                                items={anosAjuizamento}
                                size={220}
                                sort={false}
                                labels
                                selected={filters.ano_ajuizamento_julgados}
                                onSelect={filtrar('ano_ajuizamento_julgados')}
                                selectLabel="Filtrar pelo ano de ajuizamento"
                            />
                            <AnoAjuizamentoTabela itens={anosAjuizamento} />
                        </ChartCard>
                    </div>

                    <div className="grid jl-tres">
                        <ChartCard
                            title="Acórdãos por competência"
                            action={
                                <Acoes info="Acórdãos no período, agrupados por competência. Clique para filtrar." />
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
                            title="Acórdãos por comarca"
                            action={<Acoes info="Acórdãos no período, agrupados por comarca. Clique para filtrar." />}
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
                        <ChartCard
                            title="Motivo das extinções"
                            action={
                                <Acoes info="Acórdãos extintos no período, agrupados pelo motivo informado. Clique para filtrar." />
                            }
                        >
                            <div className="jl-scroll">
                                <BarList
                                    items={ordenados(j.porMotivoExtincao)}
                                    showShare
                                    wrapNames
                                    selected={filters.motivo_extincao_julgados}
                                    onSelect={filtrar('motivo_extincao_julgados')}
                                    selectLabel="Filtrar pelo motivo"
                                />
                            </div>
                        </ChartCard>
                    </div>

                    <div className="grid jl-dois">
                        <ChartCard
                            title="Acórdãos mês a mês"
                            action={
                                ano && (
                                    <label className="field-select">
                                        <span className="sr-only">Ano</span>
                                        <select
                                            value={ano.ano}
                                            onChange={(e) => setAnoEscolhido(Number(e.target.value))}
                                        >
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
                                        ? CATEGORIAS.map((k) => ({
                                              label: k.label,
                                              color: k.color,
                                              values: ano[k.value],
                                          }))
                                        : []
                                }
                            />
                        </ChartCard>
                        <ChartCard title="Total de acórdãos por ano">
                            <LineChart
                                height={320}
                                legend
                                labels={MESES_NOME_COMPLETO}
                                tooltip={tooltipMes}
                                series={porAno(totalDoAno)}
                            />
                        </ChartCard>
                    </div>

                    <div className="grid jl-dois">
                        <ChartCard
                            title="Acórdãos por ano"
                            action={
                                <SeletorCategoria
                                    label="Categoria do gráfico Acórdãos por ano"
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
                                <Acoes info="Por mês e ano: acórdãos da categoria escolhida ÷ (procedentes + improcedentes + extintos), mesma base do card Taxa de procedência. Meses sem acórdão decidido ficam sem ponto.">
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

                    <AcordaosLista itens={j.lista} />
                </div>
            </DashSection>

            <DashSection
                index={2}
                eyebrow="Improcedência"
                title="Estudo das Improcedências"
                subtitle="Comarca, valor de causa, motivo e relatores por trás dos acórdãos improcedentes — total já julgado na base ou só o que entrou no período selecionado no topo da página."
                action={
                    <Segmented
                        label="Escopo do Estudo das Improcedências"
                        options={[
                            { value: 'estoque', label: 'Total (estoque)' },
                            { value: 'entrada', label: 'Entrada no período' },
                        ]}
                        value={escopo}
                        onChange={setEscopo}
                    />
                }
            >
                <div className="stack">
                    <div className="grid jl-dois">
                        <HeroStat
                            label="Total de Improcedências"
                            icon="x-circle"
                            tone="danger"
                            value={valor(impTotal, fmt.int)}
                            hint={
                                estoque
                                    ? 'Acórdãos improcedentes em toda a base já julgada (estoque).'
                                    : 'Acórdãos improcedentes no período selecionado.'
                            }
                        />
                        <HeroStat
                            label="Valor de causa Inicial das Improcedências"
                            icon="dollar"
                            tone="ok"
                            value={valor(impValor, fmt.brl)}
                            hint="Soma do valor de causa inicial dos acórdãos improcedentes no escopo selecionado."
                        />
                    </div>

                    <ComarcaMapa
                        title="Improcedências por comarca"
                        geo={mapa.geo}
                        quantidade={impPorComarca}
                        valor={impValorPorComarca}
                        comarcas={j.comarcaOpcoes}
                        selected={filters.comarca_julgados}
                        onSelect={filtrar('comarca_julgados')}
                        capital={mapa.capital}
                        totalJulgados={totalNoEscopo ?? 0}
                        // Só a NG conta os recursos ao STJ/STF (3ª coluna da legenda).
                        revertidos={ng ? stj + stf : undefined}
                        textos={
                            ng
                                ? {
                                      categoriaPlural: 'improcedentes',
                                      revertidosTitulo: 'Recursos ao STJ / STF',
                                      revertidosDescricao: `subiram — ${fmt.int(stj)} Recurso Especial (STJ) · ${fmt.int(stf)} Recurso Extraordinário (STF)`,
                                      revertidosFrase: 'sobe ao STJ ou ao STF.',
                                  }
                                : { categoriaPlural: 'improcedentes' }
                        }
                        height={520}
                        viewWidth={1320}
                        info="Quantidade e valor de causa (inicial) dos acórdãos improcedentes por comarca, no escopo selecionado. Clique para filtrar."
                        infoDetalhada={
                            ng
                                ? 'Cor e tamanho do município pela quantidade de acórdãos improcedentes (raiz quadrada); passe o mouse para ver quantidade, valor e tempo médio sentença → acórdão da comarca. Clique num município para filtrar a página pela comarca correspondente. A 3ª coluna da legenda mostra quantos acórdãos improcedentes subiram ao STJ (Recurso Especial) ou ao STF (Recurso Extraordinário), pela subfase atual do processo — os demais seguem para trânsito/arquivamento.'
                                : 'Cor e tamanho do município pela quantidade de acórdãos improcedentes (raiz quadrada); passe o mouse para ver quantidade, valor e tempo médio sentença → acórdão da comarca. Clique num município para filtrar a página pela comarca correspondente.'
                        }
                    />

                    <div className="grid jl-dois">
                        <ChartCard
                            title="Motivo das improcedências"
                            action={
                                <Acoes info="Acórdãos improcedentes, agrupados pelo motivo informado no 2º grau, no escopo selecionado. Clique para filtrar." />
                            }
                        >
                            <div className="jl-scroll">
                                <BarList
                                    items={ordenados(imp.porMotivo)}
                                    showShare
                                    wrapNames
                                    selected={filters.motivo_extincao_julgados}
                                    onSelect={filtrar('motivo_extincao_julgados')}
                                    selectLabel="Filtrar pelo motivo"
                                />
                            </div>
                        </ChartCard>
                        <ChartCard
                            title="Relatores que mais julgam improcedente"
                            action={
                                <Acoes info="Acórdãos improcedentes por relator (2G), no escopo selecionado. Clique para filtrar." />
                            }
                        >
                            <div className="jl-scroll">
                                <BarList
                                    items={ordenados(imp.porRelator)}
                                    showShare
                                    wrapNames
                                    selected={filters.relator_julgados}
                                    onSelect={filtrar('relator_julgados')}
                                    selectLabel="Filtrar pelo relator"
                                />
                            </div>
                        </ChartCard>
                    </div>
                </div>
            </DashSection>
        </div>
    )
}

// O valor de causa de cada ano, embaixo da pizza (na v1 ia no rótulo da fatia: "2023 12 (30,0%) · R$ 1,2 mi").
function AnoAjuizamentoTabela({ itens }: { itens: Fatia[] }) {
    if (itens.length === 0) return null
    const total = itens.reduce((s, p) => s + p.value, 0)
    return (
        <table className="tbl jl-mini-tbl">
            <thead>
                <tr>
                    <th scope="col">Ano</th>
                    <th scope="col" className="num">
                        Acórdãos
                    </th>
                    <th scope="col" className="num">
                        Valor de causa
                    </th>
                </tr>
            </thead>
            <tbody>
                {itens.map((p) => (
                    <tr key={p.name}>
                        <td>
                            <span className="jl-ano">
                                <span className="chart-key dot" style={{ background: p.color }} />
                                {p.name}
                            </span>
                        </td>
                        <td className="num">
                            {fmt.int(p.value)}{' '}
                            <span className="muted">({fmt.dec1(total ? (p.value / total) * 100 : 0)}%)</span>
                        </td>
                        <td className="num">{show(p.valorCausa, fmt.brlShort)}</td>
                    </tr>
                ))}
            </tbody>
        </table>
    )
}
