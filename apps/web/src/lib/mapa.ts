// Módulo: o mapa de comarcas sem biblioteca de mapas (sem React; testado em mapa.test.ts).
// Os contornos são os municípios do IBGE (malha simplificada, public/geo/<uf>-municipios.json, só Polygon);
// a projeção é a de Mercator ajustada à caixa do desenho, como o geoMercator().fitSize da v1.

export type Anel = [number, number][] // [longitude, latitude]
export type Municipio = { id: string; name: string; uf: string; aneis: Anel[] }

type GeoJson = {
    features: { properties: { id: string | number; name: string }; geometry: { type: string; coordinates: unknown } }[]
}

// Os arquivos de contorno por UF (os mesmos da v1).
export const GEO_POR_UF: Record<string, string> = {
    AC: '/geo/ac-municipios.json',
    AM: '/geo/amazonas-municipios.json',
    BA: '/geo/ba-municipios.json',
    MA: '/geo/ma-municipios.json',
    PA: '/geo/pa-municipios.json',
    PB: '/geo/pb-municipios.json',
    RJ: '/geo/rj-municipios.json',
}

// Os municípios de um GeoJSON (Polygon e MultiPolygon; outros tipos ficam de fora).
export function municipios(geo: GeoJson, uf: string): Municipio[] {
    return geo.features.flatMap((f) => {
        const { type, coordinates } = f.geometry
        const poligonos =
            type === 'Polygon' ? [coordinates as Anel[]] : type === 'MultiPolygon' ? (coordinates as Anel[][]) : []
        if (poligonos.length === 0) return []
        return [{ id: String(f.properties.id), name: f.properties.name, uf, aneis: poligonos.flat() }]
    })
}

// Nome de comarca/município para comparar: sem acento, maiúsculo, sem espaço sobrando ("Tefé" = "TEFE").
export const normalizar = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toUpperCase().trim()

const merc = ([lon, lat]: [number, number]): [number, number] => {
    const phi = (Math.max(-85, Math.min(85, lat)) * Math.PI) / 180
    return [(lon * Math.PI) / 180, -Math.log(Math.tan(Math.PI / 4 + phi / 2))]
}

// A projeção que cabe todos os municípios em largura × altura (centralizada, com a mesma escala nos dois eixos).
export function projecao(lista: Municipio[], largura: number, altura: number) {
    let x0 = Infinity
    let y0 = Infinity
    let x1 = -Infinity
    let y1 = -Infinity
    for (const m of lista)
        for (const anel of m.aneis)
            for (const p of anel) {
                const [x, y] = merc(p)
                if (x < x0) x0 = x
                if (x > x1) x1 = x
                if (y < y0) y0 = y
                if (y > y1) y1 = y
            }
    if (!Number.isFinite(x0)) return (p: [number, number]) => p
    const escala = Math.min(largura / (x1 - x0 || 1), altura / (y1 - y0 || 1))
    const dx = (largura - (x1 - x0) * escala) / 2
    const dy = (altura - (y1 - y0) * escala) / 2
    return (p: [number, number]): [number, number] => {
        const [x, y] = merc(p)
        return [dx + (x - x0) * escala, dy + (y - y0) * escala]
    }
}

// O contorno SVG de um município ("M x,y L ... Z" por anel; furos saem com fill-rule evenodd).
export function caminho(m: Municipio, proj: (p: [number, number]) => [number, number]): string {
    return m.aneis
        .map((anel) =>
            anel
                .map((p, i) => {
                    const [x, y] = proj(p)
                    return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`
                })
                .join('')
                .concat('Z'),
        )
        .join('')
}

// Um ponto por comarca (o da API): quantidade, UF e tempo médio na comarca (dias).
export type PontoComarca = { name: string; value: number; uf: string; tempoMedio: number | null }

export type Categoria = 'colorido' | 'zero' | 'fora_base'
export type MunicipioPintado = {
    municipio: Municipio
    comarca: string | null // a comarca da base com o mesmo nome (null = "sem comarca na base")
    categoria: Categoria
    quantidade: number
    valor: number
    tempoMedio: number | null
    intensidade: number // 0–1, pela raiz quadrada da quantidade (como a v1)
}

// Casa cada município com a comarca de mesmo nome na mesma UF, como a v1 (não é dado real de jurisdição).
export function pintar(
    lista: Municipio[],
    quantidade: PontoComarca[],
    valor: { name: string; value: number; uf?: string }[],
    comarcas: string[],
): MunicipioPintado[] {
    const chave = (uf: string, nome: string) => `${uf.trim().toUpperCase()}|${normalizar(nome)}`
    const qtd = new Map(quantidade.map((p) => [chave(p.uf, p.name), p]))
    const val = new Map(valor.map((p) => [chave(p.uf ?? '', p.name), p.value]))
    const original = new Map<string, string>()
    for (const c of comarcas) if (!original.has(normalizar(c))) original.set(normalizar(c), c)
    const brutos = lista.map((m) => {
        const k = chave(m.uf, m.name)
        const comarca = original.get(normalizar(m.name)) ?? qtd.get(k)?.name ?? null
        const q = qtd.get(k)?.value ?? 0
        const categoria: Categoria = !comarca ? 'fora_base' : q > 0 ? 'colorido' : 'zero'
        return {
            municipio: m,
            comarca,
            categoria,
            quantidade: q,
            valor: val.get(k) ?? 0,
            tempoMedio: qtd.get(k)?.tempoMedio ?? null,
        }
    })
    const max = Math.max(0, ...brutos.filter((b) => b.categoria === 'colorido').map((b) => b.quantidade))
    return brutos.map((b) => ({
        ...b,
        intensidade: b.categoria === 'colorido' && max > 0 ? Math.sqrt(b.quantidade) / Math.sqrt(max) : 0,
    }))
}

// As UFs que o mapa mostra: as que têm comarca nos dados e contorno disponível.
export function ufsDoMapa(quantidade: PontoComarca[]): string[] {
    return [...new Set(quantidade.map((p) => p.uf.trim().toUpperCase()).filter((uf) => GEO_POR_UF[uf]))].sort()
}

// '0,4 dia' -> '10h'; 214,6 -> '214d 14h' (o tempo médio do detalhe da v1). null -> '—'.
export function tempoMedio(dias: number | null): string {
    if (dias === null) return '—'
    if (dias < 1) return `${Math.round(dias * 24)}h`
    const d = Math.floor(dias)
    const h = Math.round((dias - d) * 24)
    return h > 0 ? `${d}d ${h}h` : `${d}d`
}
