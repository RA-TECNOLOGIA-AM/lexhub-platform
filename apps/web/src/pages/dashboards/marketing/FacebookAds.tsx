import { useState, type CSSProperties, type ReactNode } from 'react'
import { ChartCard } from '../../../components/charts/ChartCard.tsx'
import { LineChart } from '../../../components/charts/LineChart.tsx'
import { DashSection } from '../../../components/dashboard/DashSection.tsx'
import { Pill, ToneIcon } from '../../../components/dashboard/StatCard.tsx'
import type { Tone } from '../../../components/dashboard/tone.ts'
import { CountUp } from '../../../components/ui/CountUp.tsx'
import type { IconName } from '../../../components/ui/Icon.tsx'
import { fmt } from '../../../lib/format.ts'
import { LinhasDuasEscalas } from './LinhasDuasEscalas.tsx'
import { funilAnuncio, funilPipeline, participacao, variacaoSobre, type Leitor } from './marketingComum.ts'

const pct1 = (v: number) => `${fmt.dec1(v)}%`
const vezes = (v: number) => `${fmt.dec2(v)}x`

// Card de indicador do topo: rótulo e ícone, o número grande e uma linha de contexto embaixo.
function Indicador(p: {
    label: string
    icon: IconName
    tone: Tone
    value: number
    format: (v: number) => string
    legenda: ReactNode
    valorNaCor?: boolean // o número na cor do tom (ex.: ROAS em verde)
}) {
    return (
        <div className={`card hero tone-${p.tone} mkt-ind`}>
            <div className="hero-top">
                <span className="hero-l">{p.label}</span>
                <ToneIcon icon={p.icon} tone={p.tone} />
            </div>
            <span className={`mkt-ind-v num${p.valorNaCor ? ' tone-text' : ''}`}>
                <CountUp value={p.value} format={p.format} />
            </span>
            <span className="mkt-ind-legenda">{p.legenda}</span>
        </div>
    )
}

// Card pequeno da linha de leads: rótulo, número e uma legenda curta (a parte dele no par ativa/passiva).
function Pequeno(p: { label: string; value: number; legenda: ReactNode; tone?: Tone; valorNaCor?: boolean }) {
    return (
        <div className={`card mkt-peq tone-${p.tone ?? 'neutral'}`}>
            <span className="hero-l">{p.label}</span>
            <span className={`mkt-peq-v num${p.valorNaCor ? ' tone-text' : ''}`}>
                <CountUp value={p.value} format={fmt.int} />
            </span>
            <span className="mkt-peq-legenda">{p.legenda}</span>
        </div>
    )
}

const COR_ETAPA = ['var(--accent)', 'var(--accent)', 'var(--c-info)', 'var(--ok-dot)']

function FunilAnuncio({ ler }: { ler: Leitor }) {
    const { n } = ler
    const etapas = funilAnuncio([
        { nome: 'Cliques', valor: n('facebook_cliques') },
        { nome: 'Pageview', valor: n('facebook_pageview') },
        { nome: 'Leads', valor: n('facebook_leads') },
        { nome: 'Clientes', valor: n('total_clientes') },
    ])
    const base = ['', 'dos cliques', 'dos pageviews', 'dos leads']
    const cliqueCliente = participacao(etapas[3].valor, etapas[0].valor)
    return (
        <ChartCard
            title="Anúncio · Funil de conversão"
            subtitle="Do clique ao cliente fechado no período, com taxas de passagem"
            action={<Pill tone="accent">{`${pct1(cliqueCliente)} Clique → Cliente`}</Pill>}
            footer={
                <div className="mkt-passagens">
                    {etapas.slice(1).map((e, i) => (
                        <div key={e.nome} className="mkt-passagem">
                            <span>
                                {etapas[i].nome === 'Cliques' ? 'Clique' : etapas[i].nome.replace(/s$/, '')} →{' '}
                                {e.nome.replace(/s$/, '')}
                            </span>
                            <strong className="num" style={{ color: COR_ETAPA[i + 1] }}>
                                {pct1(e.taxa)}
                            </strong>
                        </div>
                    ))}
                </div>
            }
        >
            {etapas[0].valor === 0 ? (
                <p className="chart-empty muted small">Sem dados de anúncios no período.</p>
            ) : (
                <ol className="mkt-funil">
                    {etapas.map((e, i) => (
                        <li key={e.nome}>
                            <span className="mkt-funil-top">
                                <span>
                                    <span className="num muted">{String(i + 1).padStart(2, '0')}</span>{' '}
                                    <strong>{e.nome}</strong>{' '}
                                    <span className="muted small">
                                        ({i === 0 ? '100%' : `${pct1(e.taxa)} ${base[i]}`})
                                    </span>
                                </span>
                                <strong className="num">{fmt.int(e.valor)}</strong>
                            </span>
                            <span className="mkt-trilho">
                                <span
                                    style={
                                        {
                                            '--w': `${Math.max(e.valor > 0 ? 2 : 0, e.largura)}%`,
                                            '--cor': COR_ETAPA[i],
                                        } as CSSProperties
                                    }
                                />
                            </span>
                        </li>
                    ))}
                </ol>
            )}
        </ChartCard>
    )
}

function FunilPipeline({ ler }: { ler: Leitor }) {
    const [aberto, setAberto] = useState(false)
    const { ativas, zeradas, maior, conversao } = funilPipeline(ler.serie('funil_pipeline'))
    const ultima = ativas.length - 1
    return (
        <ChartCard
            title="Funil de pipeline comercial"
            subtitle="Etapas do banco NG legado (o LexPre não tem essas etapas); zeradas agrupadas"
            action={
                zeradas.length > 0 && (
                    <button type="button" className="btn mkt-btn" onClick={() => setAberto((a) => !a)}>
                        {aberto ? 'Agrupar etapas zeradas' : `Expandir ${zeradas.length} etapas zeradas`}
                    </button>
                )
            }
            footer={
                conversao && (
                    <div className="mkt-pipe-conv">
                        <span>
                            Conversão {conversao.de.name} → {conversao.para.name}:
                        </span>
                        <strong className="num tone-text-ok">
                            {pct1(conversao.taxa)} ({fmt.int(conversao.para.value)} / {fmt.int(conversao.de.value)})
                        </strong>
                    </div>
                )
            }
        >
            <div className="mkt-pipe">
                {zeradas.length > 0 &&
                    (aberto ? (
                        zeradas.map((e) => (
                            <div key={e.name} className="mkt-pipe-zero">
                                <span>{e.name}</span>
                                <span className="num">0</span>
                            </div>
                        ))
                    ) : (
                        <div className="mkt-pipe-zeradas">
                            <span>
                                <strong>{zeradas.length} etapas intermediárias sem saldo atual</strong>
                                <span className="muted small">{zeradas.map((e) => e.name).join(' → ')}</span>
                            </span>
                            <span className="num mkt-pipe-zero-n">0</span>
                        </div>
                    ))}
                {ativas.map((e, i) => (
                    <div key={e.name} className={`mkt-pipe-etapa ${i === ultima ? 'tone-ok' : 'tone-accent'}`}>
                        <span className="mkt-pipe-top">
                            <strong className="tone-text">{e.name}</strong>
                            <strong className="num">{fmt.int(e.value)}</strong>
                        </span>
                        <span className="mkt-trilho">
                            <span
                                style={
                                    {
                                        '--w': `${participacao(e.value, maior)}%`,
                                        '--cor': 'var(--tone)',
                                    } as CSSProperties
                                }
                            />
                        </span>
                    </div>
                ))}
                {ativas.length === 0 && zeradas.length === 0 && (
                    <p className="chart-empty muted small">Sem dados de pipeline no período.</p>
                )}
            </div>
        </ChartCard>
    )
}

// 03 · Facebook Ads, igual nas duas páginas do Marketing. O funil de pipeline só existe no banco NG: sem ele, o
// funil do anúncio ocupa a linha inteira.
export function FacebookAds({ ler, index }: { ler: Leitor; index: number }) {
    const { n, serie, investimento } = ler
    const temPipeline = serie('funil_pipeline').length > 0
    const cacCamp = n('facebook_cac_campanha')
    const cacGeral = n('facebook_cac_geral')
    const difCac = variacaoSobre(cacGeral, cacCamp)
    const ind = n('indicacao_ativa') + n('indicacao_passiva')
    const ret = n('retorno_ativa') + n('retorno_passiva')
    const dias = investimento.map((p) => p.name)
    const media = investimento.length ? investimento.reduce((s, p) => s + p.investimento, 0) / investimento.length : 0
    // A parte maior do par ativa/passiva vai colorida.
    const parte = (v: number, total: number, outro: number, nome: string, cor: Tone) => (
        <span className={v >= outro && v > 0 ? `tone-text-${cor}` : undefined}>
            {`${pct1(participacao(v, total))} ${nome}`}
        </span>
    )

    return (
        <DashSection
            index={index}
            eyebrow="Facebook Ads"
            title="Facebook Ads"
            subtitle="Funil de conversão do anúncio, pipeline comercial e evolução diária de investimento, cliques e leads."
        >
            <div className="mkt-grid-5">
                <Indicador
                    label="Valor gasto"
                    icon="dollar"
                    tone="danger"
                    value={n('facebook_valor_gasto')}
                    format={fmt.brl}
                    legenda="Investimento no período"
                />
                <Indicador
                    label="CAC campanha"
                    icon="target"
                    tone="info"
                    value={cacCamp}
                    format={fmt.brl}
                    legenda={
                        <span className="tone-text-info">{`Base: ${fmt.int(n('clientes_campanha'))} clientes camp.`}</span>
                    }
                />
                <Indicador
                    label="CAC geral"
                    icon="target"
                    tone="accent"
                    value={cacGeral}
                    format={fmt.brl}
                    legenda={
                        difCac === null ? (
                            'Anúncio + indicação'
                        ) : (
                            <span className={difCac <= 0 ? 'tone-text-ok' : 'tone-text-danger'}>
                                {`${difCac > 0 ? '+' : ''}${pct1(difCac)} vs. CAC campanha`}
                            </span>
                        )
                    }
                />
                <Indicador
                    label="ROAS campanha"
                    icon="trend-up"
                    tone="ok"
                    value={n('facebook_roas_campanha')}
                    format={vezes}
                    legenda="Retorno direto atribuído"
                    valorNaCor
                />
                <Indicador
                    label="ROAS geral"
                    icon="trend-up"
                    tone="ok"
                    value={n('facebook_roas_geral')}
                    format={vezes}
                    legenda="Retorno global (org + pago)"
                    valorNaCor
                />
            </div>

            <div className={temPipeline ? 'mkt-grid-2 grid-mini' : 'grid-mini'}>
                <FunilAnuncio ler={ler} />
                {temPipeline && <FunilPipeline ler={ler} />}
            </div>

            <div className="mkt-grid-6 grid-mini">
                <Pequeno
                    label="Clientes campanha"
                    value={n('clientes_campanha')}
                    legenda={<span className="tone-text-danger">Atribuídos Ads</span>}
                />
                <Pequeno label="Leads totais" value={n('leads')} legenda="Todos os canais" tone="info" valorNaCor />
                <Pequeno
                    label="Indicação ativa"
                    value={n('indicacao_ativa')}
                    legenda={parte(n('indicacao_ativa'), ind, n('indicacao_passiva'), 'indicações', 'accent')}
                />
                <Pequeno
                    label="Indicação passiva"
                    value={n('indicacao_passiva')}
                    legenda={parte(n('indicacao_passiva'), ind, n('indicacao_ativa'), 'indicações', 'accent')}
                />
                <Pequeno
                    label="Retorno ativa"
                    value={n('retorno_ativa')}
                    legenda={parte(n('retorno_ativa'), ret, n('retorno_passiva'), 'retornos', 'ok')}
                />
                <Pequeno
                    label="Retorno passiva"
                    value={n('retorno_passiva')}
                    legenda={parte(n('retorno_passiva'), ret, n('retorno_ativa'), 'retornos', 'ok')}
                />
            </div>

            <div className="mkt-grid-2 grid-mini">
                <ChartCard
                    title="Investimento por dia"
                    subtitle="Valor gasto diário no Facebook Ads (passe o cursor para inspecionar)"
                    action={media > 0 && <Pill tone="accent">{`Média: ${fmt.brl(media)}/dia`}</Pill>}
                >
                    <LineChart
                        labels={dias}
                        series={[
                            {
                                label: 'Investimento',
                                color: 'var(--accent)',
                                values: investimento.map((p) => p.investimento),
                            },
                        ]}
                        format={fmt.brl}
                        area
                        tooltip={{ heading: 'Dia', title: (i) => dias[i] }}
                    />
                </ChartCard>
                <ChartCard
                    title="Cliques e leads por dia"
                    subtitle={
                        <>
                            Eixo esq.: <strong>Cliques</strong> · Eixo dir.:{' '}
                            <strong className="tone-text-info">Leads</strong>
                        </>
                    }
                    action={
                        <span className="mkt-legenda-linha">
                            <span>
                                <span className="chart-key" style={{ background: 'var(--text)' }} /> Cliques
                            </span>
                            <span>
                                <span className="chart-key" style={{ background: 'var(--c-info)' }} /> Leads
                            </span>
                        </span>
                    }
                >
                    <LinhasDuasEscalas
                        labels={dias}
                        esquerda={{
                            label: 'Cliques',
                            color: 'var(--text)',
                            values: investimento.map((p) => p.cliques),
                        }}
                        direita={{ label: 'Leads', color: 'var(--c-info)', values: investimento.map((p) => p.leads) }}
                    />
                </ChartCard>
            </div>
        </DashSection>
    )
}
