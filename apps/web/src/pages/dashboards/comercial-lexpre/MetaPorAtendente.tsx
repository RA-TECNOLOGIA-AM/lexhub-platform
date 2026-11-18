import { useState, type CSSProperties } from 'react'
import { useParams } from 'react-router'
import { ChartEmpty } from '../../../components/charts/ChartCard.tsx'
import { InfoTip, Pill } from '../../../components/dashboard/StatCard.tsx'
import { CountUp } from '../../../components/ui/CountUp.tsx'
import { Icon } from '../../../components/ui/Icon.tsx'
import { useAsync } from '../../../hooks/useAsync.ts'
import { useDebouncedValue } from '../../../hooks/useDebouncedValue.ts'
import { FETCH_DELAY_MS } from '../../../lib/dashboardQuery.ts'
import { fmt } from '../../../lib/format.ts'
import { dataClient } from '../../../services/client.ts'
import type { DashboardFilters } from '../../../types/index.ts'
import {
    PERIODOS_META,
    datasDoPeriodo,
    faixaAtingimento,
    linhasMeta,
    metaDoPeriodo,
    somarPorNome,
    trimestreDe,
    type PeriodoMeta,
} from './comercial.ts'
import type { ComercialLexpreResponse } from './types.ts'

type MetaPorAtendenteProps = {
    referencia: string // fim do período da página (AAAA-MM-DD): define o ano e o trimestre inicial
    filters: DashboardFilters
}

// Módulo: "Meta por Atendente" da v1. Escolhe trimestre ou semestre do ano; busca o valor de causa protocolado
// de cada atendente nesse período (com os filtros da página) e compara com a meta (R$ 12 mi/trimestre).
export function MetaPorAtendente({ referencia, filters }: MetaPorAtendenteProps) {
    const { org = '', unit = '' } = useParams()
    const [periodo, setPeriodo] = useState<PeriodoMeta>(() => trimestreDe(referencia))
    const ano = Number(referencia.slice(0, 4))
    const { from, to } = datasDoPeriodo(periodo, ano)
    const meta = metaDoPeriodo(periodo)
    // Os filtros da página depois de pararem de mudar (como a busca da página: um clique não é uma busca).
    // Em texto: o objeto de filtros é novo a cada render da página, o texto só muda quando eles mudam.
    const chave = useDebouncedValue(JSON.stringify(filters), FETCH_DELAY_MS)
    const { data, error, loading } = useAsync(
        (signal) =>
            dataClient.getDashboardData<ComercialLexpreResponse>('comercial-lexpre', {
                org,
                unit,
                from,
                to,
                filters: JSON.parse(chave) as DashboardFilters,
                signal,
            }),
        [org, unit, from, to, chave],
    )
    // Como na v1: LexPre + banco legado, pelo primeiro nome.
    const linhas = linhasMeta(
        somarPorNome(
            data?.stats.valor_causa_protocolado_por_atendente_periodo ?? {},
            data?.valor_causa_protocolado_por_atendente_legado,
        ),
        meta,
    )

    return (
        <div className="meta-card">
            <div className="meta-card-head">
                <span className="meta-card-title">
                    <Icon name="target" size={18} />
                    Meta por Atendente
                    <InfoTip text="Valor de causa protocolado no LexPre por atendente no período escolhido, contra a meta de cada um (R$ 12 mi por trimestre, R$ 24 mi por semestre, como na v1). Soma o LexPre com o banco legado (antes da migração), pelo primeiro nome, como a v1." />
                </span>
                <span className="meta-card-tools">
                    <label className="field-select">
                        <span className="sr-only">Período da meta</span>
                        <select value={periodo} onChange={(e) => setPeriodo(e.target.value as PeriodoMeta)}>
                            {PERIODOS_META.map((p) => (
                                <option key={p.value} value={p.value}>
                                    {p.label} {ano}
                                </option>
                            ))}
                        </select>
                    </label>
                    <span className="meta-chip num">
                        Meta do período: <strong>{fmt.brlShort(meta)}</strong>
                    </span>
                </span>
            </div>
            {error ? (
                <ChartEmpty>Não foi possível carregar o período.</ChartEmpty>
            ) : !data && loading ? (
                <ChartEmpty>Carregando o período…</ChartEmpty>
            ) : linhas.length === 0 ? (
                <ChartEmpty>Nenhum protocolo no período.</ChartEmpty>
            ) : (
                <ol className="meta-list">
                    {linhas.map((l, i) => {
                        const tone = faixaAtingimento(l.pct)
                        return (
                            <li key={l.name} className="meta-row">
                                <span className={`meta-rank num${i < 3 ? ' top' : ''}`}>{i + 1}</span>
                                <span className="meta-row-body">
                                    <span className="meta-row-head">
                                        <span className="fstack">
                                            <strong>{l.name}</strong>
                                            <span className="small muted">
                                                Protocolado:{' '}
                                                <strong className="num">
                                                    <CountUp value={l.protocolado} format={fmt.brl} />
                                                </strong>
                                                <span aria-hidden="true"> · </span>
                                                Faltam: <strong className="num">{fmt.brl(l.faltam)}</strong>
                                            </span>
                                        </span>
                                        <Pill tone={tone}>{fmt.int(Math.floor(l.pct))}%</Pill>
                                    </span>
                                    <span className="meta-track" aria-hidden="true">
                                        <span
                                            className={`meta-bar tone-${tone}`}
                                            style={{ '--w': `${Math.min(100, l.pct)}%` } as CSSProperties}
                                        />
                                    </span>
                                </span>
                            </li>
                        )
                    })}
                </ol>
            )}
        </div>
    )
}
