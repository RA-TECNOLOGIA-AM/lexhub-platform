import { useState, type CSSProperties } from 'react'
import { ChartEmpty } from '../../../components/charts/ChartCard.tsx'
import { ComarcaMapa } from '../../../components/charts/ComarcaMapa.tsx'
import { DashSection } from '../../../components/dashboard/DashSection.tsx'
import { Icon } from '../../../components/ui/Icon.tsx'
import { fmt } from '../../../lib/format.ts'
import type { DashboardFilters } from '../../../types/index.ts'
import { CAPITAL_POR_UF, GEO_POR_UF, mapaDaUnidade, type MapaDaUnidade } from '../julgados-acordaos/julgados.ts'
import {
    CAMPO_VALOR,
    FASES,
    ORDENS,
    ROTULO_FASE,
    brlSelo,
    gargalo,
    listaSubfases,
    pontosMapa,
    resumoFases,
    semSubfase,
    unidadeMapa,
    type Fase,
    type Juridico,
    type OrdemSubfase,
    type ResumoFase,
} from './estrategico.ts'

// O mapa de cada unidade (o dos Julgados), mas na NG só com os estados que ela atende: um processo com UF de outro
// estado não acrescenta o estado inteiro ao desenho. Objeto fixo: o mapa só busca de novo quando o conjunto muda.
const MAPA_NG: MapaDaUnidade = {
    geo: { porUf: { AM: GEO_POR_UF.AM, PA: GEO_POR_UF.PA, PB: GEO_POR_UF.PB } },
    capital: CAPITAL_POR_UF,
}
const mapaEstrategico = (u: 'NG' | 'LA' | 'RJ'): MapaDaUnidade => (u === 'NG' ? MAPA_NG : mapaDaUnidade(u))

// A cor de cada fase nos cards, nas abas e nas barras: Inicial azul, Recursal laranja, Execução verde.
const TOM: Record<Fase, string> = { inicial: 'info', recursal: 'warn', execucao: 'ok' }

type Modo = 'periodo' | 'fixo'

const TEXTO: Record<
    Modo,
    { eyebrow: string; titulo: string; sub: string; painel: string; painelSub: string; selo: string }
> = {
    periodo: {
        eyebrow: 'Jurídico · Fluxo do período',
        titulo: 'Jurídico: avanço nas fases',
        sub: 'Processos que entraram em cada fase no período (pela data de entrada na fase). Clique em um card para explorar suas subfases.',
        painel: 'por subfase',
        painelSub: 'Detalhamento interno das entradas no período por subfase, valor e tempo médio de permanência.',
        selo: 'entradas',
    },
    fixo: {
        eyebrow: 'Jurídico · Retrato atual',
        titulo: 'Jurídico fixo',
        sub: 'Retrato de agora, sem o período: todos os processos atualmente posicionados em cada fase.',
        painel: 'por subfase (estoque fixo)',
        painelSub: 'Distribuição atual das subfases com destaque para itens sem subfase e gargalos de tempo médio.',
        selo: 'processos ativos',
    },
}

// Seções 03 (com período) e 04 (fixo) do Estratégico: os 3 cards de fase, o painel de subfases da fase escolhida
// (ou das três, em "Ver todas") e os processos por comarca, que filtram o Jurídico.
export function JuridicoSecao({
    index,
    modo,
    j,
    unidade,
    comarcasBase,
    filters,
    onComarca,
}: {
    index: number
    modo: Modo
    j: Juridico | undefined
    unidade: string | undefined
    comarcasBase: string[] // as comarcas com processo (Jurídico fixo): separa zero no filtro de sem comarca na base
    filters: DashboardFilters
    onComarca?: (comarca: string) => void
}) {
    const t = TEXTO[modo]
    const r = resumoFases(j)
    const [fase, setFase] = useState<Fase>('inicial')
    const atual = r.fases.find((f) => f.fase === fase) ?? r.fases[0]
    const comarcas = j?.juridico_por_comarca ?? []
    const selecionadas = filters.comarca_estrategico ?? []
    const pontos = pontosMapa(comarcas)
    const mapa = mapaEstrategico(unidadeMapa(unidade))

    return (
        <DashSection
            index={index}
            eyebrow={t.eyebrow}
            badge={
                <span className={`es-selo tone-${modo === 'periodo' ? 'accent' : 'info'} num`}>
                    {fmt.int(r.processos)} {t.selo} · {brlSelo(r.valor)}
                </span>
            }
            title={t.titulo}
            subtitle={t.sub}
        >
            <div className="grid es-fases">
                {r.fases.map((f) => (
                    <CardFase key={f.fase} f={f} ativo={f.fase === fase} onClick={() => setFase(f.fase)} />
                ))}
            </div>
            <PainelSubfases fases={r.fases} atual={atual} onFase={setFase} titulo={t.painel} subtitulo={t.painelSub} />
            <div className="ex-mt">
                {comarcas.length === 0 ? (
                    <ChartEmpty>Nenhum processo{modo === 'periodo' ? ' no período' : ''} para o mapa.</ChartEmpty>
                ) : (
                    <ComarcaMapa
                        title={
                            modo === 'periodo'
                                ? 'Entradas no Jurídico por comarca'
                                : 'Processos do Jurídico por comarca'
                        }
                        geo={mapa.geo}
                        capital={mapa.capital}
                        quantidade={pontos.quantidade}
                        valor={pontos.valor}
                        comarcas={comarcasBase}
                        selected={selecionadas}
                        onSelect={onComarca}
                        height={520}
                        viewWidth={1320}
                        info={`Processos do Jurídico (Inicial + Recursal + Execução) ${modo === 'periodo' ? 'que entraram na fase no período' : 'de agora'}, por comarca. Clique num município para filtrar o Jurídico.`}
                        infoDetalhada="Cor do município pela quantidade de processos da comarca de mesmo nome (raiz quadrada); passe o cursor para ver a quantidade e o valor de causa. Clique num município para filtrar as seções do Jurídico pela comarca (de novo, para tirar). Cinza: a comarca existe, mas não tem processo no filtro; hachurado: não há comarca com esse nome na base."
                    />
                )}
            </div>
        </DashSection>
    )
}

function CardFase({ f, ativo, onClick }: { f: ResumoFase; ativo: boolean; onClick: () => void }) {
    const n = f.subfases.length
    return (
        <button
            type="button"
            className={`card es-fase tone-${TOM[f.fase]}`}
            aria-pressed={ativo}
            aria-label={`${ROTULO_FASE[f.fase]}: ${fmt.int(f.processos)} processos. Ver subfases`}
            onClick={onClick}
        >
            <span className="es-fase-topo">
                <span className="es-fase-chip">{ROTULO_FASE[f.fase]}</span>
                <span className="muted small">
                    {fmt.int(n)} subfase{n === 1 ? '' : 's'}
                </span>
                <span className="es-fase-pct num">{fmt.pct(f.pctTotal)} do total</span>
            </span>
            <span className="es-fase-numeros">
                <span>
                    <span className="es-fase-rotulo">Processos</span>
                    <span className="es-fase-qtd num">{fmt.int(f.processos)}</span>
                </span>
                <span className="es-fase-direita">
                    <span className="es-fase-rotulo">Valor de causa</span>
                    <span className="es-fase-valor num">{fmt.brl(f.valor)}</span>
                </span>
            </span>
            <span className="es-fase-rodape">
                {f.secundario ? (
                    <>
                        <span className="muted">{f.secundario.rotulo}:</span>
                        <strong className="es-fase-sec num">{fmt.brl(f.secundario.valor)}</strong>
                    </>
                ) : (
                    <>
                        <span className="muted">Sem valor secundário vinculado</span>
                        <span className="es-fase-link">Ver subfases →</span>
                    </>
                )}
            </span>
        </button>
    )
}

function PainelSubfases({
    fases,
    atual,
    onFase,
    titulo,
    subtitulo,
}: {
    fases: ResumoFase[]
    atual: ResumoFase
    onFase: (f: Fase) => void
    titulo: string
    subtitulo: string
}) {
    const [busca, setBusca] = useState('')
    const [ordem, setOrdem] = useState<OrdemSubfase>('processos')
    const [todas, setTodas] = useState(false)
    const visiveis = todas ? fases : [atual]
    const total = visiveis.reduce((s, f) => s + f.subfases.length, 0)
    const processos = visiveis.reduce((s, f) => s + f.processos, 0)

    return (
        <div className="card es-painel ex-mt">
            <div className="es-painel-cab">
                <div className="es-painel-texto">
                    <span className="es-painel-titulo">
                        <strong>
                            {todas ? 'Todas as fases' : ROTULO_FASE[atual.fase]} {titulo}
                        </strong>
                        <span className="es-selo tone-info num">
                            {fmt.int(total)} subfases · {fmt.int(processos)} processos
                        </span>
                    </span>
                    <span className="muted small">{subtitulo}</span>
                </div>
                <div className="es-painel-controles">
                    {!todas && (
                        <div className="es-abas" role="tablist" aria-label="Fase">
                            {fases.map((f) => (
                                <button
                                    key={f.fase}
                                    type="button"
                                    role="tab"
                                    aria-selected={f.fase === atual.fase}
                                    className={`tone-${TOM[f.fase]}`}
                                    onClick={() => onFase(f.fase)}
                                >
                                    {ROTULO_FASE[f.fase]} <span className="num">({fmt.int(f.processos)})</span>
                                </button>
                            ))}
                        </div>
                    )}
                    <label className="es-busca">
                        <Icon name="search" size={15} />
                        <span className="sr-only">Filtrar subfase</span>
                        <input
                            type="search"
                            placeholder="Filtrar subfase..."
                            value={busca}
                            onChange={(e) => setBusca(e.target.value)}
                        />
                    </label>
                    <label className="es-ordem">
                        <span className="sr-only">Ordenar subfases</span>
                        <select value={ordem} onChange={(e) => setOrdem(e.target.value as OrdemSubfase)}>
                            {ORDENS.map((o) => (
                                <option key={o.value} value={o.value}>
                                    Ordenar: {o.label}
                                </option>
                            ))}
                        </select>
                    </label>
                    <button type="button" className="btn" aria-pressed={todas} onClick={() => setTodas((v) => !v)}>
                        {todas ? 'Ver uma' : `Ver todas (${FASES.length})`}
                    </button>
                </div>
            </div>
            {visiveis.map((f) => (
                <TabelaSubfases
                    key={f.fase}
                    f={f}
                    titulo={todas ? ROTULO_FASE[f.fase] : null}
                    busca={busca}
                    ordem={ordem}
                />
            ))}
        </div>
    )
}

const ROTULO_VALOR = { valor_causa: 'Valor de causa', valor_execucao: 'Valor execução' }

function TabelaSubfases({
    f,
    titulo,
    busca,
    ordem,
}: {
    f: ResumoFase
    titulo: string | null
    busca: string
    ordem: OrdemSubfase
}) {
    const campo = CAMPO_VALOR[f.fase]
    const itens = listaSubfases(f.subfases, campo, ordem, busca)
    const soma = f.subfases.reduce((s, i) => s + i.value, 0)
    const maior = Math.max(...f.subfases.map((i) => i.value), 1)
    const pior = gargalo(f.subfases)
    const temTempo = f.subfases.some((i) => i.tempo_medio_dias != null)
    const linha = `es-tab-linha${temTempo ? '' : ' sem-tempo'}`
    return (
        <div className={`es-tabela tone-${TOM[f.fase]}`}>
            {titulo && <h3 className="es-tabela-titulo">{titulo}</h3>}
            <div className={`${linha} es-tab-cab`} aria-hidden="true">
                <span>Subfase</span>
                <span>Distribuição</span>
                <span>Processos</span>
                <span>%</span>
                <span>{ROTULO_VALOR[campo]}</span>
                {temTempo && <span>Tempo médio</span>}
            </div>
            {itens.length === 0 ? (
                <ChartEmpty>
                    {f.subfases.length === 0 ? 'Nenhum processo nesta fase.' : 'Nenhuma subfase com esse nome.'}
                </ChartEmpty>
            ) : (
                <ul className="es-tab-lista" role="list">
                    {itens.map((s) => {
                        const vazio = semSubfase(s)
                        const valor = s[campo]
                        return (
                            <li key={s.name} className={`${linha}${vazio ? ' es-sem-subfase' : ''}`}>
                                <span className="es-tab-nome" title={s.name}>
                                    {s.name}
                                </span>
                                <span className="es-tab-trilho" aria-hidden="true">
                                    <span
                                        className="es-tab-barra"
                                        style={{ '--w': `${Math.max((s.value / maior) * 100, 3)}%` } as CSSProperties}
                                    />
                                </span>
                                <strong className="num">{fmt.int(s.value)}</strong>
                                <span className="num muted">{fmt.pct(soma > 0 ? (s.value / soma) * 100 : 0)}</span>
                                <strong className="num">{valor == null ? '—' : fmt.brlShort(valor)}</strong>
                                {temTempo && (
                                    <span className="num">
                                        {s.tempo_medio_dias == null ? (
                                            <span className="muted">—</span>
                                        ) : s.name === pior ? (
                                            <span
                                                className="es-gargalo"
                                                title="Maior tempo médio de permanência desta fase"
                                            >
                                                {fmt.dias(s.tempo_medio_dias)}
                                            </span>
                                        ) : (
                                            <span className="muted">{fmt.dias(s.tempo_medio_dias)}</span>
                                        )}
                                    </span>
                                )}
                            </li>
                        )
                    })}
                </ul>
            )}
        </div>
    )
}
