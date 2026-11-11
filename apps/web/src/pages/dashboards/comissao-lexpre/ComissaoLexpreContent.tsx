import { Delta } from '../../../components/dashboard/Delta.tsx'
import { Kpi } from '../../../components/dashboard/Kpi.tsx'
import { KpiSection } from '../../../components/dashboard/KpiSection.tsx'
import { fmt, show } from '../../../lib/format.ts'
import type { ComissaoLexpreResponse } from './types.ts'

// Fator multiplicador é um número (ex.: 4), não dinheiro: mostra como "4×".
const nfFator = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 2 })
const fator = (v: number) => `${nfFator.format(v)}×`

// Desconto aparece negativo, como na v1 ("- R$ 120,00"); zero fica "R$ 0,00".
const desconto = (v: number) => (v > 0 ? `- ${fmt.brl(v)}` : fmt.brl(v))

// Só o que é da Comissão: os KPIs e a tabela. Carregar, erros e cabeçalho ficam no DashboardView.
export function ComissaoLexpreContent({ data }: { data: ComissaoLexpreResponse }) {
    const s = data.stats
    const atendentes = s.comissionamento_por_atendente ?? []

    return (
        <>
            <KpiSection
                id="calculo"
                title="Cálculo da comissão"
                subtitle="Comissão base × fator multiplicador = comissão com FM; menos o desconto de cancelamentos = comissão líquida."
            >
                <Kpi
                    label="Comissão Base"
                    value={show(s.comissao_base, fmt.brl)}
                    note="Soma do valor de cada rubrica × ações fechadas"
                />
                <Kpi
                    label="Valor FM"
                    value={show(s.fator_multiplicador, fator)}
                    note="Conta a partir de R$ 2,5 mi protocolados; trava em 4 ao atingir R$ 4 mi"
                />
                <Kpi
                    label="Comissão com FM (bruta)"
                    value={show(s.comissao_com_fm, fmt.brl)}
                    note="Comissão base × fator multiplicador"
                />
                <Kpi
                    label="Desconto por cancelamento"
                    value={show(s.desconto_cancelamentos, desconto)}
                    note="Comissionadas antes e canceladas no período (valor cheio, sem FM)"
                />
                <Kpi
                    label="Comissão com FM"
                    value={show(s.comissao_com_fm_liquida, fmt.brl)}
                    note="Líquida: o pool repartido entre AM/PA e PB"
                />
            </KpiSection>

            <KpiSection
                id="proporcionais"
                title="Divisão por estado"
                subtitle="Como a comissão líquida se reparte: a PB pela fatia do valor de causa protocolado lá; AM/PA fica com o restante."
            >
                <Kpi
                    label="Proporcional AM/PA"
                    value={show(s.proporcional_am_pa, fmt.brl)}
                    note="Valor da comissão proporcional aos estados AM e PA"
                />
                <Kpi
                    label="Proporcional PB"
                    value={show(s.proporcional_pb, fmt.brl)}
                    note="Valor da comissão proporcional ao estado da PB"
                />
            </KpiSection>

            <KpiSection id="base" title="Base do período" subtitle="Os números do Comercial de onde a comissão sai.">
                <Kpi
                    label="Ações Fechadas"
                    value={show(s.acoes_fechadas?.total, fmt.int)}
                    note={`${show(s.rubricas_reunidas_fechadas, fmt.int)} rubricas reunidas`}
                />
                <Kpi
                    label="Protocolados"
                    value={show(s.protocolados?.total, fmt.int)}
                    note={<Delta value={s.protocolados?.comparativo ?? null} />}
                />
                <Kpi
                    label="Valor de causa protocolado"
                    value={show(s.valor_causa_protocolado?.total, fmt.brl)}
                    note={<Delta value={s.valor_causa_protocolado?.comparativo ?? null} />}
                />
                <Kpi
                    label="Cancelados"
                    value={show(s.demandas_canceladas?.total, fmt.int)}
                    note={<Delta value={s.demandas_canceladas?.comparativo ?? null} betterWhenDown />}
                />
            </KpiSection>

            <section className="card" style={{ overflow: 'hidden' }} aria-labelledby="por-atendente">
                <div className="card-head" style={{ paddingBottom: 12 }}>
                    <h2 className="h2" id="por-atendente">
                        Comissão por atendente
                    </h2>
                    <p className="muted small">Mesmo cálculo, linha a linha (é o conteúdo do PDF de comissão da v1).</p>
                </div>
                {atendentes.length === 0 ? (
                    <p className="card-pad muted small">Sem dados de comissão para o período selecionado.</p>
                ) : (
                    <div className="tblwrap">
                        <table className="tbl" style={{ minWidth: 760 }}>
                            <thead>
                                <tr>
                                    <th>Atendente</th>
                                    <th className="num">Ações</th>
                                    <th className="num">Comissão base</th>
                                    <th className="num">Comissão com FM</th>
                                    <th className="num">Desconto de cancelamentos</th>
                                    <th className="num">Proporcional AM/PA</th>
                                    <th className="num">Proporcional PB</th>
                                </tr>
                            </thead>
                            <tbody>
                                {atendentes.map((a) => (
                                    <tr key={a.atendente}>
                                        <td>{a.atendente}</td>
                                        <td className="num">{show(a.acoes, fmt.int)}</td>
                                        <td className="num">{show(a.comissao_base, fmt.brl)}</td>
                                        <td className="num">{show(a.comissao_com_fm, fmt.brl)}</td>
                                        <td className="num">{show(a.desconto_cancelamentos, desconto)}</td>
                                        <td className="num">{show(a.proporcional_am_pa, fmt.brl)}</td>
                                        <td className="num">{show(a.proporcional_pb, fmt.brl)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </section>
        </>
    )
}
