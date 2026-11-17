import { parseMonth } from '../../../lib/charts.ts'
import { fmt } from '../../../lib/format.ts'
import type { JulgadosAcordaos, JulgadosUnit } from './fields.ts'
import type { LinhaAcordao, PontoJulgados } from './types.ts'

// As contas da tela do Julgados Acórdãos, sem React (testadas em julgados.test.ts). Tudo sai do que a API já
// manda, com as mesmas regras da página da v1 (pages/dashboards/NG/julgados_acordao_NG.tsx).

export type Categoria = 'procedente' | 'improcedente' | 'extinto'

// As cores de categoria são as da v1 (verde, vermelho e âmbar do Tailwind), em todos os gráficos e barras.
export const CATEGORIAS: { value: Categoria; label: string; color: string }[] = [
    { value: 'procedente', label: 'Procedentes', color: '#10b981' },
    { value: 'improcedente', label: 'Improcedentes', color: '#ef4444' },
    { value: 'extinto', label: 'Extintos', color: '#f59e0b' },
]

export const rotuloCategoria = (c: Categoria) => CATEGORIAS.find((x) => x.value === c)?.label ?? c

// Status Resultante dos embargos, na ordem fixa da API (mj.STATUS_EMBARGO_ORDEM), com as cores da v1
// (lib/julgadosEmbargosStatus.ts). É também o valor do filtro resultado_embargos_julgados.
export const STATUS_EMBARGOS: { name: string; color: string }[] = [
    { name: 'Revertido Ganho', color: '#10b981' },
    { name: 'Ganho Ampliado', color: '#22c55e' },
    { name: 'Ganho Reduzido', color: '#eab308' },
    { name: 'Status Mantido', color: '#9ca3af' },
    { name: 'Revertido Perda', color: '#ef4444' },
    { name: 'Revisar Classificação', color: '#a855f7' },
    { name: 'Sem resultado lançado', color: '#475569' },
]

// Os meses no eixo dos gráficos por ano, como na v1.
export const MESES_NOME_COMPLETO = [
    'Janeiro',
    'Fevereiro',
    'Março',
    'Abril',
    'Maio',
    'Junho',
    'Julho',
    'Agosto',
    'Setembro',
    'Outubro',
    'Novembro',
    'Dezembro',
]

// Cores dos gráficos com uma linha por ano (v1): o ano atual sempre laranja e contínuo; os outros anos ciclam
// por esta paleta, tracejados.
const CORES_ANOS = ['#6366f1', '#14b8a6', '#ec4899', '#84cc16', '#0ea5e9', '#a855f7', '#eab308']
const COR_ANO_ATUAL = '#f97316'

export function coresDosAnos(anos: number[], anoAtual: number): { color: string; dashed: boolean }[] {
    let i = 0
    return anos.map((ano) =>
        ano === anoAtual
            ? { color: COR_ANO_ATUAL, dashed: false }
            : { color: CORES_ANOS[i++ % CORES_ANOS.length], dashed: true },
    )
}

// ---------- Taxa de procedência (2G) do período ----------

export type Composicao = {
    total: number
    procedentes: number
    improcedentes: number
    extintos: number
    decididos: number // procedentes + improcedentes + extintos
    naoClassificados: number
    temDados: boolean
    taxa: number // % de procedentes entre os decididos
    pct: Record<Categoria, number> // as três partes da barra (somam 100)
}

// Como o card "Taxa de procedência (2G)" da v1: campo que falta conta 0.
export function composicao(n: JulgadosAcordaos['n']): Composicao {
    const total = n.total ?? 0
    const procedentes = n.procedentes ?? 0
    const improcedentes = n.improcedentes ?? 0
    const extintos = n.extintos ?? 0
    const decididos = procedentes + improcedentes + extintos
    const temDados = decididos > 0
    const proc = temDados ? (procedentes / decididos) * 100 : 0
    const imp = temDados ? (improcedentes / decididos) * 100 : 0
    return {
        total,
        procedentes,
        improcedentes,
        extintos,
        decididos,
        naoClassificados: Math.max(total - decididos, 0),
        temDados,
        taxa: proc,
        pct: { procedente: proc, improcedente: imp, extinto: temDados ? Math.max(100 - proc - imp, 0) : 0 },
    }
}

// ---------- Histórico mês a mês (a API manda do histórico todo, sem o período) ----------

// Os gráficos de histórico por ano mostram só a partir deste ano (como na v1).
export const ANO_INICIAL_HISTORICO = 2024

export type AnoAcordaos = { ano: number } & Record<Categoria, number[]>

// Um ano por linha (os anos com acórdão, desde 2024), de janeiro a dezembro, por categoria. Mês sem acórdão da
// categoria vale 0, como na v1 (o ano atual vai a 0 nos meses que ainda não chegaram, igual lá).
export function acordaosPorAno(porMes: JulgadosAcordaos['porMes']): AnoAcordaos[] {
    const fontes: [Categoria, PontoJulgados[]][] = [
        ['procedente', porMes.procedentes],
        ['improcedente', porMes.improcedentes],
        ['extinto', porMes.extintos],
    ]
    const zeros = () => Array<number>(12).fill(0)
    const anos = new Map<number, Record<Categoria, number[]>>()
    for (const [categoria, pontos] of fontes) {
        for (const p of pontos) {
            const m = parseMonth(p.name)
            if (!m || m.year < ANO_INICIAL_HISTORICO) continue
            const ano = anos.get(m.year) ?? { procedente: zeros(), improcedente: zeros(), extinto: zeros() }
            ano[categoria][m.month - 1] = p.value
            anos.set(m.year, ano)
        }
    }
    return [...anos.entries()].sort(([a], [b]) => a - b).map(([ano, valores]) => ({ ano, ...valores }))
}

// Total do mês (procedentes + improcedentes + extintos): "Total de acórdãos por ano".
export function totalDoAno(a: AnoAcordaos): number[] {
    return a.procedente.map((p, i) => p + a.improcedente[i] + a.extinto[i])
}

// % da categoria entre os decididos do mês (uma casa, como na v1); mês sem acórdão decidido fica sem ponto.
export function taxaDoAno(a: AnoAcordaos, categoria: Categoria): (number | null)[] {
    return totalDoAno(a).map((decididos, i) =>
        decididos > 0 ? Math.round((a[categoria][i] / decididos) * 1000) / 10 : null,
    )
}

// ---------- Faixa "Atenção" (dados faltando) ----------

// As mensagens da v1, na mesma ordem; só as que têm processo.
export function avisosDadosFaltando(n: JulgadosAcordaos['n']): string[] {
    const q = (v: number | null) => fmt.int(v ?? 0)
    const regras: [number | null, string][] = [
        [
            n.meritoSemData,
            `Existem ${q(n.meritoSemData)} processo(s) com mérito do acórdão lançado e sem a data do acórdão — não entram em nenhuma contagem!`,
        ],
        [
            n.dataSemMerito,
            `Existem ${q(n.dataSemMerito)} processo(s) com data do acórdão e sem o mérito lançado — contam como "Não classificados"!`,
        ],
        [n.semRelator, `Existem ${q(n.semRelator)} processo(s) com acórdão sem o nome do relator!`],
        [n.semMateria, `Existem ${q(n.semMateria)} processo(s) com acórdão sem a matéria!`],
        [n.semComarca, `Existem ${q(n.semComarca)} processo(s) com acórdão sem a comarca!`],
        [n.semCompetencia, `Existem ${q(n.semCompetencia)} processo(s) com acórdão sem a competência!`],
        [n.semUf, `Existem ${q(n.semUf)} processo(s) com acórdão sem a UF!`],
        [
            n.semValorPe,
            `Existem ${q(n.semValorPe)} processo(s) com acórdão procedente com proveito econômico sem o valor do acórdão!`,
        ],
    ]
    return regras.filter(([v]) => (v ?? 0) > 0).map(([, msg]) => msg)
}

// Quantos processos por informação faltando, do mais comum ao menos (os botões do modal da v1).
export function contarPorCampo(itens: { campo: string }[]): [string, number][] {
    const contagem = new Map<string, number>()
    for (const item of itens) contagem.set(item.campo, (contagem.get(item.campo) ?? 0) + 1)
    return [...contagem.entries()].sort((a, b) => b[1] - a[1])
}

// ---------- Estudo das Improcedências: o mapa por comarca ----------

// Os mapas da v1: na NG, o de vários estados (as UFs com dados na base de Julgados da NG, cada uma com a sua
// capital); na LA, o do Amazonas, e no RJ, o do Rio de Janeiro, comparando só pelo nome da capital.
// Os GeoJSON ficam em public/geo/ (malha municipal simplificada do IBGE), baixados quando o mapa aparece.
export const GEO_POR_UF: Record<string, string> = {
    AC: '/geo/ac-municipios.json',
    AM: '/geo/amazonas-municipios.json',
    BA: '/geo/ba-municipios.json',
    MA: '/geo/ma-municipios.json',
    PA: '/geo/pa-municipios.json',
    PB: '/geo/pb-municipios.json',
    RJ: '/geo/rj-municipios.json',
}
export const CAPITAL_POR_UF: Record<string, string> = {
    AC: 'Rio Branco',
    AM: 'Manaus',
    BA: 'Salvador',
    MA: 'São Luís',
    PA: 'Belém',
    PB: 'João Pessoa',
    RJ: 'Rio de Janeiro',
}

export type MapaDaUnidade = {
    geo: { porUf: Record<string, string> } | { url: string }
    capital: Record<string, string> | string
}

// Objetos fixos (o mapa só busca de novo quando muda o conjunto de arquivos).
const MAPAS: Record<JulgadosUnit, MapaDaUnidade> = {
    NG: { geo: { porUf: GEO_POR_UF }, capital: CAPITAL_POR_UF },
    LA: { geo: { url: GEO_POR_UF.AM }, capital: 'Manaus' },
    RJ: { geo: { url: GEO_POR_UF.RJ }, capital: 'Rio de Janeiro' },
}
export const mapaDaUnidade = (unit: JulgadosUnit): MapaDaUnidade => MAPAS[unit]

// ---------- Lista "Acórdãos no período" ----------

export const ITENS_POR_PAGINA = 15

export type OrdemLista = 'data_recente' | 'data_antiga'

export const ORDENS_LISTA: { value: OrdemLista; label: string }[] = [
    { value: 'data_recente', label: 'Data: mais recente primeiro' },
    { value: 'data_antiga', label: 'Data: mais antiga primeiro' },
]

// Pela data do acórdão; sem data vai para o fim nas duas ordens (como na v1).
export function ordenarLista(itens: LinhaAcordao[], ordem: OrdemLista): LinhaAcordao[] {
    const sinal = ordem === 'data_recente' ? -1 : 1
    return [...itens].sort((a, b) => {
        if (!a.data_acordao && !b.data_acordao) return 0
        if (!a.data_acordao) return 1
        if (!b.data_acordao) return -1
        return sinal * a.data_acordao.localeCompare(b.data_acordao)
    })
}

// Os números de página à mostra: até 5 páginas, todas; depois, a primeira, a última e a atual com as vizinhas.
export function paginas(atual: number, total: number): number[] {
    if (total <= 5) return Array.from({ length: total }, (_, i) => i + 1)
    const set = new Set([1, total, atual, atual - 1, atual + 1])
    return [...set].filter((p) => p >= 1 && p <= total).sort((a, b) => a - b)
}

// Número do processo no padrão CNJ (NNNNNNN-DD.AAAA.J.TR.OOOO); outro formato fica como veio.
export function numeroCnj(raw: string): string {
    if (!raw) return '—'
    const d = raw.replace(/\D/g, '')
    if (d.length !== 20) return raw
    return `${d.slice(0, 7)}-${d.slice(7, 9)}.${d.slice(9, 13)}.${d.slice(13, 14)}.${d.slice(14, 16)}.${d.slice(16, 20)}`
}

// '2026-11-03' -> '03/11/2026'; sem data, '—'.
export function dataBr(iso: string | null): string {
    const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso ?? '')
    return m ? `${m[3]}/${m[2]}/${m[1]}` : '—'
}
