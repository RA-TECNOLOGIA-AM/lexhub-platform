import type { AdsPreview, AdsTotals } from '../../../types/index.ts'
import { Icon } from '../../../components/ui/Icon.tsx'
import { breakdownLabel, costPer, count, cpm, ctr, dateLabel, money, segmentLabel } from './facebookAds.ts'

type AdsPreviewViewProps = { preview: AdsPreview; currency: string }

// Módulo: a prévia dos últimos 7 dias com a personalização escolhida (nada foi gravado ainda): os números da
// conta, as campanhas, cada detalhamento e os anúncios que mais gastaram, com o criativo.
export function AdsPreviewView({ preview, currency }: AdsPreviewViewProps) {
    const t = preview.totals
    const empty = t.spend === 0 && t.impressions === 0
    return (
        <div className="ads-preview">
            <p className="muted small" style={{ margin: 0 }}>
                Últimos 7 dias ({dateLabel(preview.since)} a {dateLabel(preview.until)}), como vão ficar guardados. Os
                números vêm da Meta agora; nada foi gravado ainda.
            </p>
            {empty && (
                <p className="ads-empty" role="status">
                    Nenhum gasto nesses 7 dias com essa escolha de campanhas. O histórico ainda é coletado.
                </p>
            )}
            <AdsKpis totals={t} currency={currency} />

            <section aria-label="Campanhas na prévia">
                <h4 className="ads-title">Campanhas</h4>
                {preview.campaigns.length === 0 ? (
                    <p className="muted small">Nenhuma campanha com gasto nesses dias.</p>
                ) : (
                    <div className="ads-table-wrap">
                        <table className="ads-table">
                            <thead>
                                <tr>
                                    <th scope="col">Campanha</th>
                                    <th scope="col">Gasto</th>
                                    <th scope="col">Resultados</th>
                                    <th scope="col">Custo/resultado</th>
                                    <th scope="col">CTR</th>
                                </tr>
                            </thead>
                            <tbody>
                                {preview.campaigns.map((c) => (
                                    <tr key={c.id}>
                                        <td>{c.name ?? c.id}</td>
                                        <td>{money(c.spend, currency)}</td>
                                        <td>{count(c.results)}</td>
                                        <td>{costPer(c.spend, c.results, currency)}</td>
                                        <td>{ctr(c.linkClicks, c.impressions)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </section>

            {preview.breakdowns.map((b) => {
                const total = b.rows.reduce((sum, r) => sum + r.spend, 0)
                return (
                    <section key={b.key} aria-label={breakdownLabel(b.key)}>
                        <h4 className="ads-title">{breakdownLabel(b.key)}</h4>
                        {b.rows.length === 0 ? (
                            <p className="muted small">Sem dados nesses dias.</p>
                        ) : (
                            <ul className="ads-bars">
                                {b.rows.map((r) => {
                                    const share = total > 0 ? r.spend / total : 0
                                    return (
                                        <li key={r.segment.join('|')}>
                                            <span className="ads-bar-label">{segmentLabel(b.key, r.segment)}</span>
                                            <span className="ads-bar" aria-hidden="true">
                                                <span style={{ width: `${Math.max(share * 100, 1)}%` }} />
                                            </span>
                                            <span className="ads-bar-value">
                                                {money(r.spend, currency)} · {count(r.results)} result.
                                            </span>
                                        </li>
                                    )
                                })}
                            </ul>
                        )}
                    </section>
                )
            })}

            {preview.ads.length > 0 && (
                <section aria-label="Anúncios que mais gastaram">
                    <h4 className="ads-title">Anúncios que mais gastaram</h4>
                    <div className="ads-creatives">
                        {preview.ads.map((a) => (
                            <article key={a.id} className="ads-creative">
                                {a.creative?.imageUrl ? (
                                    <img src={a.creative.imageUrl} alt="" loading="lazy" referrerPolicy="no-referrer" />
                                ) : (
                                    <span className="ads-creative-ph" aria-hidden="true">
                                        <Icon name="target" size={20} />
                                    </span>
                                )}
                                <div className="ads-creative-text">
                                    <strong>{a.creative?.title ?? a.name ?? a.id}</strong>
                                    {a.creative?.body && <span className="small ads-clamp">{a.creative.body}</span>}
                                    <span className="muted small">
                                        {a.campaignName} · {money(a.spend, currency)} · {count(a.results)} result.
                                    </span>
                                    {a.creative?.linkUrl && (
                                        <span className="muted small ads-link" title={a.creative.linkUrl}>
                                            {a.creative.linkUrl}
                                        </span>
                                    )}
                                </div>
                            </article>
                        ))}
                    </div>
                </section>
            )}
        </div>
    )
}

// Módulo: os números de um período (gasto, resultados, custos, cliques...). Também usado no painel do detalhe.
export function AdsKpis({ totals, currency }: { totals: AdsTotals; currency: string }) {
    const t = totals
    const items: [string, string][] = [
        ['Gasto', money(t.spend, currency)],
        ['Resultados', count(t.results)],
        ['Custo por resultado', costPer(t.spend, t.results, currency)],
        ['Leads', count(t.leads)],
        ['Conversas', count(t.conversations)],
        ['Impressões', count(t.impressions)],
        ['Cliques no link', count(t.linkClicks)],
        ['CTR (link)', ctr(t.linkClicks, t.impressions)],
        ['CPC (link)', costPer(t.spend, t.linkClicks, currency)],
        ['CPM', cpm(t.spend, t.impressions, currency)],
    ]
    if (t.reach !== null) items.push(['Alcance', count(t.reach)])
    if (t.thruplays !== null) items.push(['ThruPlays', count(t.thruplays)])
    return (
        <dl className="ads-kpis">
            {items.map(([label, value]) => (
                <div key={label} className="ads-kpi">
                    <dt>{label}</dt>
                    <dd>{value}</dd>
                </div>
            ))}
        </dl>
    )
}
