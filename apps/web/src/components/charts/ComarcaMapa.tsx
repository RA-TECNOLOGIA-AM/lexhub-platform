import { useEffect, useId, useMemo, useRef, useState, type KeyboardEvent, type MouseEvent } from 'react'
import { geoMercator, geoPath, type GeoPermissibleObjects } from 'd3-geo'
import {
    aCadaDez,
    capitalInterior,
    resolverMunicipios,
    resumoMapa,
    revertidos as calcularRevertidos,
    semComarca as calcularSemComarca,
    tempoMedio,
    ufsComDados,
    type Municipio,
    type MunicipioResolvido,
    type PontoComarca,
} from '../../lib/comarcaMapa.ts'
import { fmt } from '../../lib/format.ts'
import { Icon } from '../ui/Icon.tsx'
import { Modal } from '../ui/Modal.tsx'
import './ComarcaMapa.css'

// Um município do GeoJSON simplificado (public/geo/*.json, malha municipal do IBGE).
type Feature = { type: 'Feature'; properties: { id: string; name: string }; geometry: unknown }
type FeatureCollection = { type: 'FeatureCollection'; features: Feature[] }

// Os municípios já desenhados (o caminho SVG de cada um) para um conjunto de arquivos (chave 'UF=url,...').
type Forma = Municipio & { d: string }
type Desenho = { chave: string; formas: Forma[] }
const SEM_FORMAS: Forma[] = []

// Cada GeoJSON é baixado uma vez só (sob demanda, quando o mapa aparece) e fica guardado enquanto a aba vive.
const cache = new Map<string, Promise<FeatureCollection>>()
function carregar(url: string): Promise<FeatureCollection> {
    let pronto = cache.get(url)
    if (!pronto) {
        pronto = fetch(url).then((res) => {
            if (!res.ok) throw new Error(`Falha ao carregar o mapa (HTTP ${res.status})`)
            return res.json() as Promise<FeatureCollection>
        })
        pronto.catch(() => cache.delete(url))
        cache.set(url, pronto)
    }
    return pronto
}

// Textos da legenda (os da v1; o padrão é o do estudo de extinção).
export type TextosMapa = {
    categoriaPlural?: string // "A cada 10 processos julgados, X são {categoriaPlural}."
    revertidosTitulo?: string // título da 3ª coluna
    revertidosDescricao?: string // linha embaixo do % da 3ª coluna
    revertidosFrase?: string // "A cada 10 processos {categoriaPlural}, Y {revertidosFrase}"
}

type ComarcaMapaProps = {
    title: string
    // Vários estados (NG): UF -> GeoJSON, e o mapa mostra os estados que têm dado. Um estado (LA, RJ): o GeoJSON dele.
    geo: { porUf: Record<string, string> } | { url: string }
    quantidade: PontoComarca[] // por comarca, no escopo; no de vários estados, com a UF
    valor?: PontoComarca[] // valor (R$) por comarca, para a dica do cursor
    comarcas: string[] // todas as comarcas da base (separa "zero no filtro" de "sem comarca na base")
    selected?: string[]
    onSelect?: (comarca: string) => void
    info?: string // o "i" (ao passar o cursor)
    infoDetalhada?: string // clicar no "i" abre a explicação completa
    capital?: Record<string, string> | string // capital de cada UF (vários estados) ou do estado
    totalJulgados?: number // base do "a cada 10"
    revertidos?: number // 3ª coluna da legenda (ex.: recursos ao STJ/STF)
    textos?: TextosMapa
    height?: number // altura do mapa (px)
    viewWidth?: number // proporção do desenho (largura : altura)
    viewHeight?: number
}

// Módulo: o mapa coroplético de comarcas da v1 (ComarcaMapaMultiUfChart e ComarcaMapaChart num só). Cada município
// com comarca homônima na base fica laranja pela quantidade (raiz quadrada; mais forte = mais processos), cinza
// quando a comarca existe mas não tem processo no filtro, e hachurado quando não há comarca na base. Cursor mostra
// quantidade, valor e tempo médio; clicar num município liga ou desliga o filtro da comarca. Embaixo, a legenda
// (contagens, Capital × Interior, "a cada 10" e a 3ª coluna opcional) e o aviso dos processos sem comarca.
export function ComarcaMapa({
    title,
    geo,
    quantidade,
    valor = [],
    comarcas,
    selected = [],
    onSelect,
    info,
    infoDetalhada,
    capital,
    totalJulgados,
    revertidos,
    textos = {},
    height = 520,
    viewWidth = 680,
    viewHeight = 560,
}: ComarcaMapaProps) {
    const porUf = 'porUf' in geo
    const urlsPorUf = porUf ? geo.porUf : null
    const urlUnica = porUf ? null : geo.url
    const ufs = urlsPorUf ? ufsComDados(quantidade, urlsPorUf) : []
    // Os arquivos a carregar: as UFs com dado (vários estados) ou o estado. A chave 'UF=url,...' só muda quando muda
    // o conjunto, e é dela que dependem a busca e a projeção.
    const urls = urlsPorUf ? ufs.map((uf) => [uf, urlsPorUf[uf]] as const) : [['', urlUnica ?? ''] as const]
    const chaveUrls = urls.map(([uf, url]) => `${uf}=${url}`).join(',')

    const [desenho, setDesenho] = useState<Desenho | null>(null)
    const [erro, setErro] = useState<string | null>(null)
    const [hover, setHover] = useState<MunicipioResolvido<Forma> | null>(null)
    const [mouse, setMouse] = useState<{ x: number; y: number } | null>(null)
    const [detalhes, setDetalhes] = useState(false)
    const caixa = useRef<HTMLDivElement>(null)
    const padrao = `cmapa-hachura-${useId().replace(/[^\w-]/g, '')}` // id seguro para url(#...)

    // Baixa os estados e desenha (projeção Mercator ajustada ao conjunto, como a v1) só quando muda o conjunto de
    // arquivos (a chave 'UF=url,...'): filtros e cursor não refazem a projeção.
    useEffect(() => {
        let cancelado = false
        const chaves = chaveUrls ? chaveUrls.split(',') : []
        Promise.all(
            chaves.map((k) =>
                carregar(k.slice(k.indexOf('=') + 1)).then((g) => ({ uf: k.slice(0, k.indexOf('=')), g })),
            ),
        )
            .then((estados) => {
                if (cancelado) return
                const todas = estados.flatMap(({ uf, g }) => g.features.map((f) => ({ uf, f })))
                const colecao = { type: 'FeatureCollection', features: todas.map((x) => x.f) }
                const caminho = geoPath(
                    geoMercator().fitSize([viewWidth, viewHeight], colecao as unknown as GeoPermissibleObjects),
                )
                setErro(null)
                setDesenho({
                    chave: chaveUrls,
                    formas: todas.map(({ uf, f }) => ({
                        uf,
                        id: f.properties.id,
                        nome: f.properties.name,
                        d: caminho(f.geometry as GeoPermissibleObjects) ?? '',
                    })),
                })
            })
            .catch((e: unknown) => {
                if (!cancelado) setErro(e instanceof Error ? e.message : 'Erro ao carregar o mapa.')
            })
        return () => {
            cancelado = true
        }
    }, [chaveUrls, viewWidth, viewHeight])

    const pronto = desenho !== null && desenho.chave === chaveUrls
    const formas = pronto ? desenho.formas : SEM_FORMAS
    const municipios = useMemo(
        () => resolverMunicipios(formas, { quantidade, valor, comarcas, selecionadas: selected }, porUf),
        [formas, quantidade, valor, comarcas, selected, porUf],
    )

    const resumo = resumoMapa(municipios)
    const semComarca = calcularSemComarca(quantidade, valor)
    const capInt = capital ? capitalInterior(quantidade, capital) : null
    const proporcao = aCadaDez(resumo.totalProcessos, totalJulgados)
    const terceira = calcularRevertidos(revertidos, resumo.totalProcessos)
    const plural = textos.categoriaPlural ?? 'extintos'

    const clicar = (m: MunicipioResolvido<Forma>) => {
        if (m.comarca && onSelect) onSelect(m.comarca)
    }
    const tecla = (e: KeyboardEvent<SVGPathElement>, m: MunicipioResolvido<Forma>) => {
        if (e.key !== 'Enter' && e.key !== ' ') return
        e.preventDefault()
        clicar(m)
    }
    // A dica segue o cursor, sem passar da borda direita do mapa.
    const mover = (e: MouseEvent<SVGSVGElement>) => {
        const r = caixa.current?.getBoundingClientRect()
        if (!r) return
        const x = e.clientX - r.left
        setMouse({ x: Math.min(x + 14, Math.max(r.width - 210, 0)), y: Math.max(e.clientY - r.top - 12, 0) })
    }

    let corpo
    if (erro) corpo = <p className="cmapa-msg">{erro}</p>
    else if (porUf && ufs.length === 0)
        corpo = <p className="cmapa-msg">Nenhum estado com dados de comarca neste recorte.</p>
    else if (!pronto) corpo = <p className="cmapa-msg">Carregando mapa...</p>
    else
        corpo = (
            <svg
                viewBox={`0 0 ${viewWidth} ${viewHeight}`}
                className="cmapa-svg"
                role="group"
                aria-label={`${title}: ${fmt.int(resumo.totalProcessos)} processo(s) em ${resumo.coloridos} município(s)`}
                onMouseMove={mover}
                onMouseLeave={() => setHover(null)}
            >
                <defs>
                    <pattern
                        id={padrao}
                        patternUnits="userSpaceOnUse"
                        width="6"
                        height="6"
                        patternTransform="rotate(45)"
                    >
                        <rect width="6" height="6" style={{ fill: 'var(--cmapa-zero)', fillOpacity: 0.4 }} />
                        <line
                            x1="0"
                            y1="0"
                            x2="0"
                            y2="6"
                            style={{ stroke: 'var(--border-strong)', strokeWidth: 1.5 }}
                        />
                    </pattern>
                </defs>
                {municipios.map((m) => {
                    const fill =
                        m.categoria === 'fora_base'
                            ? `url(#${padrao})`
                            : m.categoria === 'zero'
                              ? 'var(--cmapa-zero)'
                              : `rgba(255, 136, 0, ${0.18 + 0.72 * m.intensidade})`
                    const clicavel = m.comarca !== null && onSelect !== undefined
                    return (
                        <path
                            key={`${m.uf}-${m.id}`}
                            d={m.d}
                            className={clicavel ? 'cmapa-mun clicavel' : 'cmapa-mun'}
                            style={{
                                fill,
                                stroke: m.ativo ? '#FF8800' : 'var(--border-strong)',
                                strokeWidth: m.ativo ? 2 : 0.6,
                            }}
                            role={clicavel ? 'button' : undefined}
                            tabIndex={clicavel ? 0 : undefined}
                            aria-pressed={clicavel ? m.ativo : undefined}
                            aria-label={
                                clicavel
                                    ? `Filtrar pela comarca ${m.comarca}: ${fmt.int(m.quantidade)} processo(s)`
                                    : undefined
                            }
                            onMouseEnter={() => setHover(m)}
                            onFocus={() => setHover(m)}
                            onBlur={() => setHover(null)}
                            onClick={clicavel ? () => clicar(m) : undefined}
                            onKeyDown={clicavel ? (e) => tecla(e, m) : undefined}
                        />
                    )
                })}
            </svg>
        )

    return (
        <figure className="card chart cmapa">
            <figcaption className="chart-head">
                <span className="chart-head-text">
                    <span className="chart-title">{title}</span>
                </span>
                {info && (
                    <button
                        type="button"
                        className="tip cmapa-info"
                        aria-label="Informações"
                        data-tip={infoDetalhada ? `${info}\nClique para mais detalhes` : info}
                        onClick={() => infoDetalhada && setDetalhes(true)}
                    >
                        <Icon name="info" size={15} />
                    </button>
                )}
            </figcaption>
            <div className="chart-body">
                <div ref={caixa} className="cmapa-area" style={{ height }}>
                    {corpo}
                    {hover && mouse && (
                        <div className="cmapa-dica" role="status" style={{ left: mouse.x, top: mouse.y }}>
                            <strong>
                                {hover.nome.toUpperCase()}
                                {porUf ? ` · ${hover.uf}` : ''}
                            </strong>
                            {hover.comarca ? (
                                <>
                                    <span className="muted">Comarca {hover.comarca}</span>
                                    <span className="num">
                                        {fmt.int(hover.quantidade)} processo(s)
                                        {hover.valor > 0 ? ` · ${fmt.brl(hover.valor)}` : ''}
                                    </span>
                                    {(porUf || hover.tempoMedioDias !== null) && (
                                        <span className="muted">Tempo médio: {tempoMedio(hover.tempoMedioDias)}</span>
                                    )}
                                </>
                            ) : (
                                <span className="muted">Sem comarca na base</span>
                            )}
                        </div>
                    )}
                </div>
            </div>
            <div className="chart-foot cmapa-legenda">
                <div className="cmapa-colunas">
                    <div className="cmapa-coluna">
                        <div className="cmapa-chaves">
                            <span>
                                <span className="cmapa-chave" style={{ background: '#FF8800' }} />
                                {porUf ? 'Com comarca e processos' : 'Com comarca e dado'} ({resumo.coloridos})
                            </span>
                            <span>
                                <span className="cmapa-chave" style={{ background: 'var(--cmapa-zero)' }} />
                                {porUf ? 'Com comarca, zero processos no filtro' : 'Com comarca, sem dado no filtro'} (
                                {resumo.zeros})
                            </span>
                            <span>
                                <span className="cmapa-chave hachura" />
                                Sem comarca na base ({resumo.foraBase})
                            </span>
                        </div>
                        <p>Intensidade por raiz quadrada {porUf ? 'da quantidade' : 'do valor'}.</p>
                        <p className="num">
                            {porUf
                                ? `${fmt.int(resumo.totalProcessos)} processo(s) nos municípios pintados · máximo ${fmt.int(resumo.maximo)} · fonte IBGE, malha municipal simplificada.`
                                : `${fmt.int(resumo.totalProcessos)} processo(s) nos municípios pintados (soma) · máximo ${fmt.int(resumo.maximo)} processo(s) · fonte IBGE, malha municipal simplificada.`}
                        </p>
                        {porUf && ufs.length > 0 && <p>Estado(s) exibido(s): {ufs.join(', ')}.</p>}
                    </div>

                    {capInt && (
                        <div className="cmapa-coluna cmapa-bloco">
                            <span className="cmapa-titulo">Capital × Interior</span>
                            <span className="cmapa-par">
                                <span>
                                    <strong className="num">{fmt.dec1(capInt.capitalPct)}%</strong>
                                    <span className="num">Capital · {fmt.int(capInt.capital)}</span>
                                </span>
                                <span>
                                    <strong className="num">{fmt.dec1(capInt.interiorPct)}%</strong>
                                    <span className="num">Interior · {fmt.int(capInt.interior)}</span>
                                </span>
                            </span>
                            <span className="cmapa-barra" aria-hidden="true">
                                <span style={{ width: `${capInt.capitalPct}%`, background: '#FF8800' }} />
                                <span style={{ width: `${capInt.interiorPct}%`, background: '#64748b' }} />
                            </span>
                            {proporcao !== null && (
                                <p>
                                    A cada 10 processos julgados, <strong className="num">{fmt.dec1(proporcao)}</strong>{' '}
                                    são {plural}.
                                </p>
                            )}
                        </div>
                    )}

                    {terceira && (
                        <div className="cmapa-coluna cmapa-bloco">
                            <span className="cmapa-titulo">{textos.revertidosTitulo ?? 'Revertidas em 2G'}</span>
                            <span className="cmapa-par">
                                <span>
                                    <strong className="num cmapa-verde">{fmt.dec1(terceira.pct)}%</strong>
                                    <span className="num">
                                        {fmt.int(terceira.revertidas)}{' '}
                                        {textos.revertidosDescricao ?? 'com acórdão "Sentença Anulada"'}
                                    </span>
                                </span>
                            </span>
                            <span className="cmapa-barra" aria-hidden="true">
                                <span style={{ width: `${Math.min(terceira.pct, 100)}%`, background: '#10b981' }} />
                            </span>
                            <p>
                                A cada 10 processos {plural},{' '}
                                <strong className="num">{fmt.dec1(terceira.pct / 10)}</strong>{' '}
                                {textos.revertidosFrase ?? 'tem sentença anulada no 2ºG.'}
                            </p>
                        </div>
                    )}
                </div>

                {semComarca.quantidade > 0 && (
                    <p className="cmapa-aviso num">
                        <strong>⚠ {fmt.int(semComarca.quantidade)}</strong>
                        <span>
                            processo(s) sem comarca preenchida no cadastro
                            {semComarca.valor > 0 ? ` · ${fmt.brl(semComarca.valor)}` : ''} — não aparecem no mapa.
                        </span>
                    </p>
                )}
            </div>

            {detalhes && infoDetalhada && (
                <Modal title={title} onClose={() => setDetalhes(false)}>
                    <p className="cmapa-detalhes">{infoDetalhada}</p>
                </Modal>
            )}
        </figure>
    )
}
