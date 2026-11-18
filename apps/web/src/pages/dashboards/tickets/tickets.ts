import type { Meta, Point } from '../../../types/index.ts'

// Tickets (banco NG): a página da v1 NG/Tickets.tsx. A API devolve a resposta da rota /tickets da v1 sem mudança
// (app/dashboards/tickets.py); aqui só a leitura e as contas que a página da v1 fazia no navegador.
// Só lógica pura (testada em tickets.test.ts).

export type Atividade = {
    id: string
    tipo: 'success' | 'pending' | 'warning'
    categoria: string // "bug", "acesso"... (a v1 usava a categoria, ou o título, em minúsculas para as abas)
    status: string | null
    descricao: string
    usuario: string
    quando: string // "há 3 h"
    minutosAtras: number | null
    servidor: string | null // NG, LA-AM, LA-RJ
    numero: string | null // #1195
    anydesk: string | null
    url: string | null
}

export type TicketsResponse = {
    meta: Meta
    dashboard?: string
    stats?: Record<string, unknown>
    tickets_por_categoria?: unknown
    tickets_por_subcategoria?: unknown
    tickets_por_abertura?: unknown
    tickets_por_fechamento?: unknown
    tickets_por_mes?: unknown
    tickets_por_status?: unknown
    tickets_abertos_por_servidor?: unknown
    tickets_encerrados_por_servidor?: unknown
    tickets_media_encerrados_por_colaborador?: unknown
    recent_activities?: unknown
}

// Meta da Taxa de Resolução e SLA do atendimento (as constantes da página da v1).
export const META_TAXA_RESOLUCAO = 80
export const SLA_HORAS = 24
export const SERVIDORES = ['NG', 'LA-AM', 'LA-RJ']

const objetos = (v: unknown): Record<string, unknown>[] =>
    Array.isArray(v) ? v.filter((x): x is Record<string, unknown> => typeof x === 'object' && x !== null) : []
const texto = (v: unknown) => (v === null || v === undefined ? '' : String(v))
const numero = (v: unknown): number | null => (typeof v === 'number' && Number.isFinite(v) ? v : null)
const pontos = (v: unknown): Point[] => objetos(v).map((p) => ({ name: texto(p.name), value: numero(p.value) ?? 0 }))

// As iniciais do nome (v1: iniciais): as duas primeiras letras, sem símbolos.
export const iniciais = (nome: string) => (nome.replace(/[^\p{L}\p{N}]/gu, '').slice(0, 2) || '?').toUpperCase()

export const pct = (parte: number, total: number) => (total > 0 ? (parte / total) * 100 : 0)

// Duração em horas como a v1 (formatDuration): 0 -> "0h"; < 1h em minutos; até 24h em h e min; depois d e h.
export function duracaoHoras(horas: number): string {
    if (!horas) return '0h'
    if (horas < 1) return `${Math.round(horas * 60)}min`
    if (horas < 24) {
        const h = Math.floor(horas)
        const m = Math.round((horas - h) * 60)
        return m > 0 ? `${h}h ${m}min` : `${h}h`
    }
    const d = Math.floor(horas / 24)
    const r = Math.floor(horas % 24)
    return r > 0 ? `${d}d ${r}h` : `${d}d`
}

// A variação do Total contra o mesmo recorte de dias do mês anterior (v1: só com o anterior > 0).
export const variacao = (total: number, anterior: number | null): number | null =>
    anterior && anterior > 0 ? Math.round(((total - anterior) / anterior) * 10000) / 100 : null

const MES_ABREV = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']

// "jan 2026" -> { ano, mes } (tickets_por_mes da v1).
export function mesAno(nome: string): { ano: string; mes: number } | null {
    const m = /^([a-zç]{3})\s+(\d{4})$/i.exec(nome.trim())
    if (!m) return null
    const mes = MES_ABREV.indexOf(m[1].toLowerCase())
    return mes < 0 ? null : { ano: m[2], mes }
}

// Série histórica "mmm aaaa" -> um ano por linha (Jan–Dez), como os "mês a mês" da V2; o pico de toda a série.
export function porAno(pts: Point[]) {
    const anos = new Map<string, (number | null)[]>()
    let pico: { ano: string; mes: number; valor: number } | null = null
    for (const p of pts) {
        const ma = mesAno(p.name)
        if (!ma) continue
        const linha = anos.get(ma.ano) ?? Array<number | null>(12).fill(null)
        linha[ma.mes] = p.value
        anos.set(ma.ano, linha)
        if (!pico || p.value > pico.valor) pico = { ano: ma.ano, mes: ma.mes, valor: p.value }
    }
    return { anos: new Map([...anos].sort(([a], [b]) => a.localeCompare(b))), pico }
}

const TIPOS = new Set(['success', 'pending', 'warning'])

export function atividades(v: unknown): Atividade[] {
    return objetos(v).map((a, i) => ({
        id: texto(a.id) || String(i),
        tipo: (TIPOS.has(texto(a.type)) ? texto(a.type) : 'warning') as Atividade['tipo'],
        categoria: (texto(a.categoria) || texto(a.title) || 'Ticket').toLowerCase(),
        status: texto(a.status) || null,
        descricao: texto(a.description),
        usuario: texto(a.user) || 'Sistema',
        quando: texto(a.time),
        minutosAtras: numero(a.minutos_atras),
        servidor: texto(a.servidor) || null,
        numero: texto(a.ticket_numero) || null,
        anydesk: texto(a.anydesk) || null,
        url: texto(a.url) || null,
    }))
}

// As abas do feed (v1 MovimentacoesFeed): "Todos" e cada categoria, da mais frequente para a menos.
export function abasDoFeed(lista: Atividade[]): { value: string; label: string; total: number }[] {
    const cont = new Map<string, number>()
    for (const a of lista) cont.set(a.categoria, (cont.get(a.categoria) ?? 0) + 1)
    return [
        { value: 'todos', label: 'Todos', total: lista.length },
        ...[...cont]
            .sort((x, y) => y[1] - x[1])
            .map(([c, n]) => ({ value: c, label: c.charAt(0).toUpperCase() + c.slice(1), total: n })),
    ]
}

// Busca do feed: descrição, autor, #número e servidor (o "#" do começo é ignorado).
export function filtrarFeed(lista: Atividade[], aba: string, busca: string): Atividade[] {
    const termo = busca.trim().toLowerCase().replace(/^#/, '')
    return lista.filter((a) => {
        if (aba !== 'todos' && a.categoria !== aba) return false
        if (!termo) return true
        return [a.descricao, a.usuario, a.numero, a.servidor].some((v) => (v ?? '').toLowerCase().includes(termo))
    })
}

// A resposta inteira, já com os números da seção 01.
export function lerTickets(data: TicketsResponse) {
    const s = data.stats ?? {}
    const n = (k: string) => numero(s[k]) ?? 0
    const total = n('total_tickets')
    const anterior = numero(s.total_tickets_periodo_anterior)
    const encerrados = n('total_encerrados')
    const subcategorias = pontos(data.tickets_por_subcategoria)
    const totalSub = subcategorias.reduce((t, p) => t + p.value, 0)
    const semSub = subcategorias.find((p) => p.name.toLowerCase() === 'sem subcategoria')?.value ?? 0
    const media = pontos(data.tickets_media_encerrados_por_colaborador)
    const duracao = n('duracao_atendimento')
    return {
        temDados: data.stats !== undefined && Object.keys(s).length > 0,
        total,
        anterior,
        variacao: variacao(total, anterior),
        aguardando: n('tickets_ag_atendimento'),
        emAtendimento: n('tickets_atendimento'),
        encerrados,
        cancelados: n('tickets_cancelados'),
        reprovados: n('tickets_reprovados'),
        duracao,
        dentroSla: duracao <= SLA_HORAS,
        taxa: n('taxa_resolucao'),
        porCategoria: pontos(data.tickets_por_categoria),
        subcategorias,
        pctSemSubcategoria: pct(semSub, totalSub),
        abertura: pontos(data.tickets_por_abertura),
        fechamento: pontos(data.tickets_por_fechamento),
        porMes: pontos(data.tickets_por_mes),
        porStatus: pontos(data.tickets_por_status),
        abertosPorServidor: pontos(data.tickets_abertos_por_servidor),
        encerradosPorServidor: pontos(data.tickets_encerrados_por_servidor),
        mediaPorColaborador: media,
        mediaEquipe: media.length > 0 ? media.reduce((t, p) => t + p.value, 0) / media.length : 0,
        atividades: atividades(data.recent_activities),
    }
}
