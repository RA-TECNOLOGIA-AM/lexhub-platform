import { useMemo, useState } from 'react'
import { BarList } from '../../../components/charts/BarList.tsx'
import { ChartCard, ChartEmpty } from '../../../components/charts/ChartCard.tsx'
import { LineChart } from '../../../components/charts/LineChart.tsx'
import { MapaComarcas } from '../../../components/charts/MapaComarcas.tsx'
import { DashSection } from '../../../components/dashboard/DashSection.tsx'
import { MiniStat } from '../../../components/dashboard/StatCard.tsx'
import { Icon } from '../../../components/ui/Icon.tsx'
import { fmt } from '../../../lib/format.ts'
import type { ContentProps } from '../types.ts'
import type { ResultadoLogRank } from './kaplanMeier.ts'
import { Fluxo } from './Fluxo.tsx'
import {
    AMOSTRA_PEQUENA,
    CAMPOS,
    DIAS_GRADE,
    ROTULO_CAMPO,
    SELECAO_VAZIA,
    agruparPorVolume,
    alternar,
    aplicarFiltros,
    curvaPct,
    curvasPor,
    decodificar,
    formatarPValor,
    obsAcordao,
    obsEstagio1,
    obsEstagio2,
    obsSentenca,
    ranking,
    resumo,
    type Campo,
    type Ranking,
    type Selecao,
    type SobrevivenciaResponse,
} from './sobrevivencia.ts'

const CORES = ['var(--chart-1)', 'var(--chart-3)', 'var(--chart-4)', 'var(--chart-5)', 'var(--pie-7)', 'var(--danger)']
const pctTexto = (v: number | null) => (v === null ? '—' : `${fmt.dec1(v)}%`)
const ROTULOS_GRADE = DIAS_GRADE.map(String)

// Sobrevivência Processual (TCC, NG + LA/AM): as seções da página da v1 no layout da V2. Todo o cálculo é no navegador
// (sobrevivencia.ts + kaplanMeier.ts); os filtros (cliques nos gráficos) ficam na própria página, sem buscar a coorte de
// novo. A coorte já vem só com o escritório da unidade (NG vê NG, LA vê LA), então não há mais o filtro de escritório.
export function SobrevivenciaContent({ data }: ContentProps<SobrevivenciaResponse>) {
    const todas = useMemo(() => decodificar(data), [data])
    const [selecao, setSelecao] = useState<Selecao>(SELECAO_VAZIA)
    const base = todas
    const filtradas = useMemo(() => aplicarFiltros(base, selecao), [base, selecao])
    const sem = (c: Campo) => aplicarFiltros(base, selecao, c)
    const r = useMemo(() => resumo(filtradas), [filtradas])
    const escolher = (c: Campo) => (nome: string) => setSelecao((s) => alternar(s, c, nome))
    const etiquetas = CAMPOS.flatMap((c) => selecao[c].map((v) => ({ c, v })))

    // Ranking do Estágio 1 de uma dimensão, sem o filtro dela (top 8; a matéria vai sem limite, como a v1).
    const rk = (c: Campo) => ranking(agruparPorVolume(sem(c), c), obsEstagio1)
    const rTipo = rk('tipoAcao')
    const rMateria = ranking(agruparPorVolume(sem('materia'), 'materia', undefined, Infinity), obsEstagio1)
    const rCompetencia = rk('competencia')
    const rComarca = rk('comarca')
    const e2 = filtradas.filter((l) => l.tipoEvento2 !== null)
    const rPagamento = ranking(
        agruparPorVolume(
            sem('materia').filter((l) => l.tipoEvento2 !== null),
            'materia',
        ),
        obsEstagio2,
    )

    return (
        <div className="dsecs">
            <div className="card sv-topo">
                <div className="sv-topo-linha">
                    {etiquetas.length > 0 && (
                        <div className="ex-chips">
                            {etiquetas.map(({ c, v }) => (
                                <span key={`${c}:${v}`} className="chip" title={`${ROTULO_CAMPO[c]}: ${v}`}>
                                    {ROTULO_CAMPO[c]}: {v}
                                    <button
                                        type="button"
                                        aria-label={`Tirar o filtro ${ROTULO_CAMPO[c]}: ${v}`}
                                        onClick={() => escolher(c)(v)}
                                    >
                                        <Icon name="close" size={12} />
                                    </button>
                                </span>
                            ))}
                            <button type="button" className="linkbtn muted" onClick={() => setSelecao(SELECAO_VAZIA)}>
                                Limpar filtros
                            </button>
                        </div>
                    )}
                </div>
                <p className="muted small">
                    <Icon name="info" size={13} /> Dado de pesquisa (coorte do TCC do escritório{' '}
                    {(data.escritorio_dict ?? []).join(', ') || 'da unidade'}, dado de {data.gerado_em ?? '—'}),
                    calculado no seu navegador: as curvas de Kaplan-Meier são recalculadas a cada filtro. A coorte não
                    depende do período do calendário. Clique nos gráficos para filtrar a página (dá para marcar vários).
                </p>
                {r.coorte > 0 && r.coorte < AMOSTRA_PEQUENA && (
                    <p className="sv-alerta">
                        <Icon name="alert" size={14} /> Este recorte tem apenas {fmt.int(r.coorte)} processos: medianas
                        e rankings podem ser instáveis e pouco representativos.
                    </p>
                )}
            </div>

            <DashSection
                index={1}
                eyebrow="Visão geral"
                title="Fluxo do recorte atual"
                subtitle="Distribuição → mérito/acordo (Estágio 1, com sentença e acórdão separados) → pagamento (Estágio 2)."
            >
                <Fluxo r={r} />
                <details className="sv-notas ex-mt">
                    <summary>Notas metodológicas e regras de cálculo das bases</summary>
                    <ul>
                        <li>
                            <strong>Mediana geral.</strong> Kaplan-Meier da distribuição (t = 0) até o primeiro desfecho
                            do Estágio 1, qualquer um; "Não atingida" quando a curva não cruza 50%.
                        </li>
                        <li>
                            <strong>Acordo pré e pós.</strong> % sobre a coorte inteira (por isso números pequenos). Pré
                            = antes da 1ª decisão de mérito; pós = depois, em recurso (2G) ou na execução. Mediana =
                            tempo da distribuição ao acordo, sem censura.
                        </li>
                        <li>
                            <strong>Sentença e acórdão.</strong> A mediana conta qualquer desfecho. Favorável,
                            improcedente e extinção são % de quem já foi julgado naquela instância e não somam com o
                            "Mérito favorável c/ proveito" da coorte (um processo pode ter sentença desfavorável e
                            acórdão favorável).
                        </li>
                        <li>
                            <strong>O que segue.</strong> Só acordo e mérito favorável com proveito entram no Estágio 2;
                            a taxa de pagamento é a parcela dos elegíveis já paga.
                        </li>
                    </ul>
                </details>
            </DashSection>

            <DashSection
                index={2}
                eyebrow="Curvas de sobrevivência"
                title="Probabilidade de ainda estar em tramitação"
                subtitle="Kaplan-Meier com os filtros da página: eixo X em dias desde a distribuição (0 a 1.800), eixo Y em % ainda sem o desfecho."
            >
                <ChartCard title="Curva geral" subtitle="Até o 1º desfecho do Estágio 1 (mérito ou acordo)">
                    <Curvas
                        series={[{ label: 'Coorte', valores: curvaPct(obsEstagio1(filtradas)) }]}
                        vazio={filtradas.length === 0}
                    />
                </ChartCard>
                <div className="grid ex-duo ex-mt">
                    <ChartCard
                        title="Até a sentença (1G)"
                        subtitle="% que ainda não teve sentença de 1º grau (procedente ou não)"
                    >
                        <Curvas
                            series={[{ label: 'Sem sentença', valores: curvaPct(obsSentenca(filtradas)) }]}
                            vazio={obsSentenca(filtradas).length === 0}
                        />
                    </ChartCard>
                    <ChartCard
                        title="Até o acórdão de mérito (2G)"
                        subtitle="% que ainda não teve acórdão de mérito (procedente ou não)"
                    >
                        <Curvas
                            series={[{ label: 'Sem acórdão', valores: curvaPct(obsAcordao(filtradas)) }]}
                            vazio={obsAcordao(filtradas).length === 0}
                        />
                    </ChartCard>
                </div>
                <div className="grid ex-duo ex-mt">
                    <Comparativa titulo="Por matéria" campo="materia" linhas={sem('materia')} />
                    <Comparativa titulo="Por competência" campo="competencia" linhas={sem('competencia')} />
                </div>
                <div className="ex-mt">
                    <Comparativa titulo="Por comarca" campo="comarca" linhas={sem('comarca')} />
                </div>
            </DashSection>

            <DashSection
                index={3}
                eyebrow="Gargalos"
                title="Ranking de mediana de dias até o desfecho"
                subtitle="Maior mediana = mais lento (só categorias com pelo menos 30 processos). Clique para filtrar a página; o log-rank diz se a diferença é estatística."
            >
                <div className="grid tk-tres">
                    <RankingCard
                        titulo="Por tipo de ação"
                        r={rTipo}
                        selecionados={selecao.tipoAcao}
                        onSelect={escolher('tipoAcao')}
                    />
                    <RankingCard
                        titulo="Por matéria"
                        r={rMateria}
                        selecionados={selecao.materia}
                        onSelect={escolher('materia')}
                    />
                    <RankingCard
                        titulo="Por competência"
                        r={rCompetencia}
                        selecionados={selecao.competencia}
                        onSelect={escolher('competencia')}
                    />
                </div>
                <ChartCard
                    className="ex-mt"
                    title="Por comarca"
                    subtitle="Mediana de dias até o desfecho nas 8 comarcas de maior volume (com pelo menos 30 processos) · clique num município para filtrar"
                    footer={<LogRank titulo="Comarca" r={rComarca.logRank} />}
                >
                    {rComarca.itens.length === 0 ? (
                        <ChartEmpty>Amostra insuficiente nesse recorte para este ranking.</ChartEmpty>
                    ) : (
                        <MapaComarcas
                            quantidade={rComarca.itens.map((i) => ({
                                name: i.name,
                                value: i.value,
                                uf: 'AM',
                                tempoMedio: null,
                            }))}
                            valor={[]}
                            comarcas={data.comarca_dict ?? []}
                            selected={selecao.comarca}
                            onSelect={escolher('comarca')}
                            rotuloItem="dias (mediana)"
                            semTotal
                        />
                    )}
                </ChartCard>
            </DashSection>

            <DashSection
                index={4}
                eyebrow="Estágio 2"
                title="Do mérito favorável/acordo ao pagamento"
                subtitle="Mesmo recorte de filtros, só com quem já vai receber: quanto tempo falta até o dinheiro entrar de fato."
            >
                {e2.length === 0 ? (
                    <ChartEmpty>Nenhum processo elegível ao pagamento nesse recorte de filtros.</ChartEmpty>
                ) : (
                    <>
                        <div className="grid grid-stat">
                            <MiniStat
                                label="Elegíveis ao pagamento"
                                icon="scale"
                                tone="neutral"
                                value={fmt.int(r.estagio2.elegiveis)}
                                hint="Venceram o Estágio 1 por mérito favorável ou acordo e entraram na fase de pagamento."
                            />
                            <MiniStat
                                label="Mediana até o pagamento"
                                icon="clock"
                                tone="info"
                                value={r.estagio2.mediana === null ? '—' : `${fmt.int(r.estagio2.mediana)} dias`}
                                hint="Kaplan-Meier do desfecho do Estágio 1 (não da distribuição) até o pagamento; evento só para os pagos."
                            />
                            <MiniStat label="Já pagos" icon="dollar" tone="ok" value={fmt.int(r.estagio2.pagos)} />
                            <MiniStat
                                label="Taxa de pagamento"
                                icon="percent"
                                tone="ok"
                                value={pctTexto(r.estagio2.taxa)}
                                hint="Já pagos ÷ elegíveis."
                            />
                        </div>
                        <div className="grid ex-duo ex-mt">
                            <ChartCard
                                title="Curva geral — tempo até o pagamento"
                                subtitle="Dias desde o mérito favorável/acordo; % ainda aguardando pagamento"
                            >
                                <Curvas
                                    series={[{ label: 'Aguardando', valores: curvaPct(obsEstagio2(e2)) }]}
                                    vazio={false}
                                />
                            </ChartCard>
                            <RankingCard
                                titulo="Gargalo de pagamento — por matéria"
                                sub="Mediana de dias até o pagamento (maior = o dinheiro demora mais a sair)"
                                r={rPagamento}
                                selecionados={selecao.materia}
                                onSelect={escolher('materia')}
                                logRankTitulo="Pagamento × matéria"
                            />
                        </div>
                    </>
                )}
            </DashSection>

            <DashSection
                index={5}
                eyebrow="Exploratório"
                title="Fase, subfase, juiz (1G) e relator (2G)"
                subtitle="Mediana de dias até mérito/acordo, dentro do recorte de filtros. Fora do modelo formal (Cox/Fine-Gray) — leia com cautela."
            >
                <p className="sv-alerta">
                    <Icon name="alert" size={14} /> Não é relação de causa: fase e subfase são o estado atual do
                    processo, e juiz e relator só são conhecidos depois da decisão. Servem para filtrar e explorar, não
                    para explicar o tempo.
                </p>
                <div className="grid ex-duo">
                    <RankingCard
                        titulo="Por fase"
                        r={rk('fase')}
                        selecionados={selecao.fase}
                        onSelect={escolher('fase')}
                    />
                    <RankingCard
                        titulo="Por subfase"
                        r={rk('subfase')}
                        selecionados={selecao.subfase}
                        onSelect={escolher('subfase')}
                    />
                    <RankingCard
                        titulo="Por juiz (1G)"
                        r={rk('juiz1g')}
                        selecionados={selecao.juiz1g}
                        onSelect={escolher('juiz1g')}
                    />
                    <RankingCard
                        titulo="Por relator (2G)"
                        r={rk('relator2g')}
                        selecionados={selecao.relator2g}
                        onSelect={escolher('relator2g')}
                    />
                </div>
            </DashSection>
        </div>
    )
}

function Curvas({ series, vazio }: { series: { label: string; valores: number[] }[]; vazio: boolean }) {
    if (vazio) return <ChartEmpty>Nenhum processo nesse recorte de filtros.</ChartEmpty>
    return (
        <LineChart
            height={300}
            legend={series.length > 1}
            format={(v) => `${fmt.int(v)}%`}
            labels={ROTULOS_GRADE}
            tooltip={{ heading: 'Dias', title: (i) => `${fmt.int(DIAS_GRADE[i])} dias` }}
            series={series.map((s, i) => ({
                label: s.label,
                color: CORES[i % CORES.length],
                values: s.valores,
                area: series.length === 1,
            }))}
        />
    )
}

// Curvas comparativas (as 6 categorias de maior volume com pelo menos 30 processos); clicar no nome esconde a linha.
function Comparativa({
    titulo,
    campo,
    linhas,
}: {
    titulo: string
    campo: Campo
    linhas: ReturnType<typeof aplicarFiltros>
}) {
    const curvas = useMemo(() => curvasPor(linhas, campo), [linhas, campo])
    const [ocultas, setOcultas] = useState<string[]>([])
    const visiveis = curvas.filter((c) => !ocultas.includes(c.nome))
    const cor = (nome: string) => CORES[curvas.findIndex((c) => c.nome === nome) % CORES.length]
    return (
        <ChartCard
            title={`${titulo} (top ${curvas.length} por volume)`}
            subtitle="% ainda sem desfecho do Estágio 1 · clique num nome para esconder a linha"
        >
            {curvas.length === 0 ? (
                <ChartEmpty>
                    Amostra insuficiente nesse recorte para comparar curvas (nenhuma categoria chega a 30 processos).
                </ChartEmpty>
            ) : (
                <>
                    <div className="sv-series">
                        {curvas.map((c) => (
                            <button
                                key={c.nome}
                                type="button"
                                aria-pressed={!ocultas.includes(c.nome)}
                                onClick={() =>
                                    setOcultas((o) =>
                                        o.includes(c.nome) ? o.filter((x) => x !== c.nome) : [...o, c.nome],
                                    )
                                }
                            >
                                <i style={{ background: cor(c.nome) }} />
                                {c.nome} <span className="muted">({fmt.int(c.n)})</span>
                            </button>
                        ))}
                    </div>
                    {visiveis.length === 0 ? (
                        <ChartEmpty>Todas as linhas escondidas.</ChartEmpty>
                    ) : (
                        <LineChart
                            height={320}
                            format={(v) => `${fmt.int(v)}%`}
                            labels={ROTULOS_GRADE}
                            tooltip={{ heading: 'Dias', title: (i) => `${fmt.int(DIAS_GRADE[i])} dias` }}
                            series={visiveis.map((c) => ({ label: c.nome, color: cor(c.nome), values: c.valores }))}
                        />
                    )}
                </>
            )}
        </ChartCard>
    )
}

function RankingCard({
    titulo,
    sub = 'Mediana de dias até mérito/acordo · clique para filtrar',
    r,
    selecionados,
    onSelect,
    logRankTitulo,
}: {
    titulo: string
    sub?: string
    r: Ranking
    selecionados: string[]
    onSelect: (nome: string) => void
    logRankTitulo?: string
}) {
    return (
        <ChartCard
            className="ex-rolagem"
            title={titulo}
            subtitle={`${sub} · ${fmt.int(r.itens.reduce((t, i) => t + i.n, 0))} processos`}
            footer={<LogRank titulo={logRankTitulo ?? titulo.replace(/^Por /, '')} r={r.logRank} />}
        >
            {r.itens.length === 0 ? (
                <ChartEmpty>Amostra insuficiente nesse recorte para este ranking.</ChartEmpty>
            ) : (
                <BarList
                    items={r.itens.map((i) => ({ name: i.name, value: i.value }))}
                    format={(v) => `${fmt.int(v)} d`}
                    valueOutside
                    wrapNames
                    selected={selecionados}
                    onSelect={onSelect}
                    selectLabel={`Filtrar: ${titulo.toLowerCase()}`}
                />
            )}
        </ChartCard>
    )
}

// O resultado do log-rank da v1 (LogRankBadge): significativo a 5%, com χ², graus de liberdade e p.
function LogRank({ titulo, r }: { titulo: string; r: ResultadoLogRank | null }) {
    if (!r)
        return (
            <p className="sv-logrank muted small">
                {titulo}: categorias insuficientes nesse recorte para o teste de log-rank (precisa de pelo menos 2
                grupos comparáveis).
            </p>
        )
    const sig = r.pValor < 0.05
    return (
        <p className={`sv-logrank small${sig ? ' sig' : ''}`}>
            <strong className={sig ? 'tone-text-ok' : 'muted'}>
                {sig ? 'Diferença estatisticamente significativa' : 'Sem evidência de diferença significativa'}
            </strong>{' '}
            — log-rank: χ² = {fmt.dec1(r.chi2)}, gl = {r.df}, {formatarPValor(r.pValor)}
        </p>
    )
}
