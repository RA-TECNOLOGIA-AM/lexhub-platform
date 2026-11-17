import { useState, type CSSProperties, type ReactNode } from 'react'
import { ChartCard, ChartEmpty } from '../../../components/charts/ChartCard.tsx'
import { DashSection } from '../../../components/dashboard/DashSection.tsx'
import { DeltaPill, MiniStat, Pill } from '../../../components/dashboard/StatCard.tsx'
import type { Tone } from '../../../components/dashboard/tone.ts'
import { CountUp } from '../../../components/ui/CountUp.tsx'
import { Icon } from '../../../components/ui/Icon.tsx'
import { Modal } from '../../../components/ui/Modal.tsx'
import { fmt } from '../../../lib/format.ts'
import type { ContentProps } from '../types.ts'
import {
    ZONA_FRASE,
    ZONA_NOME,
    atingimentoPorMeta,
    compacto,
    mesNome,
    metasDoCard,
    proximaZona,
    regua,
    trimestreNome,
    zonaClasse,
    zonaDe,
    type Metas,
} from './metaAnual.ts'
import type {
    CardTrimestre,
    MetaAnualData,
    MetaAnualResponse,
    Predicao,
    PredicaoTrimestre,
    Trimestre,
    ZonaUI,
} from './types.ts'

const pct = (v: number) => `${fmt.dec1(v)}%`
const largura = (v: number) => ({ '--w': `${Math.min(100, Math.max(0, v))}%` }) as CSSProperties
const dataBr = (iso: string) => iso.split('-').reverse().join('/')

// A Meta anual (Financeiro): a página "Meta Anual" da v1 (MetaAnualNG.tsx) no layout novo. Faturamento do ano
// (honorários + sucumbência da planilha do financeiro) contra as metas Triste, Base, Avançada e Super, por ano e
// por trimestre, e a análise preditiva da Super Meta. Carregar, erros, cabeçalho e período ficam no
// DashboardView; o fim do período é a data de referência ("hoje").
export function MetaAnualContent({ data }: ContentProps<MetaAnualResponse>) {
    const d = data.data
    const [aberto, setAberto] = useState<CardTrimestre | null>(null)
    if (!d) return <ChartEmpty>Sem dados da planilha do financeiro para esta unidade.</ChartEmpty>

    const p = d.predicao ?? null
    const atual = d.cards_trimestre.find((c) => c.status === 'em_curso') ?? d.cards_trimestre.at(-1)
    const predTrim = (c: CardTrimestre) => p?.por_trimestre.find((t) => t.trimestre === c.trimestre)

    return (
        <div className="dsecs">
            <DashSection index={1} eyebrow="Visão geral" title="Situação no acumulado">
                <Situacao d={d} p={p} unidade={data.meta.unit} />
            </DashSection>

            <DashSection
                index={2}
                eyebrow="Réguas"
                title="Réguas de desempenho"
                subtitle={`Posição atual nas faixas de premiação e metas (anual e ${atual ? trimestreNome(atual.trimestre) : 'trimestre'}).`}
            >
                <div className="mz-stack">
                    <ReguaCard titulo="Régua anual" valor={d.ytd.atingido} metas={d.ytd.metas} />
                    {atual && (
                        <ReguaCard
                            titulo={`Régua trimestral (${trimestreNome(atual.trimestre)})`}
                            valor={atual.atingido}
                            metas={metasDoCard(atual)}
                        />
                    )}
                </div>
            </DashSection>

            <DashSection
                index={3}
                eyebrow="Trimestres"
                title="Por trimestre"
                subtitle="Clique em qualquer trimestre para abrir o detalhamento mensal e de metas."
            >
                <div className="grid mz-tris">
                    {d.cards_trimestre.map((c) => (
                        <TrimestreCard
                            key={c.trimestre}
                            c={c}
                            pred={predTrim(c)}
                            compareYear={d.compare_year}
                            onOpen={() => setAberto(c)}
                        />
                    ))}
                </div>
            </DashSection>

            {p && (
                <DashSection index={4} eyebrow="Ano" title="Super Meta anual">
                    <SuperMetaAnual p={p} />
                </DashSection>
            )}

            {p && (
                <DashSection
                    index={5}
                    eyebrow="Preditiva"
                    title="Análise preditiva"
                    subtitle="Esperado até hoje, projeção do ano e ritmo necessário para a Super Meta."
                >
                    <Preditiva p={p} trimestre={d.trimestre_atual} asOf={d.as_of} />
                </DashSection>
            )}

            {aberto && (
                <TrimestreModal
                    c={aberto}
                    pred={predTrim(aberto)}
                    compareYear={d.compare_year}
                    onClose={() => setAberto(null)}
                />
            )}
        </div>
    )
}

// 01 · "No acumulado, estamos na zona base." e o quadro do acumulado do ano.
function Situacao({ d, p, unidade }: { d: MetaAnualData; p: Predicao | null; unidade: string }) {
    const zona = zonaDe(d.ytd.atingido, d.ytd.metas)
    const prox = proximaZona(d.ytd.atingido, d.ytd.metas)
    const atual = d.cards_trimestre.find((c) => c.status === 'em_curso')
    return (
        <section className={`card mz-hero ${zonaClasse(zona)}`}>
            <div className="mz-hero-text">
                <div className="mz-hero-tags">
                    <span className="mz-eyebrow">
                        {unidade} — {atual ? `${trimestreNome(atual.trimestre)} em curso` : `ano de ${d.year}`}
                    </span>
                    {p && <Pill tone="ok">{pct(p.frac_ano_pct)} do ano decorrido</Pill>}
                </div>
                <h2 className="mz-headline">
                    No acumulado, estamos na <span className="z-text">{ZONA_FRASE[zona]}</span>.
                </h2>
                <p className="muted">
                    {prox.zona ? (
                        <>
                            Faltam <strong className="num">{compacto(prox.falta)}</strong> para alcançar a{' '}
                            <strong>Meta {ZONA_NOME[prox.zona]}</strong> ({compacto(d.ytd.metas[prox.zona])}).
                        </>
                    ) : (
                        <>
                            Super Meta do ano atingida: <strong className="num">{compacto(d.ytd.metas.SUPER)}</strong>.
                        </>
                    )}
                </p>
            </div>
            <div className="mz-hero-box">
                <div className="mz-row">
                    <span className="muted small">Acumulado {d.year}</span>
                    <DeltaPill value={d.ytd.variacao_pct_vs_compare} suffix={` vs. ${d.compare_year}`} />
                </div>
                <strong className="mz-big num">
                    <CountUp value={d.ytd.atingido} format={fmt.brl} />
                </strong>
                <div className="mz-lines small">
                    {prox.zona && (
                        <span>
                            <span className="muted">Meta {ZONA_NOME[prox.zona].toLowerCase()}:</span>
                            <strong className="num">{fmt.brl(d.ytd.metas[prox.zona])}</strong>
                        </span>
                    )}
                    <span>
                        <span className="muted">Mesmo corte {d.compare_year}:</span>
                        <strong className="num">{fmt.brl(d.ytd.atingido_compare)}</strong>
                    </span>
                </div>
            </div>
        </section>
    )
}

// 02 · A régua: as faixas Entrada → Super, o marcador no valor e a meta de cada faixa embaixo.
function ReguaCard({ titulo, valor, metas }: { titulo: string; valor: number; metas: Metas }) {
    const zona = zonaDe(valor, metas)
    const r = regua(valor, metas)
    const prox = proximaZona(valor, metas)
    const status =
        zona === 'ENTRADA' ? (
            <>
                Faltam <strong className="num">{compacto(prox.falta)}</strong> para atingir a meta Triste (
                {pct((valor / metas.TRISTE) * 100)})
            </>
        ) : (
            <>
                Meta {ZONA_NOME[zona]} atingida (+{compacto(valor - metas[zona as keyof Metas])} acima do piso)
            </>
        )
    return (
        <ChartCard
            title={titulo}
            tag={
                <span className={`mz-tag ${zonaClasse(zona)}`}>
                    Zona {ZONA_NOME[zona]} • {compacto(valor)}
                </span>
            }
            action={<span className="small muted mz-status">{status}</span>}
        >
            <div className="mz-regua">
                <div
                    className="mz-faixas"
                    role="img"
                    aria-label={`${titulo}: ${compacto(valor)}, zona ${ZONA_NOME[zona]}`}
                >
                    {r.faixas.map((f) => (
                        <span
                            key={f.zona}
                            className={`mz-faixa ${zonaClasse(f.zona)}${f.zona === zona ? ' on' : ''}`}
                            style={{ width: `${f.largura}%` }}
                        >
                            {ZONA_NOME[f.zona]}
                        </span>
                    ))}
                </div>
                <span className="mz-marcador" style={{ left: `${r.marcador}%` }} aria-hidden="true">
                    <span className="mz-bolha num">
                        <Icon name="trend-up" size={12} /> {compacto(valor)}
                    </span>
                </span>
                <ul className="mz-legenda" role="list">
                    {r.faixas.map((f, i) => {
                        const ultima = i === r.faixas.length - 1
                        return (
                            <li
                                key={f.zona}
                                className={zonaClasse(f.zona)}
                                style={ultima ? { right: 0, textAlign: 'right' } : { left: `${f.inicio}%` }}
                            >
                                <strong className="z-text">{ZONA_NOME[f.zona]}</strong>
                                <span className="num muted">
                                    {f.zona === 'ENTRADA' ? 'Meta: —' : fmt.brl(metas[f.zona as keyof Metas])}
                                </span>
                            </li>
                        )
                    })}
                </ul>
            </div>
        </ChartCard>
    )
}

// "Atingido e % que falta por meta": uma barra por meta.
function PorMeta({ valor, metas }: { valor: number; metas: Metas }) {
    return (
        <ul className="mz-metas" role="list">
            {atingimentoPorMeta(valor, metas).map((m) => (
                <li key={m.zona} className={zonaClasse(m.zona)}>
                    <span>{ZONA_NOME[m.zona]}</span>
                    <span className="num small">
                        <strong>{pct(m.pct)}</strong> atingido · {pct(m.falta)} falta
                    </span>
                    <span className="mz-bar" style={largura(m.pct)} aria-hidden="true" />
                </li>
            ))}
        </ul>
    )
}

// O bloco "Super Meta trimestral": meta, barra e quanto falta.
function SuperMetaTrim({ c }: { c: CardTrimestre }) {
    const pctSuper = c.meta_super > 0 ? Math.min(100, (c.atingido / c.meta_super) * 100) : 0
    const falta = Math.max(0, c.meta_super - c.atingido)
    return (
        <div className="mz-bloco">
            <span className="muted small">Super Meta trimestral</span>
            <strong className="mz-mid num">{compacto(c.meta_super)}</strong>
            <span className="mz-bar mz-bar-super" style={largura(pctSuper)} aria-hidden="true" />
            <span className="small tone-text-warn">
                {falta > 0 ? `Faltam ${compacto(falta)} (${pct(100 - pctSuper)} para a meta)` : 'Super Meta atingida'}
            </span>
            <span className="small muted num">
                Realizado: {compacto(c.atingido)} · {pct(pctSuper)} atingido
            </span>
        </div>
    )
}

// O bloco "Esperado até hoje" do trimestre em curso: Super Meta × % dos dias, contra o realizado.
function Esperado({ t }: { t: PredicaoTrimestre }) {
    const abaixo = t.gap < 0
    const pctReal = t.expectativa_ate_hoje > 0 ? (t.realizado / t.expectativa_ate_hoje) * 100 : 0
    return (
        <div className={`mz-bloco mz-esperado${abaixo ? ' abaixo' : ''}`}>
            <span className="muted small">Esperado até hoje</span>
            <strong className="mz-mid num">{compacto(t.expectativa_ate_hoje)}</strong>
            <span className="small muted num">
                {compacto(t.meta)} × {pct(t.frac_decorrida_pct)} dos dias do trimestre
            </span>
            <span className="mz-bar mz-bar-esperado" style={largura(pctReal)} aria-hidden="true" />
            <span className={`small num tone-text-${abaixo ? 'danger' : 'ok'}`}>
                {abaixo ? '↓' : '↑'} {compacto(Math.abs(t.gap))} ({t.gap_pct !== null && t.gap_pct > 0 ? '+' : ''}
                {t.gap_pct !== null ? pct(t.gap_pct) : '—'} vs. esperado)
            </span>
        </div>
    )
}

// 03 · Um trimestre: valor, zona, comparação com o ano anterior, cada meta e a Super Meta. Clicar abre o modal.
function TrimestreCard({
    c,
    pred,
    compareYear,
    onOpen,
}: {
    c: CardTrimestre
    pred?: PredicaoTrimestre
    compareYear: number
    onOpen: () => void
}) {
    const metas = metasDoCard(c)
    const zona = zonaDe(c.atingido, metas)
    const emCurso = c.status === 'em_curso'
    const pctSuper = c.meta_super > 0 ? (c.atingido / c.meta_super) * 100 : 0
    return (
        <button
            type="button"
            className={`card mz-tri ${zonaClasse(zona)}${emCurso ? ' atual' : ''}`}
            onClick={onOpen}
            aria-label={`Ver detalhes do ${trimestreNome(c.trimestre)}`}
        >
            <span className="mz-row">
                <span className="mz-eyebrow">{trimestreNome(c.trimestre)}</span>
                {emCurso && pred ? (
                    <Pill tone="ok">{fmt.int(pred.frac_decorrida_pct)}% do trim.</Pill>
                ) : (
                    <span className="small muted">{c.status === 'a_iniciar' ? 'A iniciar' : 'Ver detalhes →'}</span>
                )}
            </span>
            <strong className="mz-big num">{compacto(c.atingido)}</strong>
            <span className="mz-zona small z-text">• {zona === 'ENTRADA' ? 'Entrada' : `Meta ${ZONA_NOME[zona]}`}</span>
            <span className="mz-bar mz-bar-zona" style={largura(pctSuper)} aria-hidden="true" />
            <DeltaPill value={c.variacao_pct_vs_compare} suffix={` vs. ${compareYear}`} plain />
            <span className="mz-div" />
            <span className="mz-eyebrow">Atingido e % que falta por meta</span>
            <PorMeta valor={c.atingido} metas={metas} />
            <span className="mz-div" />
            <SuperMetaTrim c={c} />
            {emCurso && pred && <Esperado t={pred} />}
        </button>
    )
}

// O modal do trimestre: atingido × ano anterior, os meses, as metas e a Super Meta (como na v1).
function TrimestreModal({
    c,
    pred,
    compareYear,
    onClose,
}: {
    c: CardTrimestre
    pred?: PredicaoTrimestre
    compareYear: number
    onClose: () => void
}) {
    const metas = metasDoCard(c)
    const zona = zonaDe(c.atingido, metas)
    const prox = proximaZona(c.atingido, metas)
    // "Progresso no trimestre": quanto do caminho até a próxima meta (a Super atingida = 100%).
    const progresso = prox.zona ? (c.atingido / metas[prox.zona]) * 100 : 100
    const caixa = (rotulo: string, valor: ReactNode, extra?: ReactNode) => (
        <div className="mz-caixa">
            <span className="muted small">{rotulo}</span>
            <strong className="mz-mid num">{valor}</strong>
            {extra}
        </div>
    )
    return (
        <Modal
            title={`Detalhes do ${trimestreNome(c.trimestre)}`}
            subtitle={`Comparação com ${compareYear}, abertura mensal e metas por status do trimestre.`}
            aside={<span className={`mz-tag ${zonaClasse(zona)}`}>• {ZONA_NOME[zona]}</span>}
            className="mz-modal"
            onClose={onClose}
        >
            <div className={`mz-modal-body ${zonaClasse(zona)}`}>
                <div className="mz-caixas">
                    {caixa('Atingido', fmt.brl(c.atingido), <span className="small z-text">• {ZONA_NOME[zona]}</span>)}
                    {caixa(
                        String(compareYear),
                        fmt.brl(c.atingido_compare),
                        <DeltaPill value={c.variacao_pct_vs_compare} plain />,
                    )}
                    {caixa(
                        'Progresso no trimestre',
                        pct(progresso),
                        <span className="mz-bar mz-bar-zona" style={largura(progresso)} aria-hidden="true" />,
                    )}
                </div>
                <div className="mz-caixas">
                    {Object.entries(c.atingido_mensal).map(([mes, v]) => (
                        <div key={mes}>{caixa(mesNome(mes), fmt.brl(v))}</div>
                    ))}
                </div>
                <div className="mz-duas">
                    <div className="mz-caixa">
                        <strong>Metas do trimestre</strong>
                        <dl className="mz-dl">
                            {(['TRISTE', 'BASE', 'AVANCADA', 'SUPER'] as const).map((z) => (
                                <div key={z}>
                                    <dt className="muted">{ZONA_NOME[z]}</dt>
                                    <dd className="num">{fmt.brl(metas[z])}</dd>
                                </div>
                            ))}
                        </dl>
                    </div>
                    <div className="mz-caixa">
                        <strong>Atingido e % que falta por meta</strong>
                        <PorMeta valor={c.atingido} metas={metas} />
                    </div>
                </div>
                <SuperMetaTrim c={c} />
                {pred && c.status === 'em_curso' && <Esperado t={pred} />}
            </div>
        </Modal>
    )
}

// 04 · Super Meta anual: progresso, esperado até hoje, projeção e o ritmo diário necessário.
function SuperMetaAnual({ p }: { p: Predicao }) {
    const a = p.super_meta_anual
    const r = p.ritmo_diario_anual
    const proj = p.projecao_fim_ano
    const insuficiente = r.diferenca_diaria > 0
    const abaixo = a.gap_ytd < 0
    const stat = (rotulo: string, valor: ReactNode, nota?: ReactNode, className = '') => (
        <div className={`mz-stat ${className}`}>
            <span className="muted small">{rotulo}</span>
            <strong className="mz-mid num">{valor}</strong>
            {nota && <span className="small muted">{nota}</span>}
        </div>
    )
    return (
        <div className="grid mz-duas">
            <ChartCard
                title="Progresso Super Meta anual"
                action={<Pill tone={a.meta_atingida ? 'ok' : 'warn'}>{pct(a.atingido_pct)} atingido</Pill>}
                footer={
                    <span className="small muted num">
                        Esperado = {compacto(a.meta)} × {pct(a.frac_ano_pct)} dos dias do ano
                    </span>
                }
            >
                <div className="mz-stats3">
                    {stat('Realizado (acumulado)', compacto(a.realizado_ytd))}
                    {stat('Meta anual', compacto(a.meta))}
                    {stat('Atingido', pct(a.atingido_pct), 'da Super Meta', 'tone-text-warn')}
                </div>
                <span className="mz-bar mz-bar-super" style={largura(a.atingido_pct)} aria-hidden="true" />
                <span className="small tone-text-warn">
                    {a.falta > 0
                        ? `Faltam ${compacto(a.falta)} (${pct(a.distancia_pct)} para a meta)`
                        : 'Super Meta atingida'}
                </span>
                <span className="mz-div" />
                <div className="mz-stats3">
                    {stat('Esperado até hoje', compacto(a.expectativa_ytd), `${pct(a.frac_ano_pct)} do ano`)}
                    {stat(
                        'Vs. esperado',
                        `${abaixo ? '↓' : '↑'} ${compacto(Math.abs(a.gap_ytd))}`,
                        a.gap_ytd_pct !== null ? `(${pct(a.gap_ytd_pct)})` : undefined,
                        abaixo ? 'tone-text-danger' : 'tone-text-ok',
                    )}
                    {stat(
                        'Projeção fim do ano',
                        compacto(proj.valor_projetado),
                        proj.excede_meta_pct !== null
                            ? `${proj.excede_meta_pct < 0 ? '↓' : '↑'} ${pct(Math.abs(proj.excede_meta_pct))} vs. Super Meta`
                            : undefined,
                    )}
                </div>
            </ChartCard>
            <ChartCard
                title="Ritmo diário necessário (ano)"
                action={
                    <Pill tone={insuficiente ? 'danger' : 'ok'}>
                        {insuficiente ? 'Ritmo insuficiente' : 'Ritmo suficiente'}
                    </Pill>
                }
                footer={
                    <div className="mz-row small">
                        <span>
                            Falta <strong className="num">{fmt.brl(r.falta_no_ano)}</strong> para a Super Meta anual
                        </span>
                        <Pill>{r.dias_restantes}d restantes no ano</Pill>
                    </div>
                }
            >
                <div className="mz-stats3">
                    {stat('Necessário/dia', compacto(r.necessario_por_dia))}
                    {stat('Necessário/mês', compacto(r.necessario_por_mes), '30 dias')}
                    {stat('Necessário/semestre', compacto(r.necessario_por_semestre), '180 dias')}
                </div>
                <span className="mz-div" />
                <div className="mz-stats3">
                    {stat(
                        'Atual/dia',
                        compacto(r.atual_por_dia_30d),
                        'média dos últimos 30 dias',
                        insuficiente ? 'tone-text-warn' : 'tone-text-ok',
                    )}
                    {stat('Atual/mês', compacto(r.atual_por_mes_30d), '30 dias')}
                    {stat('Atual/semestre', compacto(r.atual_por_semestre_30d), '180 dias')}
                </div>
            </ChartCard>
        </div>
    )
}

const STATUS_TOM: Record<Predicao['expectativa_hoje']['status'], Tone> = {
    acima: 'ok',
    no_ritmo: 'warn',
    abaixo: 'danger',
    sem_dados: 'neutral',
}

// 05 · Análise preditiva: o trimestre em curso contra o esperado até hoje, a projeção e o ritmo do trimestre.
function Preditiva({ p, trimestre, asOf }: { p: Predicao; trimestre: Trimestre; asOf: string }) {
    const e = p.expectativa_hoje
    const proj = p.projecao_fim_ano
    const r = p.ritmo_diario
    const tom = STATUS_TOM[e.status]
    const insuficiente = r.diferenca_diaria > 0
    const frase =
        e.status === 'sem_dados' ? (
            'Sem dados suficientes para a análise.'
        ) : (
            <>
                Em <strong>{dataBr(asOf)}</strong> ({trimestreNome(trimestre)}), o trimestre está{' '}
                {e.status === 'no_ritmo' ? (
                    <>
                        no ritmo esperado (diferença de <strong className="num">{fmt.brl(Math.abs(e.gap))}</strong>)
                    </>
                ) : (
                    <>
                        <strong className="num">{fmt.brl(Math.abs(e.gap))}</strong>{' '}
                        {e.status === 'acima' ? 'acima' : 'abaixo'} do esperado até hoje
                    </>
                )}{' '}
                (Super Meta × {pct(e.frac_dias_trimestre_pct)} dos dias).
            </>
        )
    const zonaProj = proj.zona_projetada as ZonaUI
    return (
        <div className="mz-stack">
            <section className={`card mz-alerta tone-${tom}`}>
                <p className="mz-alerta-texto">
                    <span className="mz-ponto" aria-hidden="true" /> {frase}
                </p>
                <div className="grid grid-stat grid-mini grid-mini-stack">
                    <MiniStat
                        label="Esperado até hoje"
                        icon="target"
                        tone="info"
                        value={fmt.brl(e.expectativa)}
                        below={
                            <span className="small muted num">
                                {compacto(e.meta_super_trimestre)} × {pct(e.frac_dias_trimestre_pct)} dos dias
                            </span>
                        }
                    />
                    <MiniStat
                        label="Realizado (trimestre)"
                        icon="dollar"
                        tone="accent"
                        value={fmt.brl(e.realizado)}
                        below={
                            <span className="small muted num">
                                {pct(e.meta_super_trimestre > 0 ? (e.realizado / e.meta_super_trimestre) * 100 : 0)} da
                                Super Meta
                            </span>
                        }
                    />
                    <MiniStat
                        label="Diferença (trimestre)"
                        icon={e.gap < 0 ? 'trend-down' : 'trend-up'}
                        tone={e.gap < 0 ? 'danger' : 'ok'}
                        value={<span className={`tone-text-${e.gap < 0 ? 'danger' : 'ok'}`}>{fmt.brl(e.gap)}</span>}
                        below={<DeltaPill value={e.gap_pct} suffix=" vs. esperado" plain />}
                    />
                    <MiniStat
                        label="Realizado (acumulado)"
                        icon="check-circle"
                        tone="neutral"
                        value={fmt.brl(p.expectativa_ytd.realizado)}
                        below={<DeltaPill value={p.expectativa_ytd.gap_pct} suffix=" vs. esperado no ano" plain />}
                    />
                </div>
            </section>
            <div className="grid mz-duas">
                <ChartCard
                    title="Projeção fim do ano"
                    footer={
                        proj.excede_meta_pct !== null && (
                            <span className={`small num tone-text-${proj.excede_meta_pct < 0 ? 'danger' : 'ok'}`}>
                                {proj.excede_meta_pct < 0 ? '↓' : '↑'} {pct(Math.abs(proj.excede_meta_pct))} vs. meta
                                Super ({compacto(proj.meta_referencia)})
                            </span>
                        )
                    }
                >
                    <div className="mz-proj">
                        <strong className="mz-big num">{compacto(proj.valor_projetado)}</strong>
                        <span className={`small ${zonaClasse(zonaProj)}`}>
                            Zona projetada: <strong className="z-text">{ZONA_FRASE[zonaProj] ?? zonaProj}</strong>
                        </span>
                    </div>
                    <span className="small muted">
                        O acumulado do ano no ritmo de hoje: realizado ÷ {pct(p.frac_ano_pct)} do ano decorrido.
                    </span>
                </ChartCard>
                <ChartCard
                    title={`Ritmo diário necessário (${trimestreNome(trimestre)})`}
                    action={
                        <Pill tone={insuficiente ? 'danger' : 'ok'}>
                            {insuficiente ? 'Ritmo insuficiente' : 'Ritmo suficiente'}
                        </Pill>
                    }
                    footer={
                        <span className="small">
                            Falta <strong className="num">{fmt.brl(r.falta_no_trimestre)}</strong> para a Super Meta do
                            trimestre atual ({r.dias_restantes}d restantes)
                        </span>
                    }
                >
                    <div className="mz-stats2">
                        <div className="mz-stat">
                            <span className="muted small">Necessário/dia</span>
                            <strong className="mz-mid num">{compacto(r.necessario_por_dia)}</strong>
                        </div>
                        <div className="mz-stat">
                            <span className="muted small">Atual (últimos 30 dias)</span>
                            <strong className={`mz-mid num tone-text-${insuficiente ? 'warn' : 'ok'}`}>
                                {compacto(r.atual_por_dia_30d)}
                            </strong>
                        </div>
                    </div>
                </ChartCard>
            </div>
        </div>
    )
}
