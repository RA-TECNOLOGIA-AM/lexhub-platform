import { useState, type ReactNode } from 'react'
import { ChartCard, ChartEmpty } from '../../../components/charts/ChartCard.tsx'
import { GaugeChart } from '../../../components/charts/GaugeChart.tsx'
import { LineChart } from '../../../components/charts/LineChart.tsx'
import { MapaComarcas } from '../../../components/charts/MapaComarcas.tsx'
import { PieChart } from '../../../components/charts/PieChart.tsx'
import { Pill } from '../../../components/dashboard/StatCard.tsx'
import { DataTable } from '../../../components/ui/DataTable.tsx'
import { Icon } from '../../../components/ui/Icon.tsx'
import { Modal } from '../../../components/ui/Modal.tsx'
import { Segmented } from '../../../components/ui/Segmented.tsx'
import { pieSlices, seriesByYear } from '../../../lib/charts.ts'
import { fmt } from '../../../lib/format.ts'
import type { Point } from '../../../types/index.ts'
import { CORES_ANO, MESES, diaLongo, mesNome } from '../setor/datas.ts'
import { mesParcial } from '../setor/setor.ts'
import { numeroCnj, type Comarcas, type ProcessoLista } from './setorExecucao.ts'
import { usePagina } from './usePagina.ts'

// Peças das páginas de Execução Condenação e Execução Acordos (NG), no layout da V2.

// "Mês a mês" por ano, como a v1: uma linha por ano, os anteriores tracejados e o atual cheio, com degradê.
export function MesAMes({
    pontos,
    format = fmt.int,
    height = 320,
    onSelectMes,
}: {
    pontos: Point[]
    format?: (v: number) => string
    height?: number
    onSelectMes?: (ano: number, mes: number) => void // clicar num mês (mes 1–12; o ano mais recente com dado nele)
}) {
    const anos = seriesByYear(pontos)
    if (anos.length === 0) return <ChartEmpty>Sem dados no histórico.</ChartEmpty>
    const ultimo = anos.length - 1
    const parcial = mesParcial(anos[ultimo].year)
    return (
        <LineChart
            height={height}
            legend
            emphasizeData
            format={format}
            labels={MESES}
            partial={parcial !== null ? { series: ultimo, index: parcial } : undefined}
            tooltip={{ heading: 'Mês', title: mesNome }}
            onSelect={
                onSelectMes &&
                ((i) => {
                    const ano = [...anos].reverse().find((a) => a.values[i] !== null)
                    if (ano) onSelectMes(ano.year, i + 1)
                })
            }
            selectLabel={onSelectMes && 'Ver os dias do mês'}
            series={anos.map((a, i) => ({
                label: String(a.year),
                color: CORES_ANO[(anos.length - 1 - i) % CORES_ANO.length],
                values: a.values,
                dashed: i < ultimo,
                area: i === ultimo,
            }))}
        />
    )
}

// Taxa de Redução de Estoque (TRE), o medidor da v1: de -50 a 50, com 2 casas.
export function TreCard({ tre }: { tre: number | null }) {
    return (
        <ChartCard
            title="Taxa de Redução Estoque (TRE)"
            subtitle="Saídas sobre o estoque no período"
            action={
                <Pill tone={tre === null ? 'neutral' : tre > 0 ? 'ok' : tre < 0 ? 'danger' : 'neutral'}>
                    {tre === null ? '—' : fmt.dec2(tre)}
                </Pill>
            }
        >
            <div className="ex-gauge">
                <GaugeChart value={tre ?? 0} min={-50} max={50} marker={0} format={fmt.dec2} color="var(--chart-1)" />
            </div>
        </ChartCard>
    )
}

export type ModoComarca = 'total' | 'entrada' | 'saida'
const MODOS: { value: ModoComarca; label: string }[] = [
    { value: 'total', label: 'Total' },
    { value: 'entrada', label: 'Entradas' },
    { value: 'saida', label: 'Saídas' },
]

// O mapa de processos por comarca da v1: Total (agora), Entradas ou Saídas (no período). Passar o cursor num
// município mostra a quantidade, o valor e o tempo médio na comarca; clicar filtra a página por ela.
export function ComarcaCard({
    dados,
    comarcas,
    selected,
    onSelect,
    titulo = 'Mapa de processos por comarca',
    rotuloItem = 'processo(s)',
}: {
    dados: Record<ModoComarca, Comarcas>
    comarcas: string[]
    selected: string[]
    onSelect?: (comarca: string) => void
    titulo?: string
    rotuloItem?: string
}) {
    const [modo, setModo] = useState<ModoComarca>('total')
    const { quantidade, valor } = dados[modo]
    return (
        <ChartCard
            title={titulo}
            subtitle={
                modo === 'total'
                    ? 'Em execução agora, por comarca · passe o cursor para ver os números, clique para filtrar'
                    : `${modo === 'entrada' ? 'Entradas' : 'Saídas'} no período, por comarca · passe o cursor para ver os números`
            }
            action={<Segmented label="Critério do mapa" options={MODOS} value={modo} onChange={setModo} />}
        >
            <MapaComarcas
                quantidade={quantidade}
                valor={valor}
                comarcas={comarcas}
                selected={selected}
                onSelect={onSelect}
                rotuloItem={rotuloItem}
            />
        </ChartCard>
    )
}

// O aviso da v1 de processos sem valor ("Existem N processos com valor da execução vazios!"), com a lista.
export function SemValorAviso({ total, processos, campo }: { total: number; processos: string[]; campo: string }) {
    const [aberto, setAberto] = useState(false)
    if (total <= 0) return null
    return (
        <>
            <div className="card fe-aviso small ex-aviso">
                <Icon name="alert" size={16} />
                <span>
                    Existem <strong className="num">{fmt.int(total)}</strong> processos com {campo} vazio.
                </span>
                {processos.length > 0 && (
                    <button type="button" className="btn ex-aviso-btn" onClick={() => setAberto(true)}>
                        Ver processos
                    </button>
                )}
            </div>
            {aberto && (
                <Modal
                    title="Processos sem valor"
                    subtitle={`${fmt.int(processos.length)} processo(s) com ${campo} vazio no LexFlow`}
                    onClose={() => setAberto(false)}
                >
                    <ul className="ex-lista-simples num">
                        {processos.map((p, i) => (
                            <li key={`${p}-${i}`}>{numeroCnj(p)}</li>
                        ))}
                    </ul>
                </Modal>
            )}
        </>
    )
}

// Paginação simples (Anterior · 1 de 8 · Próxima) embaixo de uma tabela.
export function Paginador({
    pagina,
    total,
    onChange,
}: {
    pagina: number
    total: number
    onChange: (p: number) => void
}) {
    if (total <= 1) return null
    return (
        <nav className="ex-pager" aria-label="Páginas">
            <button type="button" className="btn" disabled={pagina <= 0} onClick={() => onChange(pagina - 1)}>
                Anterior
            </button>
            <span className="muted small num">
                {pagina + 1} de {total}
            </span>
            <button type="button" className="btn" disabled={pagina >= total - 1} onClick={() => onChange(pagina + 1)}>
                Próxima
            </button>
        </nav>
    )
}

// Processos com nº, UF, subfase, data da execução e valor (a lista do "Valor Realizado" e as execuções de acordo).
export function ProcessosTabela({
    processos,
    rotuloValor = 'Valor da execução',
    porPagina = 10,
    vazio = 'Nenhum processo.',
}: {
    processos: ProcessoLista[]
    rotuloValor?: string
    porPagina?: number
    vazio?: string
}) {
    const p = usePagina(processos, porPagina)
    return (
        <>
            <DataTable
                rows={p.itens}
                rowKey={(r) => `${r.processo}-${r.dataExecucao ?? ''}-${r.subfase}`}
                empty={vazio}
                columns={[
                    { header: 'Nº do processo', render: (r) => <span className="num">{numeroCnj(r.processo)}</span> },
                    { header: 'UF', render: (r) => r.uf || '—' },
                    {
                        header: 'Data da execução',
                        render: (r) => (r.dataExecucao ? diaLongo(r.dataExecucao.slice(0, 10)) : '—'),
                    },
                    { header: rotuloValor, align: 'right', render: (r) => (r.valor === null ? '—' : fmt.brl(r.valor)) },
                    { header: 'Subfase', render: (r) => <span className="muted">{r.subfase || '—'}</span> },
                ]}
            />
            <Paginador pagina={p.pagina} total={p.total} onChange={p.setPagina} />
        </>
    )
}

// Um card de número que filtra ao clicar (os cards de Diligências da v1).
export function CardFiltro({
    ativo,
    onClick,
    rotuloAcao,
    children,
}: {
    ativo?: boolean
    onClick: () => void
    rotuloAcao: string
    children: ReactNode
}) {
    return (
        <button
            type="button"
            className={ativo ? 'ex-cardbtn on' : 'ex-cardbtn'}
            aria-pressed={ativo}
            aria-label={rotuloAcao}
            onClick={onClick}
        >
            {children}
        </button>
    )
}

// Pizza com a legenda ao lado (nome, quantidade e %), para quando os rótulos em volta não cabem (ex.: matérias).
// As mesmas fatias e cores do PieChart (as `max` maiores e "Outras"); clicar na legenda filtra como a fatia.
export function PizzaLegenda({
    items,
    max = 8,
    centerLabel,
    selected = [],
    onSelect,
    selectLabel = 'Filtrar por',
}: {
    items: Point[]
    max?: number
    centerLabel: string
    selected?: string[]
    onSelect?: (name: string) => void
    selectLabel?: string
}) {
    const [hover, setHover] = useState<string | null>(null)
    const fatias = pieSlices(items, max, 'Outras')
    if (fatias.length === 0) return <ChartEmpty />
    const cor = (k: number, outras: number) => (outras ? 'var(--pie-rest)' : `var(--pie-${(k % 10) + 1})`)
    return (
        <div className="ex-pizza">
            <PieChart
                items={items}
                max={max}
                size={220}
                centerLabel={centerLabel}
                selected={selected}
                onSelect={onSelect && ((n) => n !== 'Outras' && onSelect(n))}
                selectLabel={selectLabel}
                hover={hover}
                onHover={setHover}
            />
            <ul className="ex-pizza-leg" role="list">
                {fatias.map((f, k) => {
                    const clicavel = onSelect && !f.others
                    const ativo = selected.includes(f.name)
                    const conteudo = (
                        <>
                            <span className="chart-key dot" style={{ background: cor(k, f.others) }} />
                            <span className="ex-pizza-nome" title={f.name}>
                                {f.others ? `Outras (${f.others})` : f.name}
                            </span>
                            <span className="num">{fmt.int(f.value)}</span>
                            <span className="num muted">{fmt.dec1(f.share)}%</span>
                        </>
                    )
                    return (
                        <li
                            key={f.name}
                            className={
                                [hover === f.name && 'on', selected.length > 0 && !ativo && 'dim']
                                    .filter(Boolean)
                                    .join(' ') || undefined
                            }
                            onMouseEnter={() => setHover(f.name)}
                            onMouseLeave={() => setHover(null)}
                        >
                            {clicavel ? (
                                <button
                                    type="button"
                                    aria-pressed={ativo}
                                    aria-label={`${selectLabel} ${f.name} (${fmt.int(f.value)})`}
                                    onClick={() => onSelect(f.name)}
                                >
                                    {conteudo}
                                </button>
                            ) : (
                                <div>{conteudo}</div>
                            )}
                        </li>
                    )
                })}
            </ul>
        </div>
    )
}
