import { useState, type KeyboardEvent, type ReactNode } from 'react'
import { ChartCard, ChartEmpty } from '../../../components/charts/ChartCard.tsx'
import { DashSection } from '../../../components/dashboard/DashSection.tsx'
import { DeltaPill, InfoTip, MiniStat, Pill } from '../../../components/dashboard/StatCard.tsx'
import { Icon, type IconName } from '../../../components/ui/Icon.tsx'
import { Segmented } from '../../../components/ui/Segmented.tsx'
import { fmt } from '../../../lib/format.ts'
import type { Point } from '../../../types/index.ts'
import type { ContentProps } from '../types.ts'
import { MesAMes } from '../execucao/partes.tsx'
import {
    METAS_DIAS,
    duracao,
    lerControle,
    type ControleResponse,
    type QtdValor,
    type Subfase,
    type Tempo,
    type TipoSentenca,
} from './controle.ts'

const brl = (v: number | null) => (v === null ? '—' : fmt.brl(v))
const qtd = (v: number | null) => (v === null ? '—' : fmt.int(v))

// Controle de Processos (NG): a página da v1 no layout da V2 — a esteira de trabalho (protocolados → inicial →
// recursal → execução → arquivados por procedência, com os extintos e a improcedência), a permanência por fase e
// a distribuição por fase e subfase. Os filtros (situação, UFs) ficam na janela Filtros; a fase, no gráfico.
export function ControleContent({ data, filters = {}, onFiltersChange }: ContentProps<ControleResponse>) {
    const c = lerControle(data, filters)
    const faseAtual = filters.fase_controle?.[0] ?? ''
    const escolherFase = (fase: string) => {
        if (!onFiltersChange) return
        const { fase_controle: _, ...resto } = filters
        void _
        onFiltersChange(fase ? { ...resto, fase_controle: [fase] } : resto)
    }
    const rotuloSituacao =
        c.situacao === 'ativo' ? 'Ativo' : c.situacao === 'suspenso' ? 'Suspenso/Sobrestado' : 'Todos'
    const [faseGrafico, setFaseGrafico] = useState<FaseGrafico>('inicial')
    const [todas, setTodas] = useState(false)
    // Clicar num estágio (fase) mostra a evolução dele no gráfico de baixo.
    const mostrarFase = (k: FaseGrafico) => {
        setFaseGrafico(k)
        setTodas(false)
    }
    // "Inspecionar subfases" de uma etapa: escolhe a fase no gráfico da seção 03 e rola até ele (só se a fase existe).
    const inspecionar = (fase: string) => {
        const nome = c.fases.find((f) => f.toUpperCase() === fase)
        if (!nome || !onFiltersChange) return undefined
        return () => {
            escolherFase(nome)
            document.getElementById('cp-subfases')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
        }
    }

    if (!c.temDados) {
        return <ChartEmpty>Sem dados do controle de processos. Ajuste os filtros ou clique em Atualizar.</ChartEmpty>
    }

    return (
        <div className="dsecs">
            <DashSection
                index={1}
                eyebrow="Linha do tempo · Fluxo processual"
                title="Esteira de trabalho"
                subtitle="Etapas: o retrato de agora (protocolados e arquivados por procedência: o período). Extintos e improcedência: o período escolhido."
            >
                <div className="card cp-linha">
                    <div className="cp-base">
                        <span className="cp-base-selo">Base total NG{c.situacao ? ` · ${rotuloSituacao}` : ''}</span>
                        <strong className="num cp-base-qtd">{qtd(c.total.qtd)}</strong>
                        <span className="muted small">processos no retrato atual</span>
                        <span className="cp-base-sep" aria-hidden="true" />
                        <span className="muted small">
                            Valor da causa total: <strong className="num tone-text-ok">{brl(c.total.valor)}</strong>
                        </span>
                    </div>

                    <ol className="cp-etapas" aria-label="Etapas da esteira">
                        <Etapa
                            n={1}
                            cor="azul"
                            titulo="Protocolados (período)"
                            sub="Legado + LexPre"
                            v={c.protocolados}
                        />
                        <Etapa
                            n={2}
                            cor="ambar"
                            titulo="Fase Inicial (1G)"
                            sub="Estoque ativo 1º grau"
                            v={c.inicial}
                            log={{ titulo: 'Inicial indeferida (log)', v: c.inicialIndeferida }}
                            inspecionar={inspecionar('INICIAL')}
                        />
                        <Etapa
                            n={3}
                            cor="violeta"
                            titulo="Fase Recursal (2G)"
                            sub="Turmas / Câmaras"
                            v={c.recursal}
                            log={{ titulo: 'Recurso não provido (log)', v: c.recursalNaoProvido }}
                            inspecionar={inspecionar('RECURSAL')}
                        />
                        <Etapa
                            n={4}
                            cor="indigo"
                            titulo="Trânsito em julgado"
                            sub="Aguardando liquidação"
                            v={c.transitoJulgado}
                            inspecionar={inspecionar('TRÂNSITO EM JULGADO')}
                        />
                        <Etapa
                            n={5}
                            cor="verde"
                            titulo="Execução ativa"
                            sub="Condenação + Acordos"
                            v={c.execucao}
                            inspecionar={inspecionar('EXECUÇÃO')}
                        />
                        <Etapa
                            n={6}
                            cor="teal"
                            titulo="Arquivados procedência"
                            sub="Saídas da Execução (período)"
                            v={c.arquivadosProcedencia}
                            rotuloValor="TED"
                            inspecionar={inspecionar('ARQUIVADO POR PROCEDÊNCIA')}
                            ultima
                        />
                    </ol>
                </div>

                <div className="grid cp-encerrados ex-mt">
                    <Extintos
                        titulo="Extintos · 1º grau"
                        sub="Saem após a fase Inicial (sentenças no período)"
                        tipos="Por tipo de sentença · extintos com mérito"
                        e={c.extintos1g}
                    />
                    <Extintos
                        titulo="Extintos · 2º grau"
                        sub="Saem após a fase Recursal (acórdãos no período, sem os filtros de situação e UF, como na v1)"
                        tipos="Por tipo de acórdão · extintos com mérito"
                        e={c.extintos2g}
                        taxa={c.extintos2g.taxaProvimento}
                    />
                    <Quadro titulo="Improcedência" sub="Arquivados por improcedência" total={c.improcedencia.qtd ?? 0}>
                        <Linha rotulo="Arquivados por improcedência" v={c.improcedencia} />
                        <div className="cp-carteira">
                            <span className="muted small">Decréscimo na carteira</span>
                            <div className="foot-row">
                                <span>Valor protocolado</span>
                                <span className="num">{brl(c.protocolados.valor)}</span>
                            </div>
                            <div className="foot-row">
                                <span>(–) Extintos sem mérito · 1º grau</span>
                                <span className="num">{brl(c.extintos1g.semMerito.valor)}</span>
                            </div>
                            <div className="foot-row">
                                <span>(–) Extintos sem mérito · 2º grau</span>
                                <span className="num">{brl(c.extintos2g.semMerito.valor)}</span>
                            </div>
                            <div className="foot-row cp-liquida">
                                <strong>Carteira líquida</strong>
                                <strong
                                    className={`num ${c.carteiraLiquida < 0 ? 'tone-text-danger' : 'tone-text-ok'}`}
                                >
                                    {fmt.brl(c.carteiraLiquida)}
                                </strong>
                            </div>
                        </div>
                    </Quadro>
                </div>
            </DashSection>

            <DashSection
                index={2}
                eyebrow="Permanência"
                title="Tempo médio e mediano por setor"
                subtitle="Comparativo lado a lado entre média e mediana em cada estágio, frente às metas ideais (JEC + Justiça Comum). Fases: processos que saíram delas no período; variação contra os mesmos dias do mês anterior."
            >
                <div className="grid cp-estagios">
                    <Estagio
                        cor="azul"
                        icon="clock"
                        titulo="Protocolo"
                        sub="Até a saída do protocolo"
                        dica="Banco NG legado: da contratação até a saída do protocolo. LexPre (onde os protocolos entram hoje): da entrada até a saída da demanda no setor de Protocolo — o LexPre não tem a data de contratação. Com os dois no período, a média é ponderada pela quantidade de cada um, e a mediana e a variação são do que teve mais protocolos."
                        p={c.permanencia.protocolo}
                        rodape={
                            <div className="foot-row small">
                                <span className="muted">
                                    {c.fonteProtocolo === 'lexpre'
                                        ? 'LexPre: entrada → saída do setor de Protocolo'
                                        : c.fonteProtocolo === 'legado'
                                          ? 'Banco legado: contratação → saída do protocolo'
                                          : c.fonteProtocolo === 'ambos'
                                            ? 'Legado + LexPre (média ponderada)'
                                            : 'Sem protocolos no período'}
                                </span>
                                <span className="cp-tag-azul num">Fluxo inicial</span>
                            </div>
                        }
                    />
                    <Estagio
                        cor="ambar"
                        icon="briefcase"
                        titulo="Fase Inicial"
                        sub="Permanência no 1º grau"
                        dica="Do ajuizamento até a saída da fase Inicial, dos processos que saíram dela no período."
                        p={c.permanencia.inicial}
                        meta={METAS_DIAS.inicial}
                        ativo={!todas && faseGrafico === 'inicial'}
                        onClick={() => mostrarFase('inicial')}
                    />
                    <Estagio
                        cor="violeta"
                        icon="scale"
                        titulo="Fase Recursal"
                        sub="Permanência em 2ª instância"
                        dica="Da entrada até a saída da fase Recursal, dos processos que saíram dela no período."
                        p={c.permanencia.recursal}
                        meta={METAS_DIAS.recursal}
                        ativo={!todas && faseGrafico === 'recursal'}
                        onClick={() => mostrarFase('recursal')}
                    />
                    <Estagio
                        cor="verde"
                        icon="target"
                        titulo="Fase Execução"
                        sub="Cumprimento e satisfação"
                        dica="Da entrada até a saída da fase de Execução, dos processos que saíram dela no período."
                        p={c.permanencia.execucao}
                        meta={METAS_DIAS.execucao}
                        ativo={!todas && faseGrafico === 'execucao'}
                        onClick={() => mostrarFase('execucao')}
                    />
                </div>

                <ChartCard
                    className="ex-mt"
                    title="Evolução mensal do tempo médio (histórico completo)"
                    subtitle="Clique numa fase acima (ou alterne aqui) ou veja todas lado a lado, frente à linha de meta ideal."
                    action={
                        <div className="cp-graf-acoes">
                            {!todas && (
                                <Segmented<FaseGrafico>
                                    label="Fase do gráfico"
                                    value={faseGrafico}
                                    onChange={setFaseGrafico}
                                    options={FASES_GRAFICO.map((f) => ({
                                        value: f.k,
                                        label: `${f.rotulo} (${METAS_DIAS[f.k]}d)`,
                                    }))}
                                />
                            )}
                            <button
                                type="button"
                                className="btn"
                                aria-pressed={todas}
                                onClick={() => setTodas((t) => !t)}
                            >
                                <Icon name="grid" size={15} />
                                {todas ? 'Ver uma' : 'Ver todas (3)'}
                            </button>
                        </div>
                    }
                >
                    {todas ? (
                        <div className="grid tk-tres">
                            {FASES_GRAFICO.map((f) => (
                                <GraficoFase key={f.k} k={f.k} rotulo={f.rotulo} pontos={c.porMes[f.k]} altura={260} />
                            ))}
                        </div>
                    ) : (
                        <GraficoFase
                            key={faseGrafico}
                            k={faseGrafico}
                            rotulo={FASES_GRAFICO.find((f) => f.k === faseGrafico)?.rotulo ?? ''}
                            pontos={c.porMes[faseGrafico]}
                            altura={340}
                        />
                    )}
                </ChartCard>
            </DashSection>

            <DashSection
                index={3}
                eyebrow="Distribuição"
                title="Fases e subfases"
                subtitle="Selecione uma fase para ver o detalhamento por subfase (retrato de agora, com a situação e as UFs dos filtros)."
            >
                <div id="cp-subfases" />
                <ChartCard
                    title="Processos por fase / subfase"
                    subtitle="Quantidade, valor de causa e tempo médio em cada subfase"
                    action={
                        <label className="field-select">
                            <span className="sr-only">Fase</span>
                            <select value={faseAtual} onChange={(e) => escolherFase(e.target.value)}>
                                <option value="">Selecione uma fase</option>
                                {c.fases.map((f) => (
                                    <option key={f} value={f}>
                                        {f}
                                    </option>
                                ))}
                            </select>
                        </label>
                    }
                >
                    {c.subfases === null ? (
                        <ChartEmpty>Selecione uma fase para ver as subfases.</ChartEmpty>
                    ) : c.subfases.itens.length === 0 ? (
                        <ChartEmpty>Nenhuma subfase nesta fase.</ChartEmpty>
                    ) : (
                        <Subfases
                            itens={c.subfases.itens}
                            total={c.subfases.total}
                            qtd={c.subfases.qtd ?? c.subfases.itens.length}
                        />
                    )}
                </ChartCard>
            </DashSection>
        </div>
    )
}

type Cor = 'azul' | 'ambar' | 'violeta' | 'indigo' | 'verde' | 'teal' | 'vermelho'

// Uma etapa da linha do tempo: número, nome, quantidade e valor, o "log" da etapa (quando há) e o atalho para as
// subfases dela.
function Etapa({
    n,
    cor,
    titulo,
    sub,
    v,
    log,
    rotuloValor,
    inspecionar,
    ultima = false,
}: {
    n: number
    cor: Cor
    titulo: string
    sub: string
    v: QtdValor
    log?: { titulo: string; v: QtdValor }
    rotuloValor?: string
    inspecionar?: () => void
    ultima?: boolean
}) {
    return (
        <li className={`cp-etapa cp-${cor}`}>
            <div className="cp-etapa-topo">
                <span className="cp-etapa-n num">Etapa {String(n).padStart(2, '0')}</span>
                {!ultima && (
                    <span className="cp-etapa-seta" aria-hidden="true">
                        →
                    </span>
                )}
            </div>
            <strong className="cp-etapa-titulo">{titulo}</strong>
            <span className="muted small cp-etapa-sub">{sub}</span>
            <strong className="num cp-etapa-qtd">{qtd(v.qtd)}</strong>
            <span className="num muted small">
                {rotuloValor ? `${rotuloValor}: ` : ''}
                {v.valor === null ? '—' : fmt.brlShort(v.valor)}
            </span>
            <div className="cp-etapa-pe">
                {log ? (
                    <div className="cp-etapa-log">
                        <span className="small">{log.titulo}</span>
                        <strong className="num tone-text-warn">{qtd(log.v.qtd)}</strong>
                        <span className="num muted small">
                            {log.v.valor === null ? '—' : fmt.brlShort(log.v.valor)}
                        </span>
                    </div>
                ) : inspecionar ? (
                    <button type="button" className="linkbtn muted small" onClick={inspecionar}>
                        Inspecionar subfases
                    </button>
                ) : null}
            </div>
        </li>
    )
}

// O painel de extintos (o mesmo formato do "Extintos · 2º grau" do Recursal): com e sem mérito e, dos com mérito,
// cada tipo de sentença / acórdão.
function Extintos({
    titulo,
    sub,
    tipos,
    e,
    taxa,
}: {
    titulo: string
    sub: string
    tipos: string
    e: { comMerito: QtdValor; semMerito: QtdValor; porTipo: TipoSentenca[]; total: number }
    taxa?: number | null
}) {
    return (
        <ChartCard
            title={titulo}
            subtitle={sub}
            tag={
                <>
                    {taxa !== undefined && taxa !== null && (
                        <Pill tone="info">Taxa de provimento {fmt.dec1(taxa)}%</Pill>
                    )}
                    <Pill>{fmt.int(e.total)} no total</Pill>
                </>
            }
        >
            <div className="grid ex-duo">
                <MiniStat
                    label="Extintos com mérito"
                    icon="check-circle"
                    tone="ok"
                    value={qtd(e.comMerito.qtd)}
                    below={<span className="muted small">{brl(e.comMerito.valor)} em valor de causa</span>}
                />
                <MiniStat
                    label="Extintos sem mérito"
                    icon="x-circle"
                    tone="danger"
                    value={qtd(e.semMerito.qtd)}
                    below={<span className="muted small">{brl(e.semMerito.valor)} em valor de causa</span>}
                />
            </div>
            {e.porTipo.length > 0 && (
                <div className="rc-portipo">
                    <span className="muted small">{tipos}</span>
                    <ul role="list">
                        {e.porTipo.map((t) => (
                            <li key={t.tipo}>
                                <span>{t.tipo}</span>
                                <span className="num">
                                    <strong>{fmt.int(t.qtd)}</strong>
                                    {t.valor !== null && <span className="muted"> · {fmt.brl(t.valor)}</span>}
                                </span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </ChartCard>
    )
}

function Quadro({ titulo, sub, total, children }: { titulo: string; sub: string; total: number; children: ReactNode }) {
    return (
        <div className="card cp-quadro">
            <div className="cp-quadro-topo">
                <div>
                    <strong>{titulo}</strong>
                    <span className="muted small"> · {sub}</span>
                </div>
                <span className="cp-badge num">{fmt.int(total)}</span>
            </div>
            {children}
        </div>
    )
}

function Linha({ rotulo, v }: { rotulo: string; v: QtdValor }) {
    return (
        <div className="foot-row cp-item">
            <span>{rotulo}</span>
            <span>
                <strong className="num">{qtd(v.qtd)}</strong> <span className="num muted small">{brl(v.valor)}</span>
            </span>
        </div>
    )
}

type FaseGrafico = 'inicial' | 'recursal' | 'execucao'
const FASES_GRAFICO: { k: FaseGrafico; rotulo: string }[] = [
    { k: 'inicial', rotulo: 'Fase Inicial' },
    { k: 'recursal', rotulo: 'Fase Recursal' },
    { k: 'execucao', rotulo: 'Fase Execução' },
]

// Um estágio da permanência: média e mediana lado a lado (subir é ruim, como na v1) e, nas fases, a meta ideal com a
// régua (a média contra a meta; a régua vai até 1,4 × a meta).
function Estagio({
    cor,
    icon,
    titulo,
    sub,
    dica,
    p,
    meta,
    rodape,
    ativo,
    onClick,
}: {
    cor: Cor
    icon: IconName
    titulo: string
    sub: string
    dica: string
    p: { media: Tempo; mediana: Tempo }
    meta?: number
    rodape?: ReactNode
    ativo?: boolean // o estágio mostrado no gráfico de baixo
    onClick?: () => void
}) {
    const media = p.media.valor
    const escala = meta ? meta * 1.4 : 1
    const dentro = meta !== undefined && media !== null ? media <= meta : null
    return (
        <div
            className={`card cp-estagio cp-${cor}${onClick ? ' clicavel' : ''}`}
            {...(onClick
                ? {
                      role: 'button',
                      tabIndex: 0,
                      'aria-pressed': ativo,
                      'aria-label': `${titulo}: mostrar no gráfico de evolução mensal`,
                      onClick,
                      onKeyDown: (e: KeyboardEvent<HTMLDivElement>) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                              e.preventDefault()
                              onClick()
                          }
                      },
                  }
                : {})}
        >
            {ativo && <span className="cp-estagio-selo">No gráfico</span>}
            <div className="cp-estagio-topo">
                <span className="cp-estagio-ico" aria-hidden="true">
                    <Icon name={icon} size={18} />
                </span>
                <div className="cp-estagio-nome">
                    <strong>{titulo}</strong>
                    <span className="muted small">{sub}</span>
                </div>
                <InfoTip text={dica} />
            </div>
            <div className="cp-estagio-valores">
                {(
                    [
                        ['Média', p.media],
                        ['Mediana', p.mediana],
                    ] as const
                ).map(([rotulo, t]) => (
                    <div key={rotulo} className="cp-estagio-valor">
                        <span className="cp-estagio-rotulo">{rotulo}</span>
                        <strong className="num">{duracao(t.valor)}</strong>
                        <DeltaPill value={t.comparativo} betterWhenDown />
                    </div>
                ))}
            </div>
            <div className="cp-estagio-pe">
                {meta !== undefined ? (
                    <>
                        <div className="foot-row small">
                            <span className="muted">
                                <Icon name="target" size={13} /> Meta ideal: <strong className="num">{meta}d</strong>
                            </span>
                            {dentro !== null && (
                                <span className={`num ${dentro ? 'tone-text-ok' : 'tone-text-warn'}`}>
                                    {dentro ? 'Dentro da meta' : 'Acima da meta'}
                                </span>
                            )}
                        </div>
                        <span className="cp-regua" aria-hidden="true">
                            <span
                                className={dentro === false ? 'acima' : undefined}
                                style={{ width: `${Math.min(((media ?? 0) / escala) * 100, 100)}%` }}
                            />
                            <i style={{ left: `${(meta / escala) * 100}%` }} />
                        </span>
                    </>
                ) : (
                    rodape
                )}
            </div>
        </div>
    )
}

function GraficoFase({
    k,
    rotulo,
    pontos,
    altura,
}: {
    k: FaseGrafico
    rotulo: string
    pontos: Point[]
    altura: number
}) {
    return (
        <div className="cp-grafico">
            <strong className="small">Tempo médio em dias — {rotulo} (por mês)</strong>
            <MesAMes
                pontos={pontos}
                height={altura}
                format={(v) => `${fmt.int(v)}d`}
                meta={{ value: METAS_DIAS[k], label: `Meta: ${METAS_DIAS[k]}d` }}
            />
        </div>
    )
}

// As subfases da fase escolhida: barra da quantidade, %, valor de causa e tempo médio na subfase (como a v1).
function Subfases({ itens, total, qtd: nSubfases }: { itens: Subfase[]; total: number | null; qtd: number }) {
    const soma = itens.reduce((s, i) => s + i.value, 0)
    const base = soma > 0 ? soma : total && total > 0 ? total : 1
    const maior = Math.max(...itens.map((i) => i.value), 1)
    return (
        <div className="cp-subfases">
            <div className="foot-row muted small">
                <span>
                    {fmt.int(nSubfases)} subfase{nSubfases === 1 ? '' : 's'}{' '}
                    <InfoTip text="Tempo médio: a média dos períodos já encerrados de permanência na subfase, pelo histórico de movimentações (sem o filtro de UF)." />
                </span>
                <span>Total: {fmt.int(total ?? soma)}</span>
            </div>
            <div className="cp-sub-cab muted small" aria-hidden="true">
                <span>Subfase</span>
                <span>Processos</span>
                <span>%</span>
                <span>Valor de causa</span>
                <span>Tempo médio</span>
            </div>
            <ul className="cp-sub-lista" role="list">
                {itens.map((s) => (
                    <li key={s.name} className="cp-sub-linha">
                        <span className="cp-sub-nome" title={s.name}>
                            {s.name}
                        </span>
                        <span className="cp-sub-trilho">
                            <span
                                className="cp-sub-barra"
                                style={{ width: `${Math.max((s.value / maior) * 100, 2)}%` }}
                            />
                            <span className="num cp-sub-qtd">{fmt.int(s.value)}</span>
                        </span>
                        <span className="num muted">{fmt.dec1((s.value / base) * 100)}%</span>
                        <span className="num muted">{s.valor === null ? '—' : fmt.brlShort(s.valor)}</span>
                        <span className="num muted">{duracao(s.tempoMedioDias)}</span>
                    </li>
                ))}
            </ul>
        </div>
    )
}
