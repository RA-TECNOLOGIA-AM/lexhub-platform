import { useEffect, useMemo, useRef, useState } from 'react'
import { fmt } from '../../lib/format.ts'
import {
    GEO_POR_UF,
    caminho,
    municipios,
    normalizar,
    pintar,
    projecao,
    tempoMedio,
    ufsDoMapa,
    type Municipio,
    type MunicipioPintado,
    type PontoComarca,
} from '../../lib/mapa.ts'
import { ChartEmpty } from './ChartCard.tsx'

const LARGURA = 900
const ALTURA = 560

// Contornos já baixados (um arquivo por UF, ~50–300 KB): uma vez por visita.
const cache = new Map<string, Promise<Municipio[]>>()
function carregar(uf: string): Promise<Municipio[]> {
    let p = cache.get(uf)
    if (!p) {
        p = fetch(GEO_POR_UF[uf])
            .then((r) => {
                if (!r.ok) throw new Error(`Falha ao carregar o mapa (HTTP ${r.status})`)
                return r.json()
            })
            .then((geo) => municipios(geo, uf))
        p.catch(() => cache.delete(uf))
        cache.set(uf, p)
    }
    return p
}

type Props = {
    quantidade: PontoComarca[] // processos por comarca no critério escolhido (cada um com a UF)
    valor: { name: string; value: number; uf?: string }[] // valor por comarca, no mesmo critério
    comarcas: string[] // todas as comarcas da base (para separar "zero processos" de "sem comarca na base")
    selected?: string[]
    onSelect?: (comarca: string) => void
    rotuloItem?: string // "processo(s)" / "acordo(s)"
}

// Módulo: o mapa de comarcas da v1 (municípios pintados pela quantidade de processos na comarca de mesmo nome).
// Passar o cursor mostra a comarca, a quantidade, o valor e o tempo médio; clicar filtra pela comarca. Mostra só
// os estados que aparecem nos dados (o filtro de UF da página já vem aplicado).
export function MapaComarcas({
    quantidade,
    valor,
    comarcas,
    selected = [],
    onSelect,
    rotuloItem = 'processo(s)',
}: Props) {
    const ufs = useMemo(() => ufsDoMapa(quantidade), [quantidade])
    const chaveUfs = ufs.join(',')
    const [geo, setGeo] = useState<{ chave: string; lista: Municipio[] } | null>(null)
    const [erro, setErro] = useState<string | null>(null)
    const [hover, setHover] = useState<MunicipioPintado | null>(null)
    const [mouse, setMouse] = useState<{ x: number; y: number; w: number } | null>(null)
    const caixa = useRef<HTMLDivElement>(null)

    useEffect(() => {
        let cancelado = false
        if (!chaveUfs) return
        Promise.all(chaveUfs.split(',').map(carregar))
            .then((partes) => !cancelado && (setErro(null), setGeo({ chave: chaveUfs, lista: partes.flat() })))
            .catch((e: unknown) => !cancelado && setErro(e instanceof Error ? e.message : 'Erro ao carregar o mapa.'))
        return () => {
            cancelado = true
        }
    }, [chaveUfs])

    const lista = geo?.chave === chaveUfs ? geo.lista : null
    const desenho = useMemo(() => {
        if (!lista) return null
        const proj = projecao(lista, LARGURA, ALTURA)
        return pintar(lista, quantidade, valor, comarcas).map((m) => ({ ...m, d: caminho(m.municipio, proj) }))
    }, [lista, quantidade, valor, comarcas])

    const marcadas = new Set(selected.map(normalizar))
    const semComarca = {
        quantidade: quantidade.filter((p) => normalizar(p.name) === 'SEM COMARCA').reduce((s, p) => s + p.value, 0),
        valor: valor.filter((p) => normalizar(p.name) === 'SEM COMARCA').reduce((s, p) => s + p.value, 0),
    }
    const coloridos = desenho?.filter((m) => m.categoria === 'colorido') ?? []
    const resumo = {
        coloridos: coloridos.length,
        zeros: desenho?.filter((m) => m.categoria === 'zero').length ?? 0,
        fora: desenho?.filter((m) => m.categoria === 'fora_base').length ?? 0,
        total: coloridos.reduce((s, m) => s + m.quantidade, 0),
        maximo: Math.max(0, ...coloridos.map((m) => m.quantidade)),
    }

    const dica = mouse && { left: Math.min(mouse.x + 14, Math.max(mouse.w - 220, 0)), top: Math.max(mouse.y - 12, 0) }

    return (
        <div className="mapa">
            <div ref={caixa} className="mapa-area">
                {ufs.length === 0 ? (
                    <ChartEmpty>Nenhum estado com dados de comarca neste recorte.</ChartEmpty>
                ) : erro ? (
                    <ChartEmpty>{erro}</ChartEmpty>
                ) : !desenho ? (
                    <ChartEmpty>Carregando mapa…</ChartEmpty>
                ) : (
                    <svg
                        viewBox={`0 0 ${LARGURA} ${ALTURA}`}
                        role="img"
                        aria-label={`Mapa de ${rotuloItem} por comarca: ${ufs.join(', ')}`}
                        onMouseMove={(e) => {
                            const r = caixa.current?.getBoundingClientRect()
                            if (r) setMouse({ x: e.clientX - r.left, y: e.clientY - r.top, w: r.width })
                        }}
                        onMouseLeave={() => setHover(null)}
                    >
                        <defs>
                            <pattern
                                id="mapa-fora-base"
                                patternUnits="userSpaceOnUse"
                                width="6"
                                height="6"
                                patternTransform="rotate(45)"
                            >
                                <rect width="6" height="6" className="mapa-fora-fundo" />
                                <line x1="0" y1="0" x2="0" y2="6" className="mapa-fora-risco" />
                            </pattern>
                        </defs>
                        {desenho.map((m) => {
                            const ativo = marcadas.has(normalizar(m.municipio.name))
                            const clicavel = Boolean(m.comarca && onSelect)
                            return (
                                <path
                                    key={`${m.municipio.uf}-${m.municipio.id}`}
                                    d={m.d}
                                    fillRule="evenodd"
                                    className={`mapa-mun ${m.categoria}${ativo ? ' ativo' : ''}${clicavel ? ' clicavel' : ''}`}
                                    style={
                                        m.categoria === 'colorido'
                                            ? { fillOpacity: 0.18 + 0.72 * m.intensidade }
                                            : undefined
                                    }
                                    onMouseEnter={() => setHover(m)}
                                    onClick={() => clicavel && m.comarca && onSelect?.(m.comarca)}
                                >
                                    <title>{`${m.municipio.name} · ${m.municipio.uf}`}</title>
                                </path>
                            )
                        })}
                    </svg>
                )}
                {hover && dica && (
                    <div className="mapa-dica" style={dica} role="tooltip">
                        <strong>
                            {hover.municipio.name.toUpperCase()} · {hover.municipio.uf}
                        </strong>
                        {hover.comarca ? (
                            <>
                                <span className="muted">Comarca {hover.comarca}</span>
                                <span className="mapa-dica-v num">
                                    {fmt.int(hover.quantidade)} {rotuloItem}
                                    {hover.valor > 0 && ` · ${fmt.brl(hover.valor)}`}
                                </span>
                                <span className="muted">Tempo médio: {tempoMedio(hover.tempoMedio)}</span>
                            </>
                        ) : (
                            <span className="muted">Sem comarca na base</span>
                        )}
                    </div>
                )}
            </div>

            {desenho && (
                <div className="mapa-legenda small muted">
                    <span>
                        <i className="mapa-key colorido" /> Com comarca e {rotuloItem} ({resumo.coloridos})
                    </span>
                    <span>
                        <i className="mapa-key zero" /> Com comarca, zero no filtro ({resumo.zeros})
                    </span>
                    <span>
                        <i className="mapa-key fora_base" /> Sem comarca na base ({resumo.fora})
                    </span>
                    <span className="mapa-legenda-txt">
                        {fmt.int(resumo.total)} {rotuloItem} nos municípios pintados · máximo {fmt.int(resumo.maximo)} ·
                        intensidade pela raiz quadrada da quantidade · estado(s): {ufs.join(', ')} · fonte IBGE.
                    </span>
                </div>
            )}
            {semComarca.quantidade > 0 && (
                <p className="mapa-aviso small">
                    <strong className="num">{fmt.int(semComarca.quantidade)}</strong> {rotuloItem} sem comarca
                    preenchida no cadastro{semComarca.valor > 0 && ` · ${fmt.brl(semComarca.valor)}`}: não aparecem no
                    mapa.
                </p>
            )}
        </div>
    )
}
