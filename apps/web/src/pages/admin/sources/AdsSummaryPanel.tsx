import type { AdsBreakdown, AdsSummary } from '../../../types/index.ts'
import { AdsKpis } from './AdsPreviewView.tsx'
import {
    BREAKDOWN_OPTIONS,
    breakdownLabel,
    costPer,
    count,
    dateLabel,
    isActive,
    money,
    objectiveLabel,
    statusLabel,
} from './facebookAds.ts'

type AdsSummaryPanelProps = { summary: AdsSummary; currency: string }

// Módulo: o que a coleta do Facebook Ads já guardou no LexHub: período, andamento do histórico, os números dos
// últimos 30 dias, as campanhas que mais gastaram, os detalhamentos e a estrutura (campanhas, conjuntos,
// anúncios, criativos). Vem de api.source_detail (app_private.facebook_ads_summary).
export function AdsSummaryPanel({ summary, currency }: AdsSummaryPanelProps) {
    const s = summary
    const l = s.last30
    const breakdowns = Object.entries(s.breakdownRows) as [AdsBreakdown, number][]
    const progress =
        s.backfill === null
            ? 'A primeira coleta ainda não começou (ela roda logo depois de conectar).'
            : s.backfill.done
              ? 'Histórico completo; os últimos dias são atualizados a cada 10 minutos.'
              : `Buscando o histórico: já guardado até ${dateLabel(s.backfill.coveredUntil)}.`
    return (
        <section aria-label="Dados guardados" className="ads-summary">
            <h3 className="source-section-title">Dados guardados no LexHub</h3>
            <dl className="source-facts">
                <dt>Período</dt>
                <dd>{s.firstDay ? `${dateLabel(s.firstDay)} a ${dateLabel(s.lastDay)}` : 'Nada guardado ainda'}</dd>
                <dt>Linhas</dt>
                <dd>{count(s.rows)} (anúncio por dia)</dd>
                <dt>Coleta</dt>
                <dd className={s.backfill?.done ? undefined : 'ads-progress'}>{progress}</dd>
                {s.entities && (
                    <>
                        <dt>Estrutura</dt>
                        <dd>
                            {count(s.entities.campaigns)} campanhas ({count(s.entities.activeCampaigns)} ativas),{' '}
                            {count(s.entities.adsets)} conjuntos, {count(s.entities.ads)} anúncios
                            {s.entities.creatives > 0 && `, ${count(s.entities.creatives)} criativos`}
                        </dd>
                    </>
                )}
                <dt>Detalhamentos</dt>
                <dd>
                    {breakdowns.length === 0
                        ? 'Nenhum guardado'
                        : BREAKDOWN_OPTIONS.filter((b) => s.breakdownRows[b.key] !== undefined)
                              .map((b) => `${breakdownLabel(b.key)} (${count(s.breakdownRows[b.key])} linhas)`)
                              .join(', ')}
                </dd>
            </dl>

            <h4 className="ads-title">Últimos 30 dias</h4>
            <AdsKpis totals={{ ...l, reach: null, thruplays: null }} currency={currency} />

            {s.topCampaigns.length > 0 && (
                <>
                    <h4 className="ads-title">Campanhas que mais gastaram (30 dias)</h4>
                    <div className="ads-table-wrap">
                        <table className="ads-table">
                            <thead>
                                <tr>
                                    <th scope="col">Campanha</th>
                                    <th scope="col">Objetivo</th>
                                    <th scope="col">Gasto</th>
                                    <th scope="col">Resultados</th>
                                    <th scope="col">Custo/resultado</th>
                                </tr>
                            </thead>
                            <tbody>
                                {s.topCampaigns.map((c) => (
                                    <tr key={c.id}>
                                        <td>
                                            {c.name ?? c.id}{' '}
                                            <span className={`badge ${isActive(c.status) ? 'ok' : 'neutral'}`}>
                                                {statusLabel(c.status)}
                                            </span>
                                        </td>
                                        <td>{objectiveLabel(c.objective)}</td>
                                        <td>{money(c.spend, currency)}</td>
                                        <td>{count(c.results)}</td>
                                        <td>{costPer(c.spend, c.results, currency)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </>
            )}
        </section>
    )
}
