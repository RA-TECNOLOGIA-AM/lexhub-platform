import { Delta } from '../../components/Delta.tsx'
import { Kpi } from '../../components/Kpi.tsx'
import type { ProtocoloResponse } from '../../data/types.ts'
import { fmt } from '../../lib/format.ts'

// Só o que é do Protocolo: os KPIs. Carregar, erros e cabeçalho ficam no DashboardView.
export function ProtocoloContent({ data }: { data: ProtocoloResponse }) {
    const s = data.stats

    return (
        <>
            <section className="stack" aria-labelledby="periodo">
                <h2 className="h2" id="periodo">
                    No período
                </h2>

                <div className="grid grid-kpi">
                    <Kpi
                        label="Protocolados"
                        value={fmt.int(s.protocolados_total.total)}
                        note={<Delta value={s.protocolados_total.comparativo} />}
                    />
                    <Kpi
                        label="Valor de causa protocolado"
                        value={fmt.brlShort(s.valor_causa_protocolado.total)}
                        note={<Delta value={s.valor_causa_protocolado.comparativo} />}
                    />
                    <Kpi
                        label="Ticket médio"
                        value={fmt.brl(s.ticket_medio_protocolado.total)}
                        note={<Delta value={s.ticket_medio_protocolado.comparativo} />}
                    />
                    <Kpi
                        label="Tempo médio no setor"
                        value={fmt.dias(s.media_tempo_protocolado)}
                        note={<Delta value={s.comparativo_tempo_medio_protocolado} betterWhenDown />}
                    />
                    <Kpi
                        label="Tempo mediano no setor"
                        value={fmt.dias(s.mediana_tempo_protocolado)}
                        note={<Delta value={s.comparativo_mediana_tempo_protocolado} betterWhenDown />}
                    />
                </div>
            </section>

            <section className="stack" aria-labelledby="agora">
                <div>
                    <h2 className="h2" id="agora">
                        Situação atual do setor
                    </h2>
                    <p className="muted small">Não dependem do período selecionado.</p>
                </div>

                <div className="grid grid-kpi">
                    <Kpi
                        label="Represados agora"
                        value={fmt.int(s.represados)}
                        note="Ainda no setor, sem protocolo"
                    />
                    <Kpi
                        label="Devolvidos p/ Peticionamento"
                        value={fmt.int(s.devolvido_peticionamento)}
                        note="Total histórico"
                    />
                    <Kpi
                        label="Devolvidos p/ Org. de documentos"
                        value={fmt.int(s.devolvido_org_doc)}
                        note="Total histórico"
                    />
                    <Kpi
                        label="Devolvidos p/ Pendências"
                        value={fmt.int(s.devolvido_pendencia)}
                        note="Total histórico"
                    />
                </div>
            </section>
        </>
    )
}