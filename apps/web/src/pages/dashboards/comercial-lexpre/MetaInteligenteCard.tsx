import { useState, type CSSProperties } from 'react'
import { ChartEmpty } from '../../../components/charts/ChartCard.tsx'
import { InfoTip } from '../../../components/dashboard/StatCard.tsx'
import { CountUp } from '../../../components/ui/CountUp.tsx'
import { Icon } from '../../../components/ui/Icon.tsx'
import { fmt } from '../../../lib/format.ts'
import { faixaAtingimento } from './comercial.ts'
import type { MetaInteligente, MetaInteligenteAtendente } from './types.ts'

const JANELAS = [
    { value: '3', label: 'Últimos 3 meses' },
    { value: '6', label: 'Últimos 6 meses' },
    { value: '12', label: 'Últimos 12 meses' },
]

// Mês da série: '2026-10' -> 'out/26'.
const MES_CURTO = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
const mesCurto = (ym: string) => {
    const [a, m] = ym.split('-')
    return `${MES_CURTO[Number(m) - 1] ?? m}/${a.slice(2)}`
}

const tendenciaTone = (label: string) =>
    label.startsWith('crescimento') ? 'ok' : label.startsWith('queda') ? 'danger' : 'neutral'

// Módulo: "Meta Inteligente por Atendente" da v1. A API calcula (média móvel ponderada + tendência linear do valor
// protocolado por mês) para 3, 6 e 12 meses; aqui escolhe a janela. A barra é a média ponderada contra a meta
// sugerida (como na v1); abrir a linha mostra a série mensal e as contas.
export function MetaInteligenteCard({ dados }: { dados?: Record<string, MetaInteligente> }) {
    const [janela, setJanela] = useState('6')
    const [aberto, setAberto] = useState<string | null>(null)
    const atual = dados?.[janela]
    const totais = atual?.totais ?? {}

    return (
        <div className="meta-card">
            <div className="meta-card-head">
                <span className="fstack">
                    <span className="meta-card-title">
                        <Icon name="flow" size={18} />
                        Meta Inteligente por Atendente
                        <InfoTip text="Valor de causa protocolado por atendente, mês a mês: média móvel ponderada (meses recentes pesam mais) + tendência linear projetam o próximo mês; a meta sugerida é a projeção + 10%. Atendente com menos de 2 meses com protocolo fica de fora. Não depende do período nem dos filtros." />
                    </span>
                    <span className="small muted">
                        Média móvel ponderada + tendência linear
                        {atual?.gerado_em ? ` · Gerado em ${atual.gerado_em.split('-').reverse().join('/')}` : ''}
                    </span>
                </span>
                <label className="field-select">
                    <span className="sr-only">Janela de histórico</span>
                    <select value={janela} onChange={(e) => setJanela(e.target.value)}>
                        {JANELAS.map((j) => (
                            <option key={j.value} value={j.value}>
                                {j.label}
                            </option>
                        ))}
                    </select>
                </label>
            </div>
            {!atual || atual.atendentes.length === 0 ? (
                <ChartEmpty>Sem histórico suficiente (2 meses com protocolo) para sugerir metas.</ChartEmpty>
            ) : (
                <>
                    <div className="mi-totais">
                        <span className="fstack">
                            <span className="small muted">Média equipe/mês</span>
                            <strong className="num">{fmt.brlShort(totais.media_equipe_mes ?? 0)}</strong>
                        </span>
                        <span className="fstack">
                            <span className="small muted">Projeção próx. mês</span>
                            <strong className="num">{fmt.brlShort(totais.projecao_total_proximo_mes ?? 0)}</strong>
                        </span>
                        <span className="fstack">
                            <span className="small muted">Meta total sugerida</span>
                            <strong className="num tone-text-info">
                                {fmt.brlShort(totais.meta_total_sugerida ?? 0)}
                            </strong>
                        </span>
                    </div>
                    <ul className="mi-list" role="list">
                        {atual.atendentes.map((a) => (
                            <LinhaMeta
                                key={a.atendente}
                                a={a}
                                aberto={aberto === a.atendente}
                                onToggle={() => setAberto((x) => (x === a.atendente ? null : a.atendente))}
                            />
                        ))}
                    </ul>
                </>
            )}
        </div>
    )
}

function LinhaMeta({ a, aberto, onToggle }: { a: MetaInteligenteAtendente; aberto: boolean; onToggle: () => void }) {
    const pct = a.meta_sugerida > 0 ? Math.max(0, Math.min(100, (a.media_ponderada / a.meta_sugerida) * 100)) : 0
    const tone = tendenciaTone(a.tendencia_label)
    const maior = Math.max(1, ...a.historico_mensal.map((h) => h.valor))
    return (
        <li className="mi-row">
            <button type="button" className="mi-row-head" aria-expanded={aberto} onClick={onToggle}>
                <span className={`mi-trend tone-text-${tone}`}>
                    <Icon name={tone === 'danger' ? 'trend-down' : 'trend-up'} size={16} />
                </span>
                <strong>{a.atendente}</strong>
                <span className={`small tone-text-${tone}`}>{a.tendencia_label}</span>
                <span className="mi-row-right">
                    <span className="small muted num">{fmt.dec1(a.percentual_da_equipe)}% da equipe</span>
                    <strong className="num">{fmt.int(Math.floor(pct))}%</strong>
                    <Icon name={aberto ? 'chevron-up' : 'chevron-down'} size={16} />
                </span>
            </button>
            <span className="meta-track" aria-hidden="true">
                <span
                    className={`meta-bar tone-${faixaAtingimento(pct)}`}
                    style={{ '--w': `${pct}%` } as CSSProperties}
                />
            </span>
            {aberto && (
                <div className="mi-detalhe">
                    <div className="mi-serie" aria-label="Valor protocolado por mês">
                        {a.historico_mensal.map((h) => (
                            <span key={h.mes} className="mi-mes" title={`${mesCurto(h.mes)}: ${fmt.brl(h.valor)}`}>
                                <span className="mi-mes-bar" style={{ height: `${(h.valor / maior) * 100}%` }} />
                                <span className="small muted num">{mesCurto(h.mes)}</span>
                            </span>
                        ))}
                    </div>
                    <dl className="mi-contas">
                        <dt>Média ponderada</dt>
                        <dd className="num">
                            <CountUp value={a.media_ponderada} format={fmt.brl} />
                        </dd>
                        <dt>Tendência/mês</dt>
                        <dd className={`num tone-text-${tone}`}>{fmt.brl(a.tendencia_mensal)}</dd>
                        <dt>Projeção próx. mês</dt>
                        <dd className="num">{fmt.brl(a.projecao_proximo_mes)}</dd>
                        <dt>Meta sugerida (+10%)</dt>
                        <dd className="num tone-text-info">{fmt.brl(a.meta_sugerida)}</dd>
                        <dt>Parte da meta do trimestre</dt>
                        <dd className="num">{fmt.brl(a.meta_proporcional)}</dd>
                    </dl>
                </div>
            )}
        </li>
    )
}
