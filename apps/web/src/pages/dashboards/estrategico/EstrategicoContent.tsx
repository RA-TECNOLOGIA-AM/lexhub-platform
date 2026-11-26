import { useState, type ReactNode } from 'react'
import { ChartCard, ChartEmpty } from '../../../components/charts/ChartCard.tsx'
import { LineChart } from '../../../components/charts/LineChart.tsx'
import { DashSection } from '../../../components/dashboard/DashSection.tsx'
import { DeltaPill, FootRow, HeroStat } from '../../../components/dashboard/StatCard.tsx'
import type { Tone } from '../../../components/dashboard/tone.ts'
import { CountUp } from '../../../components/ui/CountUp.tsx'
import { Icon, type IconName } from '../../../components/ui/Icon.tsx'
import { toggleFilter } from '../../../lib/filters.ts'
import { fmt } from '../../../lib/format.ts'
import type { Point } from '../../../types/index.ts'
import { MesAMes } from '../execucao/partes.tsx'
import { diaCurto, diaLongo } from '../setor/datas.ts'
import type { ContentProps } from '../types.ts'
import { JuridicoSecao } from './JuridicoSecao.tsx'
import {
    comarcasDisponiveis,
    comparativo,
    diasDoMes,
    divideSeries,
    rotuloMes,
    type Comercial,
    type EstrategicoResponse,
    type Protocolo,
} from './estrategico.ts'

const VS = ' vs período anterior'

// Estratégico: as 4 seções da página da v1 (Comercial, Protocolo, Jurídico com período e Jurídico fixo) no layout
// da V2, com os números da unidade. Os gráficos mês a mês abrem os dias do mês ao clicar; a comarca do Jurídico
// filtra as seções 03 e 04 (de novo, para tirar).
export function EstrategicoContent({ data, filters = {}, onFiltersChange }: ContentProps<EstrategicoResponse>) {
    const comercial = data.comercial
    const protocolo = data.protocolo
    if (!comercial || !protocolo) {
        return (
            <ChartCard title="Estratégico">
                <ChartEmpty>Sem dados para esta unidade.</ChartEmpty>
            </ChartCard>
        )
    }
    const alternarComarca =
        onFiltersChange && ((c: string) => onFiltersChange(toggleFilter(filters, 'comarca_estrategico', c)))
    const fontes = data.fontes
    const comarcasBase = comarcasDisponiveis(data)
    const aviso =
        fontes && (!fontes.legado || !fontes.lexpre)
            ? `Esta unidade não tem o ${!fontes.legado ? 'banco legado' : 'LexPre'} ligado: os números do Comercial e do Protocolo vêm só do ${!fontes.legado ? 'LexPre' : 'banco legado'}.`
            : null

    return (
        <div className="dsecs">
            <SecaoComercial c={comercial} aviso={aviso} />
            <SecaoProtocolo p={protocolo} />
            <JuridicoSecao
                index={3}
                modo="periodo"
                j={data.juridico_periodo}
                unidade={data.unidade}
                comarcasBase={comarcasBase}
                filters={filters}
                onComarca={alternarComarca}
            />
            <JuridicoSecao
                index={4}
                modo="fixo"
                j={data.juridico_fixo}
                unidade={data.unidade}
                comarcasBase={comarcasBase}
                filters={filters}
                onComarca={alternarComarca}
            />
        </div>
    )
}

const valor = (v: number) => <CountUp value={v} format={fmt.int} />
const reais = (v: number) => <CountUp value={v} format={fmt.brl} />

function Kpi({
    label,
    icon,
    tone,
    value,
    atual,
    anterior,
    format = fmt.int,
    hint,
}: {
    label: string
    icon: IconName
    tone: Tone
    value: ReactNode
    atual?: number
    anterior?: number
    format?: (v: number) => string
    hint: string
}) {
    const temComparativo = atual !== undefined && anterior !== undefined
    return (
        <HeroStat
            label={label}
            icon={icon}
            tone={tone}
            value={value}
            hint={hint}
            below={temComparativo ? <DeltaPill value={comparativo(atual, anterior)} suffix={VS} plain /> : undefined}
            footer={
                temComparativo ? (
                    <FootRow
                        left="Período anterior"
                        right={<strong className="num">{anterior ? format(anterior) : '—'}</strong>}
                    />
                ) : undefined
            }
        />
    )
}

function SecaoComercial({ c, aviso }: { c: Comercial; aviso: string | null }) {
    return (
        <DashSection
            index={1}
            eyebrow="Comercial"
            title="Resultados comerciais"
            subtitle="Contratos e ações fechados no período (banco legado + LexPre)."
        >
            {aviso && (
                <p className="es-aviso">
                    <Icon name="info" size={15} />
                    {aviso}
                </p>
            )}
            <div className="grid es-dois">
                <Kpi
                    label="Contratos fechados"
                    icon="briefcase"
                    tone="accent"
                    value={valor(c.contratos)}
                    atual={c.contratos}
                    anterior={c.contratos_anterior}
                    hint="Contratos fechados no período, somando o Comercial do banco legado e o do LexPre. O comparativo usa o período anterior de mesmo tamanho."
                />
                <Kpi
                    label="Ações fechadas"
                    icon="scale"
                    tone="info"
                    value={valor(c.acoes)}
                    atual={c.acoes}
                    anterior={c.acoes_anterior}
                    hint="Ações (processos) fechadas pela equipe comercial no período, banco legado + LexPre."
                />
            </div>
            <div className="grid dist-grid ex-mt">
                <MesDia titulo="Contratos" mensal={c.contratos_por_mes} diario={c.contratos_por_dia} />
                <MesDia titulo="Ações" mensal={c.acoes_por_mes} diario={c.acoes_por_dia} />
            </div>
        </DashSection>
    )
}

function SecaoProtocolo({ p }: { p: Protocolo }) {
    const ticketMes = divideSeries(p.valor_causa_por_mes, p.protocolados_por_mes)
    const ticketDia = divideSeries(p.valor_causa_por_dia, p.protocolados_por_dia)
    return (
        <DashSection
            index={2}
            eyebrow="Protocolo"
            title="Produção e valor de causa"
            subtitle="Represados antes do protocolo (agora) e o que foi protocolado no período."
        >
            <div className="grid grid-stat">
                <Kpi
                    label="Represados no pré-protocolo"
                    icon="inbox"
                    tone="warn"
                    value={valor(p.represados)}
                    hint="Estoque de agora antes do protocolo: não organizados, pendências não resolvidas, não protocolados e não peticionados (no LA: protocolos represados, não confeccionados, pendências e não organizados), banco legado + LexPre."
                />
                <Kpi
                    label="Processos protocolados"
                    icon="check-circle"
                    tone="ok"
                    value={valor(p.protocolados)}
                    atual={p.protocolados}
                    anterior={p.protocolados_anterior}
                    hint="Protocolos resolvidos no período (dashboard de Protocolo), banco legado + LexPre."
                />
                <Kpi
                    label="Valor de causa gerado"
                    icon="dollar"
                    tone="accent"
                    value={reais(p.valor_causa)}
                    atual={p.valor_causa}
                    anterior={p.valor_causa_anterior}
                    format={fmt.brl}
                    hint="Soma do valor de causa dos processos protocolados no período."
                />
                <Kpi
                    label="Ticket médio protocolado"
                    icon="receipt"
                    tone="info"
                    value={reais(p.ticket_medio)}
                    atual={p.ticket_medio}
                    anterior={p.ticket_medio_anterior}
                    format={fmt.brl}
                    hint="Valor de causa médio por processo protocolado no período."
                />
            </div>
            <div className="grid dist-grid ex-mt">
                <MesDia titulo="Protocolados" mensal={p.protocolados_por_mes} diario={p.protocolados_por_dia} />
                <MesDia
                    titulo="Valor de causa protocolado"
                    mensal={p.valor_causa_por_mes}
                    diario={p.valor_causa_por_dia}
                    format={fmt.brlShort}
                />
            </div>
            <div className="ex-mt">
                <MesDia titulo="Ticket médio protocolado" mensal={ticketMes} diario={ticketDia} format={fmt.brlShort} />
            </div>
        </DashSection>
    )
}

// Um "mês a mês" (todo o histórico, um ano por linha) que abre os dias do mês clicado, como os gráficos da v1.
function MesDia({
    titulo,
    mensal,
    diario,
    format = fmt.int,
}: {
    titulo: string
    mensal: Point[]
    diario: Point[]
    format?: (v: number) => string
}) {
    const [mes, setMes] = useState('')
    const dias = mes ? diasDoMes(diario, mes) : []
    return (
        <ChartCard
            title={mes ? `${titulo} por dia` : `${titulo} por mês`}
            subtitle={mes ? rotuloMes(mes) : 'Histórico todo, sem o período · clique num mês para ver os dias'}
            action={
                mes && (
                    <button type="button" className="btn" onClick={() => setMes('')}>
                        <Icon name="undo" size={15} />
                        Mês a mês
                    </button>
                )
            }
        >
            {mensal.length === 0 ? (
                <ChartEmpty>Sem dados no histórico.</ChartEmpty>
            ) : (
                <div key={mes || 'meses'} className="ex-drill">
                    {mes ? (
                        dias.length === 0 ? (
                            <ChartEmpty>Sem lançamentos neste mês.</ChartEmpty>
                        ) : (
                            <LineChart
                                height={280}
                                area
                                format={format}
                                labels={dias.map((d) => diaCurto(d.name))}
                                tooltip={{ heading: 'Dia', title: (i) => diaLongo(dias[i]?.name) }}
                                series={[{ label: titulo, color: 'var(--chart-1)', values: dias.map((d) => d.value) }]}
                            />
                        )
                    ) : (
                        <MesAMes
                            pontos={mensal}
                            height={280}
                            format={format}
                            onSelectMes={(ano, m) => setMes(`${ano}-${String(m).padStart(2, '0')}`)}
                        />
                    )}
                </div>
            )}
        </ChartCard>
    )
}
