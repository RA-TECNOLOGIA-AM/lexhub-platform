import { useMemo, useState } from 'react'
import { BarList } from '../../../components/charts/BarList.tsx'
import { ChartCard, ChartEmpty } from '../../../components/charts/ChartCard.tsx'
import { LineChart } from '../../../components/charts/LineChart.tsx'
import { FilterPicker } from '../../../components/dashboard/FilterDialog.tsx'
import { DashSection } from '../../../components/dashboard/DashSection.tsx'
import { HeroStat, InfoTip, MiniStat } from '../../../components/dashboard/StatCard.tsx'
import { Icon, type IconName } from '../../../components/ui/Icon.tsx'
import { Segmented } from '../../../components/ui/Segmented.tsx'
import { fmt } from '../../../lib/format.ts'
import type { ContentProps } from '../types.ts'
import {
    MIN_N,
    MODELOS,
    RESULTADOS_1G,
    SELECAO_VAZIA,
    alternarPilula,
    calcular,
    curva,
    dec,
    disponiveis,
    lerVitoria,
    nModelo,
    pct,
    pct1,
    pctJa,
    taxaProcedencia,
    type Calculo,
    type Ponderacao,
    type PrevisaoResponse,
    type Selecao,
} from './previsao.ts'

const COR_CASO = 'var(--chart-1)'
const COR_MATERIA = 'var(--chart-3)'

type CampoLista = 'materias' | 'comarcas' | 'competencias' | 'tipos'

// Previsão Individualizada (TCC, Fase 6): a página da v1 no layout da V2. O formulário (seção 01) é só da página: cada
// mudança recalcula no navegador a mistura do XGBoost-AFT, sem buscar o bundle de novo. O bundle já vem só com o
// escritório da unidade (NG vê NG, LA vê LA), então não há mais as pílulas de escritório da v1.
export function PrevisaoContent({ data }: ContentProps<PrevisaoResponse>) {
    const [sel, setSel] = useState<Selecao>(SELECAO_VAZIA)
    const disp = useMemo(() => disponiveis(data), [data])
    const c = useMemo(() => calcular(data, sel), [data, sel])
    const escritorio = data.opcoes.escritorios.join(' e ') || 'da unidade'
    const mudou = JSON.stringify(sel) !== JSON.stringify(SELECAO_VAZIA)

    const listas: { campo: CampoLista; label: string; icon: IconName; opcoes: string[]; dica: string }[] = [
        { campo: 'materias', label: 'Matéria', icon: 'book', opcoes: disp.materias, dica: 'Múltipla escolha' },
        { campo: 'comarcas', label: 'Comarca', icon: 'pin', opcoes: disp.comarcas, dica: 'Múltipla escolha' },
        {
            campo: 'competencias',
            label: 'Competência',
            icon: 'building',
            opcoes: disp.competencias,
            dica: 'Vazio = Todas (ponderado)',
        },
        {
            campo: 'tipos',
            label: 'Tipo de ação',
            icon: 'scale',
            opcoes: data.opcoes.tiposAcao,
            dica: 'Múltipla escolha',
        },
    ]
    const [aberto, setAberto] = useState<CampoLista | null>(null)
    const alternarLista = (campo: CampoLista, v: string) =>
        setSel((s) => ({ ...s, [campo]: s[campo].includes(v) ? s[campo].filter((x) => x !== v) : [...s[campo], v] }))

    return (
        <div className="dsecs">
            <div className="card sv-topo">
                <p className="muted small">
                    <Icon name="info" size={13} /> Pesquisa (TCC, Fase 6):{' '}
                    <strong>{data.modelo ?? 'XGBoost-AFT'}</strong>, treinado com {fmt.int(data.n_treino ?? 0)}{' '}
                    processos do LexFlow (foto de {data.gerado_em ?? '—'}). As previsões são pré-calculadas e combinadas
                    no seu navegador, só com o histórico do escritório {escritorio}. Generalização de padrões passados,
                    não análise de mérito de um caso específico — não é orientação jurídica.
                </p>
            </div>

            <DashSection
                index={1}
                eyebrow="Simulação"
                title="Previsão para este caso"
                subtitle="Escolha as características do processo; a previsão é recalculada na hora. Vazio = todas (ponderadas pelo histórico)."
                action={
                    <button
                        type="button"
                        className="btn btn-ghost"
                        disabled={!mudou}
                        onClick={() => setSel(SELECAO_VAZIA)}
                        title="Restaurar filtros"
                    >
                        <Icon name="undo" size={15} /> Restaurar
                    </button>
                }
            >
                <div className="pv-grade">
                    <aside className="card pv-form">
                        <div className="pv-form-h">
                            <span className="pv-eyebrow">Dados do processo</span>
                            <strong>Características do caso</strong>
                        </div>
                        {listas.map((l) => (
                            <div key={l.campo} className="pv-campo">
                                <span className="pv-rot">
                                    {l.label} <span className="muted">{l.dica}</span>
                                </span>
                                <FilterPicker
                                    field={{
                                        label: `Todas: ${l.label.toLowerCase()}`,
                                        icon: l.icon,
                                        options: l.opcoes.map((v) => ({ value: v, label: v })),
                                    }}
                                    chosen={sel[l.campo]}
                                    open={aberto === l.campo}
                                    onOpenChange={(o) => setAberto(o ? l.campo : null)}
                                    onToggle={(v) => alternarLista(l.campo, v)}
                                    onClear={() => setSel((s) => ({ ...s, [l.campo]: [] }))}
                                />
                                {sel[l.campo].length > 1 && (
                                    <div className="ex-chips pv-chips">
                                        {sel[l.campo].map((v) => (
                                            <span key={v} className="chip">
                                                {v}
                                                <button
                                                    type="button"
                                                    aria-label={`Remover ${v}`}
                                                    onClick={() => alternarLista(l.campo, v)}
                                                >
                                                    <Icon name="close" size={12} />
                                                </button>
                                            </span>
                                        ))}
                                    </div>
                                )}
                            </div>
                        ))}
                        <Pilulas
                            rotulo="Valor de causa"
                            todos="Todos"
                            opcoes={data.opcoes.faixasValor}
                            sel={sel.faixas}
                            onChange={(faixas) => setSel((s) => ({ ...s, faixas }))}
                        />
                        <div className="pv-1g">
                            <Pilulas
                                rotulo="Resultado do 1G"
                                selo="Se já houver"
                                todos="Todos / ainda não há"
                                opcoes={RESULTADOS_1G}
                                sel={sel.resultados1g}
                                onChange={(resultados1g) => setSel((s) => ({ ...s, resultados1g }))}
                            />
                        </div>
                        <div className="pv-campo">
                            <span className="pv-rot">
                                Ponderação <span className="muted">Como combinar várias opções</span>
                            </span>
                            <Segmented<Ponderacao>
                                label="Ponderação"
                                value={sel.ponderacao}
                                onChange={(ponderacao) => setSel((s) => ({ ...s, ponderacao }))}
                                options={[
                                    { value: 'historico', label: 'Pelo histórico' },
                                    { value: 'igual', label: 'Igual' },
                                ]}
                            />
                        </div>
                        <p className="muted small pv-nota">
                            O modelo distingue as {nModelo(data, 'materia')} matérias, {nModelo(data, 'comarca')}{' '}
                            comarcas e {nModelo(data, 'competencia')} competências mais frequentes; as demais
                            compartilham a previsão do grupo "outras", mas entram com o peso da categoria real.
                        </p>
                    </aside>

                    <div className="pv-res">
                        {c.nTreino === 0 ? (
                            <p className="sv-alerta">
                                <Icon name="alert" size={14} />{' '}
                                <span>
                                    <strong>Sem processos no histórico com essas características.</strong> Nenhum
                                    processo do {escritorio} com essa combinação de matéria, comarca, competência, tipo
                                    de ação e faixa de valor foi encontrado no histórico de treino — sem base, a página
                                    não mostra previsão. Amplie a seleção (mais matérias/comarcas/competências, outra
                                    faixa de valor ou outro tipo de ação).
                                </span>
                            </p>
                        ) : (
                            <Resultado data={data} c={c} sel={sel} escritorio={escritorio} />
                        )}
                    </div>
                </div>
            </DashSection>

            <Acuracia data={data} />

            <p className="muted small pv-rodape">
                Protótipo de pesquisa (Fase 6 do TCC) — previsões reais do modelo pré-calculadas; expor isso como
                recurso operacional do LexHub (fora do contexto de pesquisa) seria uma decisão de produto separada,
                ainda não tomada.
            </p>
        </div>
    )
}

function Pilulas<T extends string>({
    rotulo,
    selo,
    todos,
    opcoes,
    sel,
    onChange,
}: {
    rotulo: string
    selo?: string
    todos: string
    opcoes: readonly T[]
    sel: T[]
    onChange: (v: T[]) => void
}) {
    return (
        <div className="pv-campo">
            <span className="pv-rot">
                {rotulo} {selo && <span className="pv-selo">{selo}</span>}
            </span>
            <div className="pv-pilulas" role="group" aria-label={rotulo}>
                <button type="button" aria-pressed={sel.length === 0} onClick={() => onChange([])}>
                    {todos}
                </button>
                {opcoes.map((o) => (
                    <button
                        key={o}
                        type="button"
                        aria-pressed={sel.includes(o)}
                        onClick={() => onChange(alternarPilula(sel, o, opcoes))}
                    >
                        {o}
                    </button>
                ))}
            </div>
        </div>
    )
}

function Resultado({
    data,
    c,
    sel,
    escritorio,
}: {
    data: PrevisaoResponse
    c: Calculo
    sel: Selecao
    escritorio: string
}) {
    const [verCaso, setVerCaso] = useState(true)
    const [verMateria, setVerMateria] = useState(true)
    const k = useMemo(() => curva(c), [c])
    const { j1, f1, j2, f2 } = c.historico
    const amostra = (fav: number, julg: number, rotulo: string) =>
        julg
            ? `${fmt.int(fav)} de ${fmt.int(julg)} ${rotulo}${julg < MIN_N ? ' — amostra pequena' : ''}`
            : `Nenhum caso com ${rotulo} no histórico`
    const nMaterias = sel.materias.length || data.opcoes.materias.length
    const rotuloMateria =
        sel.materias.length === 1
            ? 'da matéria'
            : sel.materias.length === 0
              ? 'de todas as matérias'
              : `das ${nMaterias} matérias`
    const auc1g = data.metricas_procedencia?.['1G']?.auc_xgb
    const m2g = data.metricas_procedencia_2g
    const xgb2g = m2g?.modelo === 'xgboost'
    const auc2g = xgb2g ? m2g?.auc_xgb : m2g?.auc_logistica
    const maisRapido = c.delta !== null && c.delta < 0
    const comparativo =
        c.delta === null ? '—' : c.delta === 0 ? 'igual' : `${c.delta > 0 ? '+' : ''}${fmt.int(c.delta)}d`

    const ajudaMediana =
        'Mediana prevista pelo XGBoost-AFT (Fases 4-5): com a escala log-normal fixa, é o tempo com 50% de chance de o processo já ter tido o desfecho (mérito ou acordo). O modelo considera a época da distribuição (mediana de ~720 dias para os distribuídos em 2022, ~190 em 2025) e usa o ritmo mais recente; no backtest com até ~2 anos bateu nas faixas típicas e tende a superestimar os casos mais lentos. "Metade dos casos entre" = P25–P75 previsto: 1 em 4 termina antes do primeiro número e 1 em 4 depois do segundo (no backtest a faixa conteve 55–69% dos processos reais).'
    const ajuda1g = `Chance prevista de a sentença de mérito no 1º grau ser procedente ou parcialmente procedente com proveito econômico — dado que haja sentença de mérito. Classificador XGBoost com as mesmas características e o split temporal do TCC${auc1g !== undefined ? ` (AUC ${dec(auc1g, 2)} no teste; 0,5 = acaso)` : ''}. Tende a superestimar os perfis mais favoráveis.${j1 ? ` Histórico com essas características: ${taxaProcedencia(f1, j1)} (${amostra(f1, j1, 'sentenças')}).` : ''} Acordo pré-sentença: chance prevista de fechar acordo antes de qualquer sentença (entre os que se resolvem no 1º grau). O nível de acordos muda com a época (pico de ~7% no fim de 2024, perto de 1% hoje) e no teste mais recente a taxa real ficou abaixo do previsto — leia como teto provável.${c.historicoPre ? ` Histórico: ${pct1(c.historicoPre.taxa)} (${fmt.int(c.historicoPre.a)} de ${fmt.int(c.historicoPre.n)}).` : ''}`
    const ajuda2g = `Chance prevista de o acórdão de mérito no 2º grau ser procedente ou parcialmente procedente com proveito econômico — dado que haja acórdão de mérito (sentença anulada fica fora). ${xgb2g ? 'XGBoost' : 'Regressão logística'} (escolhido por validação temporal, sem olhar o teste final) com as mesmas características mais o resultado do 1G, a variável mais forte. Sem resultado do 1G informado, a chance combina os cenários pela procedência 1G prevista.${c.c2g ? ` Se o 1G for procedente: ${pct(c.c2g.seProcedente)}; improcedente: ${pct(c.c2g.seImprocedente)}; extinto: ${pct(c.c2g.seExtinto)}.` : ''}${auc2g !== undefined ? ` Validação: AUC ${dec(auc2g, 2)} no teste.` : ''} Acordo pós-sentença: chance prevista de, depois da sentença e antes do acórdão, fechar acordo — segue o mesmo cenário do resultado do 1G.`

    return (
        <>
            <p className="muted small pv-base">
                Base: <strong>{fmt.int(c.nTreino)}</strong> {c.nTreino === 1 ? 'processo' : 'processos'} de treino do{' '}
                {escritorio} com essas mesmas características (matéria, comarca, competência, tipo de ação e faixa de
                valor){c.nTreino < MIN_N ? ' — base pequena, leia a previsão com cautela' : ''}.
            </p>
            <div className="grid grid-stat pv-kpis">
                <HeroStat
                    label="Mediana prevista"
                    icon="clock"
                    tone="accent"
                    hint={ajudaMediana}
                    value={c.diasPrevisto === null ? '—' : `${fmt.int(c.diasPrevisto)} dias`}
                    footer={
                        c.faixa && (
                            <>
                                <span className="small">
                                    Metade dos casos entre <strong className="num">{fmt.int(c.faixa.de)}</strong> e{' '}
                                    <strong className="num">{fmt.int(c.faixa.ate)} dias</strong>
                                </span>
                                <FaixaBarra p25={c.faixa.de} p50={c.diasPrevisto!} p75={c.faixa.ate} />
                            </>
                        )
                    }
                />
                <HeroStat
                    label="Procedência 1G"
                    icon="target"
                    tone="info"
                    hint={ajuda1g}
                    value={c.p1g === null ? '—' : pct(c.p1g)}
                    aside={<span className="muted small">prevista</span>}
                    footer={
                        <>
                            <span className="small">
                                Acordo pré-sentença:{' '}
                                <strong className="num tone-text-warn">
                                    {c.acordoPre === null ? '—' : pct1(c.acordoPre)}
                                </strong>
                            </span>
                            {c.p1g !== null && <ProbBarra p={c.p1g} acordo={c.acordoPre} cor="var(--c-info)" />}
                        </>
                    }
                />
                <HeroStat
                    label="Procedência 2G"
                    icon="scale"
                    tone="neutral"
                    hint={ajuda2g}
                    value={c.valor2g !== null ? pct(c.valor2g) : taxaProcedencia(f2, j2)}
                    aside={<span className="muted small">{c.valor2g !== null ? 'prevista' : 'histórico'}</span>}
                    footer={
                        <>
                            <span className="small">
                                Acordo pós-sentença:{' '}
                                <strong className="num tone-text-warn">
                                    {c.acordoPos === null ? '—' : pct1(c.acordoPos)}
                                </strong>
                            </span>
                            {c.valor2g !== null && (
                                <ProbBarra p={c.valor2g} acordo={c.acordoPos} cor="var(--chart-5)" />
                            )}
                        </>
                    }
                />
                <HeroStat
                    label="Comparado à matéria"
                    icon={maisRapido ? 'trend-down' : 'trend-up'}
                    tone={c.delta === null ? 'neutral' : maisRapido ? 'ok' : 'danger'}
                    outline={c.delta !== null && c.delta !== 0}
                    hint="Mediana de duração da(s) matéria(s) selecionada(s), estimada por Kaplan-Meier no conjunto de treino (a matéria inteira: não filtra comarca, competência, tipo nem faixa), comparada à mediana prevista para este caso pelo XGBoost-AFT. O percentual compara a diferença com a mediana da matéria."
                    value={
                        <span className={c.delta ? (maisRapido ? 'tone-text-ok' : 'tone-text-danger') : undefined}>
                            {comparativo}
                        </span>
                    }
                    footer={
                        <>
                            <span className="small">
                                Mediana {rotuloMateria}:{' '}
                                <strong className="num">
                                    {c.medianaMateria === null ? '—' : `${fmt.int(c.medianaMateria)}d`}
                                </strong>
                            </span>
                            {c.delta !== null && c.delta !== 0 && c.medianaMateria ? (
                                <span className={`small ${maisRapido ? 'tone-text-ok' : 'tone-text-danger'}`}>
                                    {pctJa((100 * Math.abs(c.delta)) / c.medianaMateria)}{' '}
                                    {maisRapido ? 'mais rápido' : 'mais lento'} que a mediana da matéria
                                </span>
                            ) : null}
                        </>
                    }
                />
            </div>

            {c.diasPrevisto !== null && (
                <ChartCard
                    className="ex-mt"
                    title="Curva de sobrevivência estimada"
                    subtitle={`Probabilidade de o processo seguir em tramitação ao longo do tempo (0 a ${fmt.int(k.dias.at(-1) ?? 0)} dias)`}
                    action={
                        <InfoTip text='Eixo X em dias desde a distribuição; eixo Y em % de processos parecidos ainda em tramitação. "Este caso" usa a fórmula fechada da AFT log-normal (a mesma validada na Fase 5), combinando as combinações selecionadas. "Mediana da matéria" é a mesma forma de curva centrada na mediana Kaplan-Meier da(s) matéria(s).' />
                    }
                    footer={
                        <span className="small">
                            Linha tracejada <strong>P50 (50%)</strong>: ponto em que metade dos casos já encerrou ·
                            Cruzamento P50: <strong className="num">{fmt.int(c.diasPrevisto)}d</strong>
                            {c.medianaMateria !== null && (
                                <>
                                    {' '}
                                    vs <strong className="num">{fmt.int(c.medianaMateria)}d</strong> da matéria
                                </>
                            )}
                        </span>
                    }
                >
                    <div className="sv-series">
                        <button type="button" aria-pressed={verCaso} onClick={() => setVerCaso((v) => !v)}>
                            <i style={{ background: COR_CASO }} /> Este caso
                        </button>
                        {c.medianaMateria !== null && (
                            <button type="button" aria-pressed={verMateria} onClick={() => setVerMateria((v) => !v)}>
                                <i style={{ background: COR_MATERIA }} /> Mediana da matéria
                            </button>
                        )}
                    </div>
                    <LineChart
                        height={340}
                        area
                        labels={k.dias.map((d) => `${fmt.int(d)}d`)}
                        format={(v) => `${fmt.dec1(v)}%`}
                        reference={{ value: 50, label: 'P50 (50%)' }}
                        tooltip={{ heading: 'Dias', title: (i) => `${fmt.int(k.dias[i])} dias` }}
                        series={[
                            ...(c.medianaMateria !== null && verMateria
                                ? [{ label: 'Mediana da matéria', color: COR_MATERIA, values: k.materia }]
                                : []),
                            ...(verCaso ? [{ label: 'Este caso', color: COR_CASO, values: k.caso }] : []),
                        ]}
                    />
                </ChartCard>
            )}
        </>
    )
}

// P25 – P50 – P75 numa régua (máximo = 1,6 × P75), como a v1.
function FaixaBarra({ p25, p50, p75 }: { p25: number; p50: number; p75: number }) {
    const max = Math.max(p75 * 1.6, 1)
    const pos = (v: number) => Math.min(100, (100 * v) / max)
    return (
        <span className="pv-faixa" aria-hidden="true">
            <span className="pv-faixa-trilho">
                <span className="pv-faixa-seg" style={{ left: `${pos(p25)}%`, width: `${pos(p75) - pos(p25)}%` }} />
                <span className="pv-faixa-p50" style={{ left: `${pos(p50)}%` }} />
            </span>
            <span className="pv-faixa-leg">
                <span>P25</span>
                <span className="pv-faixa-m" style={{ left: `${pos(p50)}%` }}>
                    P50
                </span>
                <span>P75</span>
            </span>
        </span>
    )
}

// A chance prevista e, ao lado, o acordo (âmbar), como a v1.
function ProbBarra({ p, acordo, cor }: { p: number; acordo: number | null; cor: string }) {
    return (
        <span className="pv-prob" aria-hidden="true">
            <span style={{ width: `${Math.max(1, 100 * p)}%`, background: cor }} />
            {acordo !== null && <span className="pv-prob-ac" style={{ width: `${Math.max(1.5, 100 * acordo)}%` }} />}
        </span>
    )
}

function Acuracia({ data }: { data: PrevisaoResponse }) {
    const m = data.metricas ?? {}
    const v = m.vitorias_pareadas_bootstrap ?? {}
    const forte = (v.xgb_vs_cox_pct ?? 0) >= 95 && (v.xgb_vs_rsf_pct ?? 0) >= 95
    const fmtPct = (x: number | undefined) => (x === undefined ? '—' : pctJa(x))
    const fmt3 = (x: number) => dec(x, 3)
    return (
        <DashSection
            index={2}
            eyebrow="Acurácia do modelo"
            title="Cox vs. RSF vs. XGBoost-AFT (Fases 4-5)"
            subtitle="Validado no conjunto de teste (split temporal, nunca visto no treino) — C-index com intervalo de confiança por bootstrap, Brier Score integrado e calibração em 90 dias. Métricas do estudo inteiro (NG e LA)."
        >
            <div className="grid grid-stat grid-stat-3">
                {MODELOS.map(({ k, label }) => {
                    const ci = m.cindex?.[k]
                    return (
                        <MiniStat
                            key={k}
                            label={label}
                            icon="target"
                            tone={k === 'XGBoost_AFT' ? 'accent' : 'neutral'}
                            value={ci?.teste === undefined ? '—' : dec(ci.teste, 4)}
                            extra={<span className="muted small">C-index (teste)</span>}
                            hint={
                                ci?.ic95_min !== undefined && ci.ic95_max !== undefined
                                    ? `IC 95% por bootstrap (500 reamostragens do teste): [${dec(ci.ic95_min, 4)} – ${dec(ci.ic95_max, 4)}].`
                                    : undefined
                            }
                            below={
                                ci?.ic95_min !== undefined && ci.ic95_max !== undefined ? (
                                    <span className="muted small num">
                                        IC 95%: {dec(ci.ic95_min, 4)} – {dec(ci.ic95_max, 4)}
                                    </span>
                                ) : undefined
                            }
                        />
                    )
                })}
            </div>
            <p className="sv-alerta pv-sig">
                <Icon name="info" size={14} />{' '}
                <span>
                    <strong>Significância da diferença (bootstrap pareado, 500 reamostragens).</strong> XGBoost-AFT
                    venceu o Cox em {fmtPct(v.xgb_vs_cox_pct)} das reamostragens ({lerVitoria(v.xgb_vs_cox_pct, 'Cox')})
                    e a RSF em {fmtPct(v.xgb_vs_rsf_pct)} ({lerVitoria(v.xgb_vs_rsf_pct, 'RSF')}). A RSF venceu o Cox em{' '}
                    {fmtPct(v.rsf_vs_cox_pct)} ({lerVitoria(v.rsf_vs_cox_pct, 'Cox')}).{' '}
                    {forte
                        ? 'O XGBoost-AFT é o melhor em discriminação e também o mais bem calibrado — é o único cuja probabilidade prevista fica perto da observada (Brier e gráfico de calibração abaixo).'
                        : 'Na discriminação os modelos ficam próximos; o que justifica o XGBoost-AFT na previsão é a calibração — é o único cuja probabilidade prevista fica perto da observada (Brier e gráfico de calibração abaixo).'}
                </span>
            </p>
            <div className="grid ex-duo ex-mt">
                <ChartCard title="C-index no teste" subtitle="Maior = melhor discriminação (0,5 = acaso)">
                    <BarList
                        format={fmt3}
                        items={MODELOS.map(({ k, label }) => ({ name: label, value: m.cindex?.[k]?.teste ?? 0 }))}
                    />
                </ChartCard>
                <ChartCard
                    title="Brier Score integrado"
                    subtitle="Menor = melhor calibrado · horizonte de 15 a 240 dias do teste; um 'chute constante' de 50% dá ≈ 0,25"
                >
                    <BarList
                        format={fmt3}
                        items={MODELOS.map(({ k, label }) => ({
                            name: label,
                            value: m.brier_score_integrado?.[k] ?? 0,
                        }))}
                    />
                </ChartCard>
            </div>
            <h3 className="pv-sub">Calibração em 90 dias (previsto vs. observado por quartil de risco)</h3>
            <p className="muted small">
                % ainda em tramitação aos 90 dias, prevista pelo modelo e observada por Kaplan-Meier, em cada quartil de
                risco previsto do teste. Linhas próximas = modelo bem calibrado.
            </p>
            <div className="grid tk-tres">
                {MODELOS.map(({ k, label }) => {
                    const linhas = [1, 2, 3, 4].map((q) =>
                        (m.calibracao_90_dias ?? []).find((r) => r.modelo === k && r.quartil === q),
                    )
                    const r1 = (x: number | undefined) => (x === undefined ? null : Math.round(x * 1000) / 10)
                    return (
                        <ChartCard key={k} title={label} subtitle="Quartis de risco previsto no teste">
                            {linhas.every((l) => !l) ? (
                                <ChartEmpty>Sem calibração no bundle.</ChartEmpty>
                            ) : (
                                <LineChart
                                    height={260}
                                    legend
                                    labels={['Q1', 'Q2', 'Q3', 'Q4']}
                                    format={(x) => `${fmt.dec1(x)}%`}
                                    series={[
                                        {
                                            label: 'Previsto',
                                            color: COR_CASO,
                                            values: linhas.map((l) => r1(l?.previsto)),
                                        },
                                        {
                                            label: 'Observado',
                                            color: COR_MATERIA,
                                            values: linhas.map((l) => r1(l?.observado)),
                                        },
                                    ]}
                                />
                            )}
                        </ChartCard>
                    )
                })}
            </div>
        </DashSection>
    )
}
