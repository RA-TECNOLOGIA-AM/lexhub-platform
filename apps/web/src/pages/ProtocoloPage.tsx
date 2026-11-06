import { useParams } from 'react-router'
import { DashboardHeader } from '../components/DashboardHeader.tsx'
import { Delta } from '../components/Delta.tsx'
import { Kpi } from '../components/Kpi.tsx'
import { dataClient } from '../data/client.ts'
import { useAsync } from '../hooks/useAsync.ts'
import { fmt } from '../lib/format.ts'

const DASHBOARD_KEY = 'protocolo-lexpre'

export function ProtocoloPage() {
    const { org = '', unit = '' } = useParams()
    // Dados da unidade e catálogo ao mesmo tempo; o useAsync busca de novo quando org ou unit mudam.
    const { data: result, error } = useAsync(
        () => Promise.all([dataClient.getProtocolo({ org, unit }), dataClient.listDashboards(org)]),
        [org, unit],
    )

    if (error) return <p className="muted">{error.message}</p>
    if (!result) return <p className="muted">Carregando…</p>

    const [data, catalog] = result
    const dashboard = catalog.available.find((d) => d.key === DASHBOARD_KEY)
    if (!dashboard) return <p className="muted">Dashboard não encontrado no catálogo.</p>

    const s = data.stats

    return (
        <>
            <DashboardHeader org={org} dashboard={dashboard} meta={data.meta} />

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