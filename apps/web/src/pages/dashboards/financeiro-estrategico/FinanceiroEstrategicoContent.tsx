import { useState, type ReactNode } from 'react'
import { BarList } from '../../../components/charts/BarList.tsx'
import { ChartCard, ChartEmpty } from '../../../components/charts/ChartCard.tsx'
import { ColumnChart } from '../../../components/charts/ColumnChart.tsx'
import { LineChart } from '../../../components/charts/LineChart.tsx'
import { PieChart } from '../../../components/charts/PieChart.tsx'
import { DashSection } from '../../../components/dashboard/DashSection.tsx'
import { DeltaPill, FootRow, HeroStat, MiniStat, Pill, StackedRate } from '../../../components/dashboard/StatCard.tsx'
import type { Tone } from '../../../components/dashboard/tone.ts'
import { CountUp } from '../../../components/ui/CountUp.tsx'
import { Icon } from '../../../components/ui/Icon.tsx'
import { Modal } from '../../../components/ui/Modal.tsx'
import { toggleFilter } from '../../../lib/filters.ts'
import { fmt } from '../../../lib/format.ts'
import type { DashboardFilters } from '../../../types/index.ts'
import type { ContentProps } from '../types.ts'
import { CORES_ANO, MESES, mesNome, periodo } from '../setor/datas.ts'
import { mesParcial, share } from '../setor/setor.ts'
import { compacto } from '../meta-anual/metaAnual.ts'
import { OPCOES_MES, barrasReflexo, colunasPrevisao, seriesPorAno } from './financeiroEstrategico.ts'
import type {
    Cenario,
    ClientesPendentes,
    Conversao,
    FinanceiroEstrategicoResponse,
    MesHistorico,
    OrigemFatia,
    Previsao,
    ReflexoFinanceiro,
} from './types.ts'

const VS = ' vs mês anterior'
const OUTROS = 'OUTROS' // fatia que junta as menores matérias: não vira filtro
const pct2 = (v: number) => `${fmt.dec2(v)}%`
const semMoeda = (v: number) => compacto(v).replace('R$ ', '') // rótulo curto em cima da barra

type Filtrar = {
    filters: DashboardFilters
    toggle?: (key: keyof DashboardFilters, value: string) => void
}

// O Financeiro Estratégico: a página da v1 (FinanceiroEstrategicoNG.tsx) no layout novo. Receita da planilha do
// financeiro (aba REPASSES CLIENTES) pela data do TED, o valor protocolado do LexFlow, a conversão, a evolução e
// a previsão da receita. Carregar, erros, cabeçalho, período e filtros (Origem, Matéria, Ano de ajuizamento)
// ficam no DashboardView; clicar numa fatia liga o filtro. A Conversão e o modal de Clientes Pendentes têm os
// próprios seletores de ano (e mês), como na v1.
export function FinanceiroEstrategicoContent({
    data,
    filters = {},
    onToggleFilter,
    onFiltersChange,
}: ContentProps<FinanceiroEstrategicoResponse>) {
    const [pendentesAberto, setPendentesAberto] = useState(false)
    const r = data.reflexo_financeiro
    if (!r) return <ChartEmpty>Sem dados da planilha do financeiro para esta unidade.</ChartEmpty>
    const f: Filtrar = { filters, toggle: onToggleFilter }
    // Seletores da seção / do modal: trocam só a própria chave (os filtros da página ficam).
    const marcar =
        onFiltersChange &&
        ((key: keyof DashboardFilters, value: string) => onFiltersChange(toggleFilter(filters, key, value)))
    const limpar =
        onFiltersChange &&
        ((key: keyof DashboardFilters) => {
            const next = { ...filters }
            delete next[key]
            onFiltersChange(next)
        })

    return (
        <div className="dsecs">
            <ReflexoSecao r={r} f={f} meta={data.meta} onPendentes={() => setPendentesAberto(true)} />
            <AjuizamentoSecao r={r} f={f} />
            {data.conversao && <ConversaoSecao c={data.conversao} filters={filters} marcar={marcar} limpar={limpar} />}
            <DashSection
                index={4}
                eyebrow="Evolução"
                title="Evolução"
                subtitle="Receita por ano do TED e o crescimento sobre o ano anterior."
            >
                <EvolucaoCard evolucao={r.evolucao_anual} />
            </DashSection>
            {data.previsao && <PrevisaoSecao p={data.previsao} />}
            {pendentesAberto && data.clientes_pendentes && (
                <PendentesModal
                    c={data.clientes_pendentes}
                    filters={filters}
                    marcar={marcar}
                    limpar={limpar}
                    onClose={() => setPendentesAberto(false)}
                />
            )}
        </div>
    )
}

// --- Peças comuns --------------------------------------------------------------------------------------------

// Pizza de receita por matéria (8 maiores + Outros): clicar numa matéria filtra a página.
function PizzaMaterias({ itens, f, centro }: { itens: { name: string; value: number }[]; f: Filtrar; centro: string }) {
    return (
        <PieChart
            items={itens}
            size={240}
            format={compacto}
            centerFormat={semMoeda}
            centerLabel={centro}
            selected={f.filters.materia}
            onSelect={f.toggle && ((name) => name !== OUTROS && f.toggle?.('materia', name))}
            selectLabel="Filtrar pela matéria"
        />
    )
}

// Origem: Condenação x Acordo pela quantidade (a fatia e o %), com a receita de cada uma embaixo.
function PizzaOrigem({ origem, f }: { origem: OrigemFatia[]; f: Filtrar }) {
    return (
        <>
            <PieChart
                items={origem.map((o) => ({ name: o.name, value: o.quantidade }))}
                size={220}
                sort={false}
                centerLabel="TEDs"
                selected={f.filters.origem}
                onSelect={f.toggle && ((name) => f.toggle?.('origem', name))}
                selectLabel="Filtrar pela origem"
            />
            <ul className="fe-legenda" role="list">
                {origem.map((o) => (
                    <li key={o.name}>
                        <span>{o.name}</span>
                        <span className="num muted">
                            {fmt.int(o.quantidade)} · {fmt.dec1(o.percentual)}%
                        </span>
                        <strong className="num">{fmt.brl(o.valor)}</strong>
                    </li>
                ))}
            </ul>
        </>
    )
}

// "Valor da Causa x Valor da Receita": as duas barras e quanto da causa virou receita.
function CausaReceita({ causa, receita }: { causa: number; receita: number }) {
    return (
        <div className="fe-funil">
            <BarList
                items={[
                    { name: 'Valor da causa', value: causa },
                    { name: 'Valor da receita', value: receita },
                ]}
                format={fmt.brl}
                valueOutside
            />
            <span className="small muted">
                A receita é <strong className="num">{fmt.dec1(share(receita, causa))}%</strong> do valor da causa.
            </span>
        </div>
    )
}

// Uma linha por ano, jan–dez (anos anteriores tracejados, o atual com o degradê e o "parcial").
function MesAMes({
    historico,
    campo,
    format,
}: {
    historico: MesHistorico[]
    campo: 'receita' | 'entradas' | 'ticket_medio'
    format: (v: number) => string
}) {
    const anos = seriesPorAno(historico, campo).slice(-CORES_ANO.length) // os anos mais recentes, uma cor cada
    const ultimo = anos.length - 1
    const parcial = ultimo >= 0 ? mesParcial(anos[ultimo].ano) : null
    return (
        <LineChart
            height={300}
            legend
            emphasizeData
            format={format}
            labels={MESES}
            partial={parcial !== null ? { series: ultimo, index: parcial } : undefined}
            tooltip={{ heading: 'Mês', title: mesNome }}
            series={anos.map((a, i) => ({
                label: String(a.ano),
                color: CORES_ANO[(anos.length - 1 - i) % CORES_ANO.length],
                values: a.valores,
                dashed: i < ultimo,
                area: i === ultimo,
            }))}
        />
    )
}

// "Reflexo do Mês": receita por mês (de ajuizamento ou do TED); clicar numa barra filtra pelo ano dela.
function ReflexoDoMes({ pontos, f }: { pontos: ReturnType<typeof barrasReflexo>; f?: Filtrar }) {
    if (pontos.length === 0) return <ChartEmpty>Sem TEDs no período.</ChartEmpty>
    return (
        <div className="fe-scroll">
            <div style={{ minWidth: Math.max(480, pontos.length * 84) }}>
                <ColumnChart
                    height={280}
                    className="col-accent"
                    format={semMoeda}
                    categories={pontos.map((p) => p.rotulo)}
                    series={[{ label: 'Receita', color: 'var(--chart-1)', values: pontos.map((p) => p.receita) }]}
                    onSelect={
                        f?.toggle &&
                        ((rotulo) => {
                            const p = pontos.find((x) => x.rotulo === rotulo)
                            if (p) f.toggle?.('ano_ajuizamento', p.ano)
                        })
                    }
                    selectLabel="Filtrar pelo ano de ajuizamento"
                />
            </div>
        </div>
    )
}

// Seletor de anos (ou meses) de uma seção ou modal: botões que ligam e desligam, e "Todos".
function Seletor({
    titulo,
    opcoes,
    marcados,
    onToggle,
    onLimpar,
}: {
    titulo: string
    opcoes: { value: string; label: string }[]
    marcados: string[]
    onToggle?: (v: string) => void
    onLimpar?: () => void
}) {
    return (
        <div className="fe-seletor" role="group" aria-label={titulo}>
            <span className="mz-eyebrow muted">{titulo}</span>
            <div className="fe-seletor-opcoes">
                <button type="button" className="fe-opcao" aria-pressed={marcados.length === 0} onClick={onLimpar}>
                    Todos
                </button>
                {opcoes.map((o) => (
                    <button
                        key={o.value}
                        type="button"
                        className="fe-opcao num"
                        aria-pressed={marcados.includes(o.value)}
                        onClick={() => onToggle?.(o.value)}
                    >
                        {o.label}
                    </button>
                ))}
            </div>
        </div>
    )
}

// --- 01 · Reflexo Financeiro -----------------------------------------------------------------------------------

function ReflexoSecao({
    r,
    f,
    meta,
    onPendentes,
}: {
    r: ReflexoFinanceiro
    f: Filtrar
    meta: FinanceiroEstrategicoResponse['meta']
    onPendentes: () => void
}) {
    const prot = r.valor_protocolado
    const med = r.mediana_tempo_ajuizamento_ted
    return (
        <DashSection
            index={1}
            eyebrow="Visão geral"
            title="Reflexo Financeiro"
            subtitle={`Entradas e receita do período (data do TED: ${periodo(r.periodo.inicio, r.periodo.fim)}), comparadas ao mesmo recorte do mês anterior.`}
        >
            <div className="grid grid-stat">
                <HeroStat
                    label="Total de entradas"
                    icon="inbox"
                    tone="accent"
                    value={<CountUp value={r.total_entradas.valor} format={fmt.int} />}
                    below={<DeltaPill value={r.total_entradas.comparativo} suffix={VS} plain />}
                    hint="Quantidade de TEDs recebidos no período (pela DATA DO TED)."
                    footer={<FootRow left="TEDs no período" right={<span className="num">{meta.unit}</span>} />}
                />
                <HeroStat
                    label="Valor total em receita"
                    icon="dollar"
                    tone="ok"
                    value={<CountUp value={r.valor_receita.valor} format={fmt.brl} />}
                    below={<DeltaPill value={r.valor_receita.comparativo} suffix={VS} plain />}
                    hint="Soma de HONO + SUCUMBÊNCIA dos TEDs do período."
                    footer={
                        <FootRow
                            left="Ticket médio"
                            right={<strong className="num">{fmt.brl(r.ticket_medio.valor)}</strong>}
                        />
                    }
                />
                <HeroStat
                    label="Valor protocolado no período"
                    icon="check-circle"
                    tone="info"
                    value={<CountUp value={prot.valor} format={fmt.brl} />}
                    below={<DeltaPill value={prot.comparativo} suffix={VS} plain />}
                    hint="Valor de causa dos processos distribuídos no período, direto do LexFlow (ANP conta o dano moral). Não vem da planilha: só muda com o período, não com Origem, Matéria e Ano de ajuizamento."
                    footer={
                        <FootRow
                            left="Processos distribuídos (LexFlow)"
                            right={<span className="num">{fmt.int(prot.quantidade)}</span>}
                        />
                    }
                />
                <HeroStat
                    label="Clientes pendentes"
                    icon="users"
                    tone="warn"
                    value={<CountUp value={r.clientes_pendentes.valor} format={fmt.brl} />}
                    below={
                        <StackedRate
                            text={fmt.int(r.clientes_pendentes.quantidade)}
                            caption="TEDs a repassar"
                            tone="warn"
                        />
                    }
                    hint="Repasse de cliente ainda não pago (STATUS pendente): valor sempre total, sem o período. Clique para abrir o controle de clientes."
                    footer={
                        <button type="button" className="linkbtn" onClick={onPendentes}>
                            Ver o controle de clientes <Icon name="chevrons" size={12} />
                        </button>
                    }
                />
            </div>
            <div className="grid grid-stat-3 grid-mini grid-mini-stack">
                <MiniStat
                    label="Ticket médio"
                    icon="receipt"
                    tone="ok"
                    value={fmt.brl(r.ticket_medio.valor)}
                    below={<DeltaPill value={r.ticket_medio.comparativo} suffix={VS} plain />}
                    hint="Valor total em receita dividido pelo total de entradas no período."
                />
                <MiniStat
                    label="Mediana de tempo (dias)"
                    icon="clock"
                    tone="info"
                    value={`${fmt.int(med.dias)} dias`}
                    below={<DeltaPill value={med.comparativo} betterWhenDown suffix={VS} plain />}
                    hint="Mediana de dias entre a DATA AJUIZAMENTO e a DATA DO TED dos TEDs do período."
                />
                <MiniStat
                    label="Mediana de tempo (meses)"
                    icon="calendar"
                    tone="info"
                    value={`${fmt.dec1(med.meses)} meses`}
                    below={<DeltaPill value={med.comparativo} betterWhenDown suffix={VS} plain />}
                    hint="A mesma mediana entre ajuizamento e TED, em meses (dias ÷ 30,44)."
                />
            </div>
            <div className="grid fe-tres">
                <ChartCard title="Receita × matérias" subtitle="8 maiores + Outras · clique para filtrar">
                    <PizzaMaterias itens={r.receita_por_materia} f={f} centro="R$ em receita" />
                </ChartCard>
                <ChartCard title="Valor da causa × valor da receita" subtitle="TEDs do período">
                    <CausaReceita causa={r.causa_x_receita.valor_causa} receita={r.causa_x_receita.valor_receita} />
                </ChartCard>
                <ChartCard title="Origem: condenação × acordo" subtitle="Pela quantidade de TEDs · clique para filtrar">
                    <PizzaOrigem origem={r.origem} f={f} />
                </ChartCard>
            </div>
            <div className="grid mz-duas">
                <ChartCard title="Receita por ano de ajuizamento" subtitle="Clique num ano para filtrar">
                    <PieChart
                        items={r.receita_por_ano_ajuizamento}
                        size={240}
                        sort={false}
                        format={compacto}
                        centerFormat={semMoeda}
                        centerLabel="R$ em receita"
                        selected={f.filters.ano_ajuizamento}
                        onSelect={f.toggle && ((name) => f.toggle?.('ano_ajuizamento', name))}
                        selectLabel="Filtrar pelo ano de ajuizamento"
                    />
                </ChartCard>
                <ChartCard title="Ticket médio por mês" tag={<Pill>Série anual</Pill>}>
                    <MesAMes historico={r.historico_mensal} campo="ticket_medio" format={compacto} />
                </ChartCard>
            </div>
            <div className="grid mz-duas">
                <ChartCard title="Receita por mês" tag={<Pill>Série anual</Pill>}>
                    <MesAMes historico={r.historico_mensal} campo="receita" format={compacto} />
                </ChartCard>
                <ChartCard title="Entradas no financeiro por mês" tag={<Pill>Série anual</Pill>}>
                    <MesAMes historico={r.historico_mensal} campo="entradas" format={fmt.int} />
                </ChartCard>
            </div>
            <ChartCard
                title="Reflexo do mês"
                subtitle="Receita dos TEDs do período pelo mês de ajuizamento do processo · clique para filtrar pelo ano"
            >
                <ReflexoDoMes pontos={barrasReflexo(r.reflexo_do_mes)} f={f} />
            </ChartCard>
        </DashSection>
    )
}

// --- 02 · Reflexo de Ajuizamento -------------------------------------------------------------------------------

function AjuizamentoSecao({ r, f }: { r: ReflexoFinanceiro; f: Filtrar }) {
    const a = r.reflexo_ajuizamento
    const med = a.mediana_tempo_ajuizamento_ted
    return (
        <DashSection
            index={2}
            eyebrow="Ajuizamento"
            title="Reflexo de Ajuizamento"
            subtitle="Os processos ajuizados no período (DATA AJUIZAMENTO) e a receita que já deram, em qualquer data do TED."
        >
            <div className="grid grid-stat-3 grid-mini grid-mini-stack">
                <MiniStat
                    label="% julgados procedentes"
                    icon="percent"
                    tone="ok"
                    value={pct2(a.percentual_procedentes.valor)}
                    below={<DeltaPill value={a.percentual_procedentes.comparativo} suffix={VS} plain />}
                    hint="TEDs dos processos ajuizados no período ÷ processos protocolados no período (LexFlow)."
                />
                <MiniStat
                    label="Valor protocolado"
                    icon="check-circle"
                    tone="info"
                    value={fmt.brl(r.valor_protocolado.valor)}
                    below={<DeltaPill value={r.valor_protocolado.comparativo} suffix={VS} plain />}
                    hint="Valor de causa dos processos distribuídos no período (LexFlow)."
                />
                <MiniStat
                    label="Receita"
                    icon="dollar"
                    tone="ok"
                    value={fmt.brl(a.valor_receita.valor)}
                    below={<DeltaPill value={a.valor_receita.comparativo} suffix={VS} plain />}
                    hint="Receita (HONO + SUCUMBÊNCIA) dos processos ajuizados no período."
                />
                <MiniStat
                    label="Ticket médio"
                    icon="receipt"
                    tone="ok"
                    value={fmt.brl(a.ticket_medio.valor)}
                    below={<DeltaPill value={a.ticket_medio.comparativo} suffix={VS} plain />}
                    hint="Receita dividida pelos TEDs dos processos ajuizados no período."
                />
                <MiniStat
                    label="Mediana de tempo (dias)"
                    icon="clock"
                    tone="info"
                    value={`${fmt.int(med.dias)} dias`}
                    below={<DeltaPill value={med.comparativo} betterWhenDown suffix={VS} plain />}
                    hint="Mediana de dias entre o ajuizamento e o TED, nos processos ajuizados no período."
                />
                <MiniStat
                    label="Mediana de tempo (meses)"
                    icon="calendar"
                    tone="info"
                    value={`${fmt.dec1(med.meses)} meses`}
                    below={<DeltaPill value={med.comparativo} betterWhenDown suffix={VS} plain />}
                    hint="A mesma mediana, em meses (dias ÷ 30,44)."
                />
            </div>
            <div className="grid fe-tres">
                <ChartCard title="Protocolados × matérias" subtitle="Valor de causa no LexFlow">
                    <PieChart
                        items={r.valor_protocolado.por_materia}
                        size={240}
                        format={compacto}
                        centerFormat={semMoeda}
                        centerLabel="R$ protocolado"
                    />
                </ChartCard>
                <ChartCard title="Origem: condenação × acordo" subtitle="Processos ajuizados no período">
                    <PizzaOrigem origem={a.origem} f={f} />
                </ChartCard>
                <ChartCard title="Receita × matérias" subtitle="Processos ajuizados no período · clique para filtrar">
                    <PizzaMaterias itens={a.receita_por_materia} f={f} centro="R$ em receita" />
                </ChartCard>
            </div>
            <div className="grid fe-pa">
                <ChartCard title="Percentual anual" subtitle="Receita pelo ano do TED">
                    <PieChart
                        items={a.receita_por_ano_ted}
                        size={240}
                        sort={false}
                        format={compacto}
                        centerFormat={semMoeda}
                        centerLabel="R$ em receita"
                    />
                </ChartCard>
                <ChartCard
                    title="Reflexo do mês"
                    subtitle="Receita dos processos ajuizados no período, pelo mês em que o TED caiu"
                >
                    <ReflexoDoMes pontos={barrasReflexo(a.reflexo_do_mes_ted)} />
                </ChartCard>
            </div>
        </DashSection>
    )
}

// --- 03 · Conversão --------------------------------------------------------------------------------------------

type Marcar = ((key: keyof DashboardFilters, value: string) => void) | undefined
type Limpar = ((key: keyof DashboardFilters) => void) | undefined

function ConversaoSecao({
    c,
    filters,
    marcar,
    limpar,
}: {
    c: Conversao
    filters: DashboardFilters
    marcar: Marcar
    limpar: Limpar
}) {
    const anos = (xs: string[]) => xs.map((value) => ({ value, label: value }))
    return (
        <DashSection
            index={3}
            eyebrow="Conversão"
            title="Conversão"
            subtitle="Quanto do valor de causa ajuizado virou receita: escolha os anos de ajuizamento e do financeiro (TED)."
        >
            <div className="card fe-seletores">
                <Seletor
                    titulo="Data ajuizamento"
                    opcoes={anos(c.anos_ajuizamento_opcoes)}
                    marcados={filters.conv_ano_ajuizamento ?? []}
                    onToggle={marcar && ((v) => marcar('conv_ano_ajuizamento', v))}
                    onLimpar={limpar && (() => limpar('conv_ano_ajuizamento'))}
                />
                <Seletor
                    titulo="Data financeiro"
                    opcoes={anos(c.anos_financeiro_opcoes)}
                    marcados={filters.conv_ano_financeiro ?? []}
                    onToggle={marcar && ((v) => marcar('conv_ano_financeiro', v))}
                    onLimpar={limpar && (() => limpar('conv_ano_financeiro'))}
                />
            </div>
            <div className="grid grid-stat-3">
                <HeroStat
                    label="Valor receita"
                    icon="dollar"
                    tone="ok"
                    value={<CountUp value={c.receita} format={fmt.brl} />}
                    hint="Receita (HONO + SUCUMBÊNCIA) das linhas da planilha nos anos de ajuizamento e do financeiro marcados."
                    footer={<FootRow left="TEDs" right={<span className="num">{fmt.int(c.quantidade)}</span>} />}
                />
                <HeroStat
                    label="Valor de causa ajuizado"
                    icon="check-circle"
                    tone="info"
                    value={<CountUp value={c.valor_causa_ajuizado.valor} format={fmt.brl} />}
                    hint="Valor de causa ajuizado no LexFlow nos anos de ajuizamento marcados (ano da distribuição)."
                    footer={
                        <FootRow
                            left="Processos (LexFlow)"
                            right={<span className="num">{fmt.int(c.valor_causa_ajuizado.quantidade)}</span>}
                        />
                    }
                />
                <HeroStat
                    label="% conversão"
                    icon="percent"
                    tone="accent"
                    value={pct2(c.percentual_conversao)}
                    hint="Valor receita ÷ valor de causa ajuizado × 100."
                    footer={<FootRow left="Receita sobre o valor ajuizado" />}
                />
            </div>
            <div className="grid fe-tres">
                <ChartCard title="Receita × matérias" subtitle="8 maiores + Outras">
                    <PieChart
                        items={c.receita_por_materia}
                        size={240}
                        format={compacto}
                        centerFormat={semMoeda}
                        centerLabel="R$ em receita"
                    />
                </ChartCard>
                <ChartCard title="Valor de causa × receita">
                    <CausaReceita causa={c.valor_causa_ajuizado.valor} receita={c.receita} />
                </ChartCard>
                <ChartCard title="Percentual anual" subtitle="Pelo ano de ajuizamento · clique para marcar o ano">
                    <PieChart
                        items={c.receita_por_ano_ajuizamento}
                        size={240}
                        sort={false}
                        format={compacto}
                        centerFormat={semMoeda}
                        centerLabel="R$ em receita"
                        selected={filters.conv_ano_ajuizamento}
                        onSelect={marcar && ((name) => marcar('conv_ano_ajuizamento', name))}
                        selectLabel="Marcar o ano de ajuizamento"
                    />
                </ChartCard>
            </div>
        </DashSection>
    )
}

// --- 04 · Evolução ---------------------------------------------------------------------------------------------

function EvolucaoCard({ evolucao }: { evolucao: ReflexoFinanceiro['evolucao_anual'] }) {
    if (evolucao.length === 0) return <ChartEmpty />
    return (
        <ChartCard
            title="Receita por ano"
            subtitle={`Pelo ano do TED, a partir de ${evolucao[0].ano}`}
            footer={
                <div className="fe-crescimentos">
                    {evolucao.map((e) => (
                        <span key={e.ano} className="small">
                            <span className="muted num">{e.ano}</span>{' '}
                            {e.crescimento_pct === null ? (
                                <span className="muted">—</span>
                            ) : (
                                <DeltaPill value={e.crescimento_pct} suffix=" vs ano anterior" />
                            )}
                        </span>
                    ))}
                </div>
            }
        >
            <ColumnChart
                height={300}
                className="col-accent"
                format={compacto}
                categories={evolucao.map((e) => String(e.ano))}
                series={[{ label: 'Receita', color: 'var(--chart-1)', values: evolucao.map((e) => e.receita) }]}
            />
        </ChartCard>
    )
}

// --- 05 · Previsão ---------------------------------------------------------------------------------------------

const ROTULO_TOM: Record<string, Tone> = { Base: 'accent', Otimista: 'ok', Conservador: 'warn' }

function PrevisaoSecao({ p }: { p: Previsao }) {
    const col = colunasPrevisao(p)
    const base = p.cenarios.find((c) => c.id === p.cenario_base)
    return (
        <DashSection
            index={5}
            eyebrow="Previsão"
            title={`Previsão de receita ${p.ano_previsto}`}
            subtitle="Quatro cenários simples e explicáveis para a receita do próximo ano, com a base inteira (sem os filtros da página)."
        >
            {p.aviso_historico && (
                <div className="card fe-aviso small">
                    <Icon name="info" size={16} /> {p.aviso_historico}
                </div>
            )}
            <div className="grid grid-stat">
                <MiniStat
                    label={`Receita ${p.ano_atual} até hoje`}
                    icon="dollar"
                    tone="ok"
                    value={fmt.brl(p.ano_atual_ate_hoje)}
                    hint={`Receita real que já entrou em ${p.ano_atual}, pela data do TED.`}
                />
                <MiniStat
                    label={`${p.ano_atual} fechado (estimado)`}
                    icon="calendar"
                    tone="info"
                    value={fmt.brl(p.ano_atual_estimado)}
                    hint={`Até hoje + o que costuma entrar até o fim do ano (${pct2(p.fracao_restante_pct)} da receita anual em ${p.anos_referencia_fracao.join(' e ')}).`}
                />
                <MiniStat
                    label={`${p.ano_previsto} — cenário base`}
                    icon="trend-up"
                    tone="accent"
                    value={fmt.brl(base?.valor ?? 0)}
                    hint={`Cenário ${base?.nome ?? 'base'}: o mais equilibrado dos cenários.`}
                />
                <MiniStat
                    label={`Faixa ${p.ano_previsto}`}
                    icon="target"
                    tone="neutral"
                    value={p.faixa ? `${compacto(p.faixa.minimo)} – ${compacto(p.faixa.maximo)}` : '—'}
                    hint="Do menor ao maior cenário: o valor real deve ficar nessa faixa se nada mudar muito."
                />
            </div>
            <ChartCard
                title="Receita anual — real e previsão"
                subtitle={`Real · o que ainda deve entrar em ${p.ano_atual} · previsão ${p.ano_previsto} (cenário base e até o maior cenário)`}
            >
                <ColumnChart
                    height={320}
                    format={compacto}
                    categories={col.anos}
                    series={[
                        { label: 'Receita real', color: 'var(--chart-1)', values: col.real },
                        {
                            label: 'Ainda deve entrar (estimado)',
                            color: 'var(--chart-1-soft, #f6c48a)',
                            values: col.restante,
                        },
                        { label: 'Previsão (cenário base)', color: 'var(--chart-3)', values: col.previsto },
                        { label: 'A mais no maior cenário', color: 'var(--chart-3-soft, #bcd3f5)', values: col.faixa },
                    ]}
                    tooltip
                />
            </ChartCard>
            <div className="grid grid-stat">
                {[...p.cenarios]
                    .sort((x, y) => x.valor - y.valor)
                    .map((c) => (
                        <CenarioCard key={c.id} c={c} anoAtual={p.ano_atual} />
                    ))}
            </div>
            {p.conferencia_safra && (
                <p className="small muted">
                    Conferência: o cenário por safra previa {fmt.brl(p.conferencia_safra.previsto)} para{' '}
                    {p.conferencia_safra.ano}; entrou {fmt.brl(p.conferencia_safra.real)} (erro de{' '}
                    {fmt.dec1(p.conferencia_safra.erro_pct)}%).
                </p>
            )}
        </DashSection>
    )
}

function CenarioCard({ c, anoAtual }: { c: Cenario; anoAtual: number }) {
    const base = c.rotulo === 'Base'
    return (
        <section className={`card fe-cenario${base ? ' base' : ''}`}>
            <div className="mz-row">
                <strong>{c.nome}</strong>
                <Pill tone={ROTULO_TOM[c.rotulo] ?? 'neutral'}>{c.rotulo}</Pill>
            </div>
            <strong className="mz-mid num">{fmt.brl(c.valor)}</strong>
            {c.crescimento_pct !== null && (
                <span className={`small num tone-text-${c.crescimento_pct >= 0 ? 'ok' : 'danger'}`}>
                    {c.crescimento_pct >= 0 ? '+' : ''}
                    {fmt.dec1(c.crescimento_pct)}% sobre {anoAtual} estimado
                </span>
            )}
            <p className="small">{c.premissa}</p>
            <p className="small muted">{c.explicacao}</p>
            <p className="small muted">
                <strong>Quando faz sentido:</strong> {c.quando_faz_sentido}
            </p>
            <p className="small muted num">{c.detalhe}</p>
        </section>
    )
}

// --- Modal · Controle de Clientes ------------------------------------------------------------------------------

function PendentesModal({
    c,
    filters,
    marcar,
    limpar,
    onClose,
}: {
    c: ClientesPendentes
    filters: DashboardFilters
    marcar: Marcar
    limpar: Limpar
    onClose: () => void
}) {
    const caixa = (rotulo: string, valor: ReactNode, nota?: string) => (
        <div className="mz-caixa">
            <span className="muted small">{rotulo}</span>
            <strong className="mz-mid num">{valor}</strong>
            {nota && <span className="small muted">{nota}</span>}
        </div>
    )
    return (
        <Modal
            title="Controle de clientes"
            subtitle="Repasses de cliente ainda não pagos (STATUS pendente), por ano e mês da DATA DO TED."
            className="mz-modal"
            onClose={onClose}
        >
            <div className="mz-modal-body">
                <div className="card fe-seletores">
                    <Seletor
                        titulo="Ano do TED"
                        opcoes={c.anos_opcoes.map((value) => ({ value, label: value }))}
                        marcados={filters.pend_ano ?? []}
                        onToggle={marcar && ((v) => marcar('pend_ano', v))}
                        onLimpar={limpar && (() => limpar('pend_ano'))}
                    />
                    <Seletor
                        titulo="Mês do TED"
                        opcoes={OPCOES_MES}
                        marcados={filters.pend_mes ?? []}
                        onToggle={marcar && ((v) => marcar('pend_mes', v))}
                        onLimpar={limpar && (() => limpar('pend_mes'))}
                    />
                </div>
                <div className="mz-caixas">
                    {caixa('Valor fixo de clientes a receber', fmt.brl(c.valor_fixo), 'Total, sem ano e mês')}
                    {caixa(
                        'Quantidade de clientes a receber',
                        fmt.int(c.quantidade_clientes),
                        `${fmt.int(c.quantidade)} TEDs`,
                    )}
                    {caixa(
                        'Valor variável de clientes a receber',
                        fmt.brl(c.valor_variavel),
                        'Com o ano e o mês escolhidos',
                    )}
                </div>
                <div className="mz-duas">
                    <div className="mz-caixa">
                        <strong>Clientes por status</strong>
                        <PieChart
                            items={c.por_status}
                            size={220}
                            format={compacto}
                            centerFormat={semMoeda}
                            centerLabel="R$ a repassar"
                        />
                    </div>
                    <div className="mz-caixa">
                        <strong>Clientes por valor</strong>
                        <div className="comissao-scroll">
                            <BarList items={c.por_cliente} format={fmt.brl} ranked valueOutside wrapNames />
                        </div>
                    </div>
                </div>
            </div>
        </Modal>
    )
}
