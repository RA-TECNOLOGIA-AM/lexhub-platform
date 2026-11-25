import type { FilterField } from '../../../lib/filters.ts'
import type { DashboardFilters, Point } from '../../../types/index.ts'

// O que é comum ao Marketing (banco NG) e ao Marketing (LexPre): as duas páginas da v1 têm as mesmas seções, com
// o prefixo de cada uma nos campos (marketing_ng_ / marketing_lexpre_ng_). Só lógica pura (testada sem navegador).

// Os filtros clicáveis da v1 (pares selection_dim/selection_value), um por dimensão, com o sufixo _marketing na
// URL (app/dashboards/marketing.py e marketing_lexpre.py). Vários valores na mesma dimensão = OU, como na v1.
// O dispositivo só existe no banco NG.
export const DIMENSOES = {
    faixa_etaria_marketing: 'Faixa etária',
    canal_aquisicao_marketing: 'Canal de aquisição',
    genero_marketing: 'Gênero',
    tipo_trafego_marketing: 'Tipo de tráfego',
    ocupacao_marketing: 'Ocupação',
    dispositivo_marketing: 'Dispositivo',
    prospeccao_marketing: 'Prospecção',
    tipo_residencia_marketing: 'Tipo de residência',
    pessoas_dependentes_marketing: 'Pessoas dependentes',
    rubrica_marketing: 'Rubrica',
    categoria_marketing: 'Categoria',
    posicionamento_marketing: 'Posicionamento',
    campanha_marketing: 'Campanha',
    conjunto_marketing: 'Conjunto',
    criativo_marketing: 'Criativo',
} as const satisfies Partial<Record<keyof DashboardFilters, string>>

export type Dimensao = keyof typeof DIMENSOES

// Os gráficos (sem o prefixo) de onde sai cada dimensão: os nomes que dá para clicar, para o rótulo das etiquetas.
export const GRAFICOS_DA_DIMENSAO: Record<Dimensao, string[]> = {
    faixa_etaria_marketing: ['faixa_etaria', 'triados_faixa_etaria'],
    canal_aquisicao_marketing: [
        'origem',
        'triados_origem',
        'trackeamento_canal_aquisicao',
        'fechamento_canal_aquisicao',
    ],
    genero_marketing: ['genero', 'triados_genero'],
    tipo_trafego_marketing: ['tipo_trafego', 'triados_tipo_trafego'],
    ocupacao_marketing: ['ocupacao', 'triados_ocupacao'],
    dispositivo_marketing: ['dispositivo', 'triados_dispositivo'],
    prospeccao_marketing: ['prospeccao', 'triados_prospeccao'],
    tipo_residencia_marketing: ['triados_tipo_residencia'],
    pessoas_dependentes_marketing: ['triados_pessoas_dependentes'],
    rubrica_marketing: [
        'rubrica_campanha',
        'rubrica_protocolado',
        'ind_rubricas',
        'org_rubricas_total',
        'org_rubricas_facebook',
        'org_rubricas_instagram',
        'org_rubricas_site',
        'org_rubricas_google',
    ],
    categoria_marketing: ['trackeamento_categoria', 'fechamento_categoria', 'ind_categoria', 'org_categoria'],
    posicionamento_marketing: [
        'trackeamento_posicionamento',
        'fechamento_posicionamento',
        'ind_posicionamento',
        'org_posicionamento',
    ],
    campanha_marketing: ['trackeamento_campanha', 'fechamento_campanha', 'ind_campanha', 'org_campanha'],
    conjunto_marketing: ['ind_conjunto', 'org_conjunto'],
    criativo_marketing: ['ind_criativo', 'org_criativo'],
}

// Canais do gráfico de rubricas do Orgânico (a v1 escolhia num seletor): valor -> gráfico org_rubricas_<canal>.
export const CANAIS_ORGANICO = ['total', 'facebook', 'instagram', 'site', 'google'] as const
export type CanalOrganico = (typeof CANAIS_ORGANICO)[number]
export const ROTULO_CANAL: Record<CanalOrganico, string> = {
    total: 'Total',
    facebook: 'Facebook',
    instagram: 'Instagram',
    site: 'Site',
    google: 'Google',
}

export type InvestimentoPonto = { name: string; investimento: number; cliques: number; leads: number }
// Rubricas do Marketing NG: campanha RA x campanha NG (RubricaCampanhaPoint da v1).
export type RubricaRaNg = { name: string; ra: number; ng: number }

const num = (v: unknown): number => (typeof v === 'number' && Number.isFinite(v) ? v : 0)
const objetos = (v: unknown): Record<string, unknown>[] =>
    Array.isArray(v) ? v.filter((p): p is Record<string, unknown> => typeof p === 'object' && p !== null) : []

// Leitor da resposta: `stats` com os números e `charts` com os gráficos (no Marketing NG, a própria resposta, como
// na v1). Número sem o prefixo, ausente = 0 (como a v1); série ausente = [].
export function leitor(stats: Record<string, unknown> | undefined, charts: Record<string, unknown>, prefixo: string) {
    const s = stats ?? {}
    return {
        n: (campo: string): number => num(s[prefixo + campo]),
        serie: (grafico: string): Point[] =>
            objetos(charts[prefixo + grafico])
                .map((p) => ({ name: String(p.name ?? ''), value: num(p.value) }))
                .filter((p) => p.name !== ''),
        rubricasRaNg: (grafico: string): RubricaRaNg[] =>
            objetos(charts[prefixo + grafico])
                .map((p) => ({ name: String(p.name ?? ''), ra: num(p.ra), ng: num(p.ng) }))
                .filter((p) => p.name !== ''),
        investimento: objetos(charts[prefixo + 'investimento_cliques_leads']).map((p): InvestimentoPonto => ({
            name: String(p.name ?? ''),
            investimento: num(p.investimento),
            cliques: num(p.cliques),
            leads: num(p.leads),
        })),
        temDados: Object.keys(s).length > 0,
    }
}

export type Leitor = ReturnType<typeof leitor>

// Os filtros da página da v1, que só se ligam clicando nos gráficos (fromChart): aparecem nas etiquetas, no
// contador e no "Limpar todos", não na janela Filtros. As opções servem só para o rótulo: os nomes dos gráficos
// da dimensão + os já escolhidos.
export function filtrosDeClique(ler: Leitor, dims: Dimensao[], current: DashboardFilters = {}): FilterField[] {
    return dims.map((key) => {
        const nomes = GRAFICOS_DA_DIMENSAO[key].flatMap((g) => [
            ...ler.serie(g).map((p) => p.name),
            ...ler.rubricasRaNg(g).map((p) => p.name),
        ])
        return {
            key,
            label: DIMENSOES[key],
            options: [...new Set([...(current[key] ?? []), ...nomes])].map((v) => ({ value: v, label: v })),
            fromChart: true,
        }
    })
}

// Faixas etárias na ordem da idade (a API devolve da maior contagem para a menor).
const ORDEM_FAIXA = ['< 18', '18-24', '25-34', '35-44', '45+']
export const porFaixaEtaria = (pts: Point[]): Point[] =>
    [...pts].sort((a, b) => ORDEM_FAIXA.indexOf(a.name) - ORDEM_FAIXA.indexOf(b.name))

// --- Selos e notas dos cards de Perfil e Triados (contas sobre as séries que a API já manda) ---

const soma = (pts: Point[]) => pts.reduce((s, p) => s + p.value, 0)
const pct = (v: number, total: number) => (total > 0 ? (v / total) * 100 : 0)

// O maior item da série e o % dele no total (ex.: "Predomínio: anuncio_ng (34,4%)"); null = série vazia.
export function lider(pts: Point[]): { name: string; value: number; share: number } | null {
    const top = pts.reduce<Point | null>((m, p) => (m === null || p.value > m.value ? p : m), null)
    return top && top.value > 0 ? { ...top, share: pct(top.value, soma(pts)) } : null
}

// Total de respostas (ex.: ocupação: "115 respondentes").
export const totalDe = soma

// "Não informado" no total: quanto da série é sem resposta (0 = 100% preenchido).
export function semResposta(pts: Point[]): number {
    const vazio = pts.filter((p) => p.name.trim().toLowerCase() === 'não informado')
    return pct(soma(vazio), soma(pts))
}

// Valores que só diferem no gênero da palavra (ex.: "ativa" e "ativo" na prospecção): o mesmo valor digitado de
// dois jeitos no banco. Devolve os dois nomes e o % que somam juntos; null = nada a unificar.
export function duplicadoPorGenero(pts: Point[]): { nomes: [string, string]; share: number } | null {
    const base = (s: string) => s.trim().toLowerCase().replace(/[ao]$/, '')
    for (let i = 0; i < pts.length; i++)
        for (let j = i + 1; j < pts.length; j++)
            if (base(pts[i].name) === base(pts[j].name) && pts[i].name.toLowerCase() !== pts[j].name.toLowerCase())
                return { nomes: [pts[i].name, pts[j].name], share: pct(pts[i].value + pts[j].value, soma(pts)) }
    return null
}

// Os nomes da série com a 1ª letra maiúscula, "A vs. B" (ex.: "Orgânico vs. Pago"), na ordem da série.
export const versus = (pts: Point[]): string =>
    pts.map((p) => p.name.charAt(0).toUpperCase() + p.name.slice(1).toLowerCase()).join(' vs. ')

// --- Média salarial e pessoas dependentes (respostas da pesquisa socioeconômica) ---

export type Faixa = { name: string; rotulo: string; value: number; share: number }

const ehNaoInformado = (nome: string) => nome.trim().toLowerCase() === 'não informado'
// "2.500" -> 2500 (os números das respostas vêm com ponto de milhar).
const numeros = (nome: string): number[] => (nome.match(/\d[\d.]*/g) ?? []).map((n) => Number(n.replace(/\./g, '')))
// 2500 -> "2,5k"; 10000 -> "10k"; abaixo de mil fica como está.
const mil = (v: number) => (v >= 1000 ? `${String(v / 1000).replace('.', ',')}k` : String(v))

// "Até 2500" -> "Até 2,5k"; "De 2.500 a 5.000" -> "2,5k – 5k"; "Acima de 10.000" -> "10k+". Outro texto fica igual.
export function rotuloSalario(nome: string): string {
    const n = numeros(nome)
    const t = nome.trim().toLowerCase()
    if (n.length >= 2) return `${mil(n[0])} – ${mil(n[1])}`
    if (n.length === 1 && t.startsWith('até')) return `Até ${mil(n[0])}`
    if (n.length === 1 && (t.startsWith('acima') || t.startsWith('mais'))) return `${mil(n[0])}+`
    return nome
}

// As faixas salariais respondidas, da menor para a maior, com o % sobre quem respondeu; "Não informado" à parte
// (% sobre o total, como no selo do card).
export function faixasSalariais(pts: Point[]): { faixas: Faixa[]; naoInformado: { value: number; share: number } } {
    const total = soma(pts)
    const respondidas = pts.filter((p) => !ehNaoInformado(p.name))
    const base = soma(respondidas)
    const inicio = (p: Point) => {
        const n = numeros(p.name)
        return p.name.trim().toLowerCase().startsWith('até') ? 0 : (n[0] ?? Infinity)
    }
    const vazio = soma(pts.filter((p) => ehNaoInformado(p.name)))
    return {
        faixas: [...respondidas]
            .sort((a, b) => inicio(a) - inicio(b))
            .map((p) => ({ name: p.name, rotulo: rotuloSalario(p.name), value: p.value, share: pct(p.value, base) })),
        naoInformado: { value: vazio, share: pct(vazio, total) },
    }
}

// Pessoas dependentes: "1 pessoa" -> "1 dep."; "Acima de 6 pessoas" -> "6+ dep."; em ordem do número de pessoas,
// com o % no total. Resposta sem número (ex.: "Não informado") vai no fim, com o nome dela.
export function dependentes(pts: Point[]): Faixa[] {
    const total = soma(pts)
    const chave = (p: Point) => numeros(p.name)[0] ?? Infinity
    return [...pts]
        .sort((a, b) => chave(a) - chave(b))
        .map((p) => {
            const n = numeros(p.name)[0]
            const acima = /acima|mais/i.test(p.name)
            const rotulo = n === undefined ? p.name : `${n}${acima ? '+' : ''} dep.`
            return { name: p.name, rotulo, value: p.value, share: pct(p.value, total) }
        })
}

// --- 03 Facebook Ads ---

// % de `parte` em `total` (0 sem total).
export const participacao = (parte: number, total: number) => pct(parte, total)

// Variação % de `a` sobre `b` (ex.: CAC geral vs. CAC campanha); null sem base.
export const variacaoSobre = (a: number, b: number): number | null => (b > 0 ? ((a - b) / b) * 100 : null)

export type EtapaFunil = { nome: string; valor: number; taxa: number; largura: number }

// Funil do anúncio (cliques -> pageview -> leads -> clientes): a taxa de cada etapa sobre a anterior (a 1ª = 100%)
// e a largura da barra sobre a 1ª etapa.
export function funilAnuncio(etapas: { nome: string; valor: number }[]): EtapaFunil[] {
    const topo = etapas[0]?.valor ?? 0
    return etapas.map((e, i) => ({
        ...e,
        taxa: i === 0 ? 100 : pct(e.valor, etapas[i - 1].valor),
        largura: pct(e.valor, topo),
    }))
}

// Funil de pipeline (actions_NG_2): as etapas com saldo em barras e as zeradas agrupadas num bloco só (podem ser
// abertas). "ASSINADO" (MOTIVO_ENCERRAMENTO = 11) aparece como "Fechado / cliente". A conversão final é a da
// última etapa com saldo sobre a penúltima.
export function funilPipeline(pts: Point[]) {
    const nome = (n: string) => (n.trim().toUpperCase() === 'ASSINADO' ? 'Fechado / cliente' : n)
    const etapas = pts.map((p) => ({ name: nome(p.name), value: p.value }))
    const ativas = etapas.filter((e) => e.value > 0)
    const zeradas = etapas.filter((e) => e.value <= 0)
    const [penultima, ultima] = ativas.slice(-2)
    return {
        ativas,
        zeradas,
        maior: Math.max(0, ...ativas.map((e) => e.value)),
        conversao:
            penultima && ultima ? { de: penultima, para: ultima, taxa: pct(ultima.value, penultima.value) } : null,
    }
}

// --- 04 Fechamento de campanhas ---

export type RubricaComparada = {
    name: string
    campanha: { ng: number; ra: number }
    protocolado: { ng: number; ra: number }
    relacao: number // protocolado ÷ campanha (as duas campanhas), em %
}

// Uma linha por rubrica com a campanha e o protocolado lado a lado (os dois gráficos de rubrica da v1 juntos),
// da rubrica com mais clientes de campanha para a com menos. No LexPre (campanha única), `ra` fica 0.
export function rubricasComparadas(campanha: RubricaRaNg[], protocolado: RubricaRaNg[]): RubricaComparada[] {
    const linhas = new Map<string, RubricaComparada>()
    const linha = (name: string) => {
        if (!linhas.has(name))
            linhas.set(name, { name, campanha: { ng: 0, ra: 0 }, protocolado: { ng: 0, ra: 0 }, relacao: 0 })
        return linhas.get(name)!
    }
    for (const r of campanha) linha(r.name).campanha = { ng: r.ng, ra: r.ra }
    for (const r of protocolado) linha(r.name).protocolado = { ng: r.ng, ra: r.ra }
    const total = (v: { ng: number; ra: number }) => v.ng + v.ra
    return [...linhas.values()]
        .map((l) => ({ ...l, relacao: pct(total(l.protocolado), total(l.campanha)) }))
        .sort((a, b) => total(b.campanha) - total(a.campanha) || total(b.protocolado) - total(a.protocolado))
}

// Série simples (LexPre) no formato RA x NG, com tudo em NG.
export const comoNg = (pts: Point[]): RubricaRaNg[] => pts.map((p) => ({ name: p.name, ra: 0, ng: p.value }))

// --- 05 Análise de aquisição ---

// Rótulo da API para atendimento sem UTM (a origem do anúncio não veio).
export const EM_BRANCO = '(Em branco)'
export const ehEmBranco = (nome: string) => nome.trim().toLowerCase() === EM_BRANCO.toLowerCase()

// Quanto da série é "(Em branco)": o valor e o % no total.
export function semUtm(pts: Point[]): { value: number; share: number; total: number } {
    const total = soma(pts)
    const value = soma(pts.filter((p) => ehEmBranco(p.name)))
    return { value, share: pct(value, total), total }
}

// --- 06 Performance e 07 Orgânico ---

// As dimensões dos gráficos de distribuição (Performance e Orgânico): valor -> rótulo e filtro da página.
export const DIMS_DIST = {
    campanha: { label: 'Campanha', dim: 'campanha_marketing' },
    posicionamento: { label: 'Posicionamento', dim: 'posicionamento_marketing' },
    conjunto: { label: 'Conjunto', dim: 'conjunto_marketing' },
    criativo: { label: 'Criativo', dim: 'criativo_marketing' },
    categoria: { label: 'Categoria', dim: 'categoria_marketing' },
} as const satisfies Record<string, { label: string; dim: Dimensao }>
export type DimDist = keyof typeof DIMS_DIST
export const OPCOES_DIST = (Object.keys(DIMS_DIST) as DimDist[]).map((d) => ({ value: d, label: DIMS_DIST[d].label }))
