// Módulo: as contas do mapa de comarcas, sem React (testadas em comarcaMapa.test.ts). Cópia das regras dos mapas
// da v1 (components/dashboard/ComarcaMapaMultiUfChart.tsx, vários estados, e ComarcaMapaChart.tsx, um estado só):
// o município é casado com a comarca pelo nome normalizado (com a UF junto, no de vários estados), não por dado
// real de jurisdição.

// Um ponto do gráfico por comarca (ChartDataPoint da v1): a quantidade (ou o valor) e, no de vários estados, a UF.
export type PontoComarca = { name: string; value: number; uf?: string | null; tempoMedioDias?: number | null }

// Um município do GeoJSON (só o que as contas usam; o desenho fica no componente).
export type Municipio = { uf: string; id: string; nome: string }

export type CategoriaMunicipio = 'colorido' | 'zero' | 'fora_base'

export type MunicipioResolvido<M extends Municipio = Municipio> = M & {
    comarca: string | null // o nome como está na base (para o filtro); null = sem comarca homônima na base
    categoria: CategoriaMunicipio
    quantidade: number
    valor: number
    tempoMedioDias: number | null
    intensidade: number // 0–1: raiz quadrada da quantidade sobre a raiz da maior
    ativo: boolean // comarca no filtro em uso
}

// Sem acento, maiúsculo e sem espaço sobrando (como a v1).
export const normalizarComarca = (s: string) =>
    s
        .normalize('NFD')
        .replace(/\p{M}/gu, '') // os acentos que o NFD separou da letra
        .toUpperCase()
        .trim()

const normalizarUf = (s: string | null | undefined) => (s ?? '').trim().toUpperCase()

// Chave de casamento: no de vários estados, UF + nome; no de um estado, só o nome.
const chave = (porUf: boolean, uf: string | null | undefined, nome: string) =>
    porUf ? `${normalizarUf(uf)}|${normalizarComarca(nome)}` : normalizarComarca(nome)

// As UFs com dado e com mapa, em ordem (o de vários estados mostra só esses estados).
export function ufsComDados(quantidade: PontoComarca[], urls: Record<string, string>): string[] {
    const ufs = new Set<string>()
    for (const p of quantidade) {
        const uf = normalizarUf(p.uf)
        if (uf && urls[uf]) ufs.add(uf)
    }
    return [...ufs].sort()
}

// Cada município com a sua comarca, a categoria (pintado, zero no filtro ou sem comarca na base), a quantidade, o
// valor, o tempo médio e a intensidade da cor.
export function resolverMunicipios<M extends Municipio>(
    municipios: M[],
    dados: { quantidade: PontoComarca[]; valor: PontoComarca[]; comarcas: string[]; selecionadas: string[] },
    porUf: boolean,
): MunicipioResolvido<M>[] {
    const original = new Map<string, string>()
    for (const c of dados.comarcas) {
        const n = normalizarComarca(c)
        if (!original.has(n)) original.set(n, c)
    }
    const quantidade = new Map<string, number>()
    const tempo = new Map<string, number>()
    for (const p of dados.quantidade) {
        if (porUf && !normalizarUf(p.uf)) continue
        const k = chave(porUf, p.uf, p.name)
        quantidade.set(k, p.value)
        if (typeof p.tempoMedioDias === 'number' && Number.isFinite(p.tempoMedioDias)) tempo.set(k, p.tempoMedioDias)
    }
    const valor = new Map<string, number>()
    for (const p of dados.valor) {
        if (porUf && !normalizarUf(p.uf)) continue
        valor.set(chave(porUf, p.uf, p.name), p.value)
    }
    const ativas = new Set(dados.selecionadas.map(normalizarComarca))

    const brutos = municipios.map((m) => {
        const n = normalizarComarca(m.nome)
        const k = porUf ? `${normalizarUf(m.uf)}|${n}` : n
        const comarca = original.get(n) ?? null
        const q = quantidade.get(k) ?? 0
        const categoria: CategoriaMunicipio = !comarca ? 'fora_base' : q > 0 ? 'colorido' : 'zero'
        return {
            ...m,
            comarca,
            categoria,
            quantidade: q,
            valor: valor.get(k) ?? 0,
            tempoMedioDias: tempo.get(k) ?? null,
            ativo: ativas.has(n),
        }
    })
    // A maior quantidade: no de vários estados, entre os pintados; no de um estado, entre todos (como cada mapa da v1).
    const maior = brutos.reduce(
        (acc, m) => (porUf && m.categoria !== 'colorido' ? acc : Math.max(acc, m.quantidade)),
        0,
    )
    return brutos.map((m) => ({
        ...m,
        intensidade: m.categoria === 'colorido' && maior > 0 ? Math.sqrt(m.quantidade) / Math.sqrt(maior) : 0,
    }))
}

// Os números da legenda: quantos municípios em cada categoria, a soma pintada e o máximo.
export function resumoMapa(municipios: MunicipioResolvido[]) {
    const coloridos = municipios.filter((m) => m.categoria === 'colorido')
    return {
        coloridos: coloridos.length,
        zeros: municipios.filter((m) => m.categoria === 'zero').length,
        foraBase: municipios.filter((m) => m.categoria === 'fora_base').length,
        totalProcessos: coloridos.reduce((acc, m) => acc + m.quantidade, 0),
        maximo: coloridos.reduce((acc, m) => Math.max(acc, m.quantidade), 0),
    }
}

// Processos com a comarca vazia no cadastro ("Sem comarca"): não aparecem no mapa, a legenda avisa.
export function semComarca(quantidade: PontoComarca[], valor: PontoComarca[]) {
    const soma = (xs: PontoComarca[]) =>
        xs.filter((p) => normalizarComarca(p.name) === 'SEM COMARCA').reduce((acc, p) => acc + p.value, 0)
    return { quantidade: soma(quantidade), valor: soma(valor) }
}

export type CapitalInterior = { capital: number; interior: number; capitalPct: number; interiorPct: number }

// Soma das comarcas capitais contra as demais ("Sem comarca" fica de fora dos dois lados). capital = a capital de
// cada UF (vários estados) ou o nome da capital (um estado). null = sem nada para comparar.
export function capitalInterior(
    quantidade: PontoComarca[],
    capital: Record<string, string> | string,
): CapitalInterior | null {
    const capitais =
        typeof capital === 'string'
            ? null
            : new Map(Object.entries(capital).map(([uf, nome]) => [normalizarUf(uf), normalizarComarca(nome)]))
    let somaCapital = 0
    let interior = 0
    for (const p of quantidade) {
        const nome = normalizarComarca(p.name)
        if (nome === 'SEM COMARCA') continue
        const ehCapital = capitais
            ? normalizarUf(p.uf) !== '' && capitais.get(normalizarUf(p.uf)) === nome
            : nome === normalizarComarca(capital as string)
        if (ehCapital) somaCapital += p.value
        else interior += p.value
    }
    const total = somaCapital + interior
    if (somaCapital <= 0 && interior <= 0) return null
    return {
        capital: somaCapital,
        interior,
        capitalPct: total > 0 ? (somaCapital / total) * 100 : 0,
        interiorPct: total > 0 ? (interior / total) * 100 : 0,
    }
}

// "A cada 10 processos julgados, X são …": a soma pintada no mapa sobre o total julgado no mesmo escopo.
export function aCadaDez(totalPintado: number, totalJulgados: number | undefined): number | null {
    if (!totalJulgados || totalJulgados <= 0 || totalPintado <= 0) return null
    return (totalPintado / totalJulgados) * 10
}

// A 3ª coluna da legenda (ex.: recursos ao STJ/STF): % sobre a soma pintada no mapa.
export function revertidos(total: number | undefined, totalPintado: number) {
    if (total === undefined || totalPintado <= 0) return null
    const n = Math.max(total, 0)
    return { revertidas: n, pct: (n / totalPintado) * 100 }
}

// Tempo médio da comarca como na v1: '—' sem dado, 'Xh' abaixo de 1 dia, senão 'Xd Yh'.
export function tempoMedio(dias: number | null): string {
    if (dias === null) return '—'
    if (dias < 1) return `${Math.round(dias * 24)}h`
    const d = Math.floor(dias)
    const h = Math.round((dias - d) * 24)
    return h > 0 ? `${d}d ${h}h` : `${d}d`
}
