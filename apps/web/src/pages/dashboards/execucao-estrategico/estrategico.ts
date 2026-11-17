import type { Meta, Point } from '../../../types/index.ts'

// A Execução Estratégico Geral (NG): a página da v1 NG/ExecucaoEstrategicoGeral.tsx. A API devolve as 8 chamadas que
// a página fazia (Condenação e Acordos no período, sem período e no período anterior; a Confecção CS), só com os
// campos usados (dashboards/execucao_estrategico.py); a soma, o escopo e os merges são os da v1, aqui.
// Só lógica pura (testada em estrategico.test.ts).

type Bloco = { stats: Record<string, unknown> } & Record<string, unknown>

export type EstrategicoResponse = {
    meta: Meta
    condenacao?: { atual: Bloco; historico: Bloco; anterior: Bloco }
    acordos?: { atual: Bloco; historico: Bloco; anterior: Bloco }
    confeccao?: Bloco
    confeccao_por_atividade?: Bloco
    periodo_anterior?: { from: string; to: string }
    atividades_confeccao?: string[] // as da Confecção CS da unidade (LA e RJ têm também a antiga, sem grau)
}

export type Escopo = 'ambos' | 'condenacao' | 'acordos'
export const ESCOPOS: { value: Escopo; label: string }[] = [
    { value: 'ambos', label: 'Ambos' },
    { value: 'condenacao', label: 'Condenação' },
    { value: 'acordos', label: 'Acordos' },
]
export const escopoDe = (valores: string[] | undefined): Escopo =>
    valores?.[0] === 'condenacao' || valores?.[0] === 'acordos' ? valores[0] : 'ambos'

// v1: ATIVIDADES_CONFECCAO_CS (NG; a resposta traz as da unidade em `atividades_confeccao`).
export const ATIVIDADES_CONFECCAO_CS = [
    'Elaborar Cumprimento de Sentença (1G)',
    'Elaborar Cumprimento de Sentença (2G)',
    'Manifestação Cálculo 1',
    'Manifestação Cálculo 2',
]

// --- leitura solta ---

export const numero = (v: unknown): number | null => (typeof v === 'number' && Number.isFinite(v) ? v : null)
const n0 = (v: unknown) => numero(v) ?? 0
const obj = (v: unknown): Record<string, unknown> =>
    typeof v === 'object' && v !== null && !Array.isArray(v) ? (v as Record<string, unknown>) : {}
export const objetos = (v: unknown): Record<string, unknown>[] =>
    Array.isArray(v) ? v.filter((x): x is Record<string, unknown> => typeof x === 'object' && x !== null) : []
const texto = (v: unknown) => (v === null || v === undefined ? '' : String(v))
const numeros = (v: unknown): number[] => (Array.isArray(v) ? v.filter((x): x is number => typeof x === 'number') : [])
export const pontos = (v: unknown): Point[] => objetos(v).map((p) => ({ name: texto(p.name), value: n0(p.value) }))

// --- os helpers da v1 (mesmas regras) ---

// mergeChartDataPoints: soma `value` pelo `name`, do maior para o menor.
export function somaPorNome(...listas: Point[][]): Point[] {
    const totais = new Map<string, number>()
    for (const p of listas.flat()) totais.set(p.name, (totais.get(p.name) ?? 0) + p.value)
    return [...totais].map(([name, value]) => ({ name, value })).sort((a, b) => b.value - a.value)
}

// mergeAnoAjuizamentoDataPoints: soma `value` e `valor_causa`, em ordem de nome (ano).
export function somaAnoAjuizamento(...listas: unknown[]): { name: string; value: number; valorCausa: number }[] {
    const acc = new Map<string, { value: number; valorCausa: number }>()
    for (const p of listas.flatMap(objetos)) {
        const nome = texto(p.name)
        const a = acc.get(nome) ?? { value: 0, valorCausa: 0 }
        a.value += n0(p.value)
        a.valorCausa += n0(p.valor_causa)
        acc.set(nome, a)
    }
    return [...acc].map(([name, a]) => ({ name, ...a })).sort((a, b) => a.name.localeCompare(b.name))
}

export type Comarca = { name: string; value: number; valor: number; tempoMedio: number | null }

// mergeComarcaDataPoints: soma quantidade e valor; o tempo médio é a média ponderada pela quantidade.
export function somaComarcas(...listas: unknown[]): Comarca[] {
    const acc = new Map<string, { value: number; valor: number; somaTempo: number; peso: number }>()
    for (const p of listas.flatMap(objetos)) {
        const nome = texto(p.name)
        const a = acc.get(nome) ?? { value: 0, valor: 0, somaTempo: 0, peso: 0 }
        const q = n0(p.value)
        a.value += q
        a.valor += n0(p.valor_execucao)
        const t = numero(p.tempo_medio_dias)
        if (t !== null && q > 0) {
            a.somaTempo += t * q
            a.peso += q
        }
        acc.set(nome, a)
    }
    return [...acc]
        .map(([name, a]) => ({
            name,
            value: a.value,
            valor: a.valor,
            tempoMedio: a.peso > 0 ? a.somaTempo / a.peso : null,
        }))
        .sort((a, b) => b.value - a.value)
}

// O tempo médio fixo de cada comarca (v1: tempoMedioPorComarcaFixo): o primeiro número encontrado nas listas, na
// ordem Condenação entrada, saída, total; Acordos entrada, saída, total. Não muda com o modo Total/Entradas/Saídas.
export function tempoFixoPorComarca(...listas: unknown[]): Map<string, number> {
    const m = new Map<string, number>()
    for (const p of listas.flatMap(objetos)) {
        const t = numero(p.tempo_medio_dias)
        if (t !== null && !m.has(texto(p.name))) m.set(texto(p.name), t)
    }
    return m
}

// mediaEMediana (v1): sobre as durações em dias, 2 casas; vazio = 0 e 0.
export function mediaEMediana(valores: number[]): { media: number; mediana: number } {
    if (valores.length === 0) return { media: 0, mediana: 0 }
    const v = [...valores].sort((a, b) => a - b)
    const media = v.reduce((s, x) => s + x, 0) / v.length
    const meio = Math.floor(v.length / 2)
    const mediana = v.length % 2 ? v[meio] : (v[meio - 1] + v[meio]) / 2
    const r2 = (x: number) => Math.round(x * 100) / 100
    return { media: r2(media), mediana: r2(mediana) }
}

// comparativoPercentual (v1): anterior 0 = 0; senão % com 2 casas.
export const comparativo = (atual: number, anterior: number): number =>
    anterior ? Math.round(((atual - anterior) / anterior) * 10000) / 100 : 0

const MES_ABREV = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']

// 'jan 2024' -> { ano: '2024', mes: 0 } (parseMesAbreviadoAno da v1); outro formato = null.
export function mesAno(nome: string): { ano: string; mes: number } | null {
    const m = /^([a-zà-ú]{3})\s+(\d{4})$/i.exec(nome.trim())
    if (!m) return null
    const mes = MES_ABREV.indexOf(m[1].toLowerCase())
    return mes < 0 ? null : { ano: m[2], mes }
}

// Pontos "mmm aaaa" -> { ano: [12 valores] } (mês sem dado = null).
export function porAno(pts: Point[]): Map<string, (number | null)[]> {
    const m = new Map<string, (number | null)[]>()
    for (const p of pts) {
        const ma = mesAno(p.name)
        if (!ma) continue
        const linha = m.get(ma.ano) ?? Array<number | null>(12).fill(null)
        linha[ma.mes] = p.value
        m.set(ma.ano, linha)
    }
    return new Map([...m].sort(([a], [b]) => a.localeCompare(b)))
}

// --- a página: o que cada lado contribui conforme o escopo (o lado excluído vira vazio, como na v1) ---

export type Lados = {
    escopo: Escopo
    incluirCondenacao: boolean
    incluirAcordos: boolean
    ca: Bloco // Condenação no período
    cs0: Bloco // Condenação sem período
    cp: Bloco // Condenação no período anterior
    aa: Bloco
    as0: Bloco
    ap: Bloco
}

const VAZIO: Bloco = { stats: {} }
const bloco = (v: unknown): Bloco => {
    const o = obj(v)
    return { ...o, stats: obj(o.stats) }
}

export function lados(data: EstrategicoResponse, escopo: Escopo): Lados {
    const incluirCondenacao = escopo !== 'acordos'
    const incluirAcordos = escopo !== 'condenacao'
    const c = (k: 'atual' | 'historico' | 'anterior') => (incluirCondenacao ? bloco(data.condenacao?.[k]) : VAZIO)
    const a = (k: 'atual' | 'historico' | 'anterior') => (incluirAcordos ? bloco(data.acordos?.[k]) : VAZIO)
    return {
        escopo,
        incluirCondenacao,
        incluirAcordos,
        ca: c('atual'),
        cs0: c('historico'),
        cp: c('anterior'),
        aa: a('atual'),
        as0: a('historico'),
        ap: a('anterior'),
    }
}

const st = (b: Bloco, k: string) => n0(b.stats[k])

export type TaxaAtualizacao = {
    linhas: {
        fluxo: string
        quantidade: number
        semValor: number
        valorDecisao: number
        valorExecucao: number
        aumento: number
        taxa: number | null
    }[]
    total: number | null
    ano: number | null
    porMes: { mes: number; valorSentenca: number; valorAcordao: number; taxa: number | null; quantidade: number }[]
    semValor: { processo: string; fluxo: string; dataEntrada: string | null; faltando: string[] }[]
}

function lerTaxa(v: unknown): TaxaAtualizacao | null {
    const o = obj(v)
    if (!o.total && !o.linhas) return null
    const linha = (x: Record<string, unknown>) => ({
        fluxo: texto(x.fluxo),
        quantidade: n0(x.quantidade),
        semValor: n0(x.sem_valor),
        valorDecisao: n0(x.valor_decisao),
        valorExecucao: n0(x.valor_execucao),
        aumento: n0(x.aumento),
        taxa: numero(x.taxa),
    })
    return {
        linhas: objetos(o.linhas).map(linha),
        total: numero(obj(o.total).taxa),
        ano: numero(o.ano),
        porMes: objetos(o.por_mes).map((m) => ({
            mes: n0(m.mes),
            valorSentenca: n0(m.valor_sentenca),
            valorAcordao: n0(m.valor_acordao),
            taxa: numero(m.Total),
            quantidade: n0(m.quantidade),
        })),
        semValor: objetos(o.sem_valor_processos).map((p) => ({
            processo: texto(p.numero_processo),
            fluxo: texto(p.fluxo),
            dataEntrada: texto(p.data_entrada) || null,
            faltando: Array.isArray(p.faltando) ? p.faltando.map(texto) : [],
        })),
    }
}

// Os 12 cards da seção 01, com as fórmulas da v1.
export function indicadores(l: Lados) {
    const { ca, cs0, cp, aa, as0, ap } = l
    const total = st(cs0, 'total_em_execucao') + st(as0, 'total_em_execucao_acordos_NG')
    const valorTotal = st(cs0, 'valor_total_em_execucao') + st(as0, 'valor_total_em_execucao_acordos_NG')
    const entradas = st(ca, 'total_em_execucao') + st(aa, 'total_entrada_execucao_acordos_periodo_NG')
    const entradasAnt = st(cp, 'total_em_execucao') + st(ap, 'total_entrada_execucao_acordos_periodo_NG')
    const saidas = st(ca, 'total_saida_execucao_periodo') + st(aa, 'total_saida_execucao_acordos_periodo_NG')
    const saidasAnt = st(cp, 'total_saida_execucao_periodo') + st(ap, 'total_saida_execucao_acordos_periodo_NG')
    const valorEntrada = st(ca, 'valor_em_execucao') + st(aa, 'valor_entrada_execucao_acordos_periodo_NG')
    const valorEntradaAnt = st(cp, 'valor_em_execucao') + st(ap, 'valor_entrada_execucao_acordos_periodo_NG')
    const valorSaida = st(ca, 'valor_execucao_saida_periodo') + st(aa, 'valor_saida_execucao_acordos_periodo_NG')
    const valorSaidaAnt = st(cp, 'valor_execucao_saida_periodo') + st(ap, 'valor_saida_execucao_acordos_periodo_NG')
    // Média e mediana: as durações dos dois lados juntas (não a média das médias), como a v1.
    const tempo = mediaEMediana([
        ...numeros(ca.stats.duracoes_tempo_execucao_NG),
        ...numeros(aa.stats.duracoes_tempo_execucao_acordos_NG),
    ])
    const tempoAnt = mediaEMediana([
        ...numeros(cp.stats.duracoes_tempo_execucao_NG),
        ...numeros(ap.stats.duracoes_tempo_execucao_acordos_NG),
    ])
    const taxa = lerTaxa(ca.stats.taxa_atualizacao_execucao_NG)
    const taxaAnt = lerTaxa(cp.stats.taxa_atualizacao_execucao_NG)
    return {
        total,
        valorTotal,
        ticketTotal: total > 0 ? valorTotal / total : 0,
        entradas,
        compEntradas: comparativo(entradas, entradasAnt),
        valorRemanescente: st(cs0, 'valor_remanescente_em_execucao'),
        saidas,
        compSaidas: comparativo(saidas, saidasAnt),
        saidasIncontroverso: st(ca, 'total_incontroverso_saida_execucao_periodo'),
        mediaTempo: tempo.media,
        compMediaTempo: comparativo(tempo.media, tempoAnt.media),
        medianaTempo: tempo.mediana,
        compMedianaTempo: comparativo(tempo.mediana, tempoAnt.mediana),
        estoqueInicial: st(ca, 'estoque_inicial') + st(aa, 'estoque_inicial_execucao_acordos_NG'),
        valorEntrada,
        compValorEntrada: comparativo(valorEntrada, valorEntradaAnt),
        ticketEntrada: entradas > 0 ? valorEntrada / entradas : 0,
        valorIncontroverso: st(ca, 'valor_incontroverso_saida_execucao_periodo'),
        valorSaida,
        compValorSaida: comparativo(valorSaida, valorSaidaAnt),
        // A v1 soma o TED dos dois lados (o comentário dela diz "só Condenação", mas o código soma).
        valorTed: st(ca, 'valor_ted_saida_execucao_periodo') + st(aa, 'valor_ted_saida_execucao_acordos_periodo_NG'),
        taxa,
        compTaxa: taxa?.total != null && taxaAnt?.total != null ? comparativo(taxa.total, taxaAnt.total) : null,
    }
}

// As opções dos filtros: as dos dois lados juntas (das chamadas no período, sem o escopo), como a v1.
export function opcoes(data: EstrategicoResponse) {
    const c = obj(obj(data.condenacao?.atual).stats)
    const a = obj(obj(data.acordos?.atual).stats)
    const junta = (x: unknown, y: unknown) =>
        [...new Set([...(Array.isArray(x) ? x : []), ...(Array.isArray(y) ? y : [])].map(texto).filter(Boolean))].sort()
    return {
        ufs: junta(c.execucao_uf_opcoes_NG, a.execucao_acordos_uf_opcoes_NG),
        comarcas: junta(c.execucao_comarca_opcoes_NG, a.execucao_acordos_comarca_opcoes_NG),
        materias: junta(c.execucao_materia_opcoes_NG, a.execucao_acordos_materia_opcoes_NG),
        subfases: junta(c.execucao_subfase_opcoes_NG, a.execucao_acordos_subfase_opcoes_NG),
    }
}

export type Fluxo = '1G' | '2G' | 'CS (sem grau)' | 'Outros'

// As séries mensais da seção 02 (somadas pelo mesmo "mmm aaaa").
export function series(l: Lados) {
    const { cs0, as0 } = l
    const entrada = somaPorNome(
        pontos(cs0.quantidade_entrada_execucao_por_mes),
        pontos(as0.quantidade_entrada_execucao_acordos_por_mes_NG),
    )
    const saida = somaPorNome(
        pontos(cs0.quantidade_saida_execucao_por_mes),
        pontos(as0.quantidade_saida_execucao_acordos_por_mes_NG),
    )
    const valorEntrada = somaPorNome(
        pontos(cs0.valor_entrada_execucao_por_mes),
        pontos(as0.valor_entrada_execucao_acordos_por_mes_NG),
    )
    const valorSaida = somaPorNome(
        pontos(cs0.valor_saida_execucao_por_mes),
        pontos(as0.valor_saida_execucao_acordos_por_mes_NG),
    )
    // A v1 soma o tempo médio dos dois lados no mês (comportamento dela, avisado na descrição do gráfico).
    const tempoMedio = somaPorNome(
        pontos(cs0.execucao_media_tempo_por_mes),
        pontos(as0.execucao_acordos_media_tempo_por_mes_NG),
    )
    const qtdEntradaAno = porAno(entrada)
    const valorEntradaAno = porAno(valorEntrada)
    // Ticket médio: soma Condenação + Acordos antes de dividir.
    const ticketAno = new Map(
        [...qtdEntradaAno].map(([ano, qtds]) => [
            ano,
            qtds.map((q, i) => (q && q > 0 ? (valorEntradaAno.get(ano)?.[i] ?? 0) / q : null)),
        ]),
    )
    // Entradas por fluxo (1G, 2G, Outros da Confecção CS; Acordos), por "mmm aaaa".
    // LA e RJ: "CS (sem grau)" = a atividade antiga, sem 1G/2G; a linha só aparece se já teve dado (como a v1).
    const fluxo = new Map<string, Record<Fluxo, number>>()
    const linhasFluxo = objetos(cs0.execucao_entrada_fluxo_cs_por_mes_NG)
    for (const p of linhasFluxo) {
        fluxo.set(texto(p.name), {
            '1G': n0(p['1G']),
            '2G': n0(p['2G']),
            'CS (sem grau)': n0(p['CS (sem grau)']),
            Outros: n0(p.Outros),
        })
    }
    const temSemGrau = linhasFluxo.some((p) => n0(p['CS (sem grau)']) > 0)
    const anos = [...new Set([...porAno(entrada).keys(), ...porAno(saida).keys()])].sort()
    return {
        anos,
        qtdEntradaAno,
        qtdSaidaAno: porAno(saida),
        valorEntradaAno,
        valorSaidaAno: porAno(valorSaida),
        tempoMedioAno: porAno(tempoMedio),
        ticketAno,
        fluxo,
        temSemGrau,
        acordosEntradaAno: porAno(pontos(as0.quantidade_entrada_execucao_acordos_por_mes_NG)),
    }
}

// As distribuições da seção 02, por modo, como a v1.
export function distribuicoes(l: Lados) {
    const { ca, cs0, aa, as0 } = l
    return {
        materia: {
            total: somaPorNome(pontos(cs0.execucao_por_materia), pontos(as0.execucao_acordos_por_materia_NG)),
            qtd_entrada: somaPorNome(pontos(ca.execucao_por_materia), pontos(aa.execucao_acordos_por_materia_NG)),
            valor_entrada: somaPorNome(
                pontos(ca.valor_execucao_por_materia),
                pontos(aa.valor_execucao_acordos_por_materia_NG),
            ),
        },
        subfase: {
            total: somaPorNome(
                pontos(cs0.valor_execucao_por_subfase),
                pontos(as0.valor_execucao_acordos_por_subfase_NG),
            ),
            entrada: somaPorNome(
                pontos(ca.valor_execucao_por_subfase),
                pontos(aa.valor_execucao_acordos_por_subfase_NG),
            ),
        },
        anoEntradas: somaAnoAjuizamento(ca.execucao_por_ano_ajuizamento_NG, aa.execucao_acordos_por_ano_ajuizamento_NG),
        anoTotal: somaAnoAjuizamento(cs0.execucao_por_ano_ajuizamento_NG, as0.execucao_acordos_por_ano_ajuizamento_NG),
        comarca: (() => {
            const fixo = tempoFixoPorComarca(
                ca.execucao_por_comarca_entrada,
                ca.execucao_por_comarca_saida,
                cs0.execucao_por_comarca_total,
                aa.execucao_acordos_por_comarca_entrada_NG,
                aa.execucao_acordos_por_comarca_saida_NG,
                as0.execucao_acordos_por_comarca_total_NG,
            )
            const comFixo = (xs: Comarca[]) => xs.map((c) => ({ ...c, tempoMedio: fixo.get(c.name) ?? c.tempoMedio }))
            return {
                entrada: comFixo(
                    somaComarcas(ca.execucao_por_comarca_entrada, aa.execucao_acordos_por_comarca_entrada_NG),
                ),
                saida: comFixo(somaComarcas(ca.execucao_por_comarca_saida, aa.execucao_acordos_por_comarca_saida_NG)),
                total: comFixo(somaComarcas(cs0.execucao_por_comarca_total, as0.execucao_acordos_por_comarca_total_NG)),
            }
        })(),
        condenacaoAcordos: {
            total: [
                { name: 'Condenação', value: st(cs0, 'total_em_execucao') },
                { name: 'Acordos', value: st(as0, 'total_em_execucao_acordos_NG') },
            ],
            entrada: [
                { name: 'Condenação', value: st(ca, 'total_em_execucao') },
                { name: 'Acordos', value: st(aa, 'total_entrada_execucao_acordos_periodo_NG') },
            ],
            saida: [
                { name: 'Condenação', value: st(ca, 'total_saida_execucao_periodo') },
                { name: 'Acordos', value: st(aa, 'total_saida_execucao_acordos_periodo_NG') },
            ],
        },
    }
}

// --- Confecção CS ---

export const atividadesConfeccao = (data: EstrategicoResponse): string[] =>
    Array.isArray(data.atividades_confeccao) && data.atividades_confeccao.length > 0
        ? data.atividades_confeccao.map(texto)
        : ATIVIDADES_CONFECCAO_CS

export type TarefaCS = {
    id: string
    processo: string
    criadoEm: string | null
    prazo: string | null
    concluidoEm: string | null
    valorSentenca: number | null
    valorAcordao: number | null
    concluida: boolean
    responsavel: string
    encerradoPeloResponsavel: boolean | null
}

const tarefasCS = (v: unknown): TarefaCS[] =>
    objetos(v).map((r, i) => ({
        id: texto(r.id) || String(i),
        processo: texto(r.numero_processo),
        criadoEm: texto(r.criado_em) || null,
        prazo: texto(r.prazo) || null,
        concluidoEm: texto(r.concluido_em) || null,
        valorSentenca: numero(r.valor_sentenca),
        valorAcordao: numero(r.valor_acordao),
        concluida: r.concluida === true,
        responsavel: texto(r.funcionario_atribuido),
        encerradoPeloResponsavel:
            typeof r.encerrado_pelo_responsavel === 'boolean' ? r.encerrado_pelo_responsavel : null,
    }))

export function confeccao(data: EstrategicoResponse) {
    const c = bloco(data.confeccao)
    const pa = bloco(data.confeccao_por_atividade)
    const o = obj(c.execucao_atividades_lista_filtros_opcoes_NG)
    const lista = tarefasCS(c.execucao_atividades_lista_NG)
    return {
        total: numero(c.stats.total_atividades_criadas_execucao_NG),
        abertas: numero(c.stats.atividades_execucao_abertas_NG),
        concluidas: numero(c.stats.atividades_execucao_concluidas_NG),
        porAtividade: objetos(pa.execucao_atividades_criadas_por_atividade_NG).map((r) => ({
            name: texto(r.name),
            concluidos: n0(r.concluidos),
            abertas: n0(r.abertas),
        })),
        motivos: pontos(c.execucao_nao_cumprido_por_motivo_NG),
        porFuncionario: objetos(c.execucao_taxa_conclusao_por_funcionario_NG).map((r) => ({
            name: texto(r.name),
            cumpridas: n0(r.encerrado_cumprido),
            percent: numero(r.percent),
        })),
        lista,
        concluidasLista: lista.filter((t) => t.concluida),
        abertasLista: tarefasCS(c.execucao_atividades_abertas_NG),
        situacoes: objetos(o.situacoes).map((s) => ({ id: texto(s.id), label: texto(s.label) || texto(s.id) })),
        funcionarios: Array.isArray(o.funcionarios) ? o.funcionarios.map(texto).filter(Boolean) : [],
    }
}

// --- Alvarás expedidos ---

export type AlvaraDia = { data: string; quantidade: number; valor: number }
export type Alvara = {
    processo: string
    origem: 'Condenação' | 'Acordo'
    subfase: string
    materia: string
    tipo: string
    expedicao: string | null
    expedicaoIncontroverso: string | null
    valor: number | null
    valorIncontroverso: number | null
}

export function alvaras(l: Lados) {
    const dias = (v: unknown): AlvaraDia[] =>
        objetos(v).map((r) => ({ data: texto(r.data), quantidade: n0(r.quantidade), valor: n0(r.valor) }))
    const lista = (v: unknown, origem: Alvara['origem']): Alvara[] =>
        objetos(v).map((r) => ({
            processo: texto(r.numero_processo),
            origem,
            subfase: texto(r.subfase),
            materia: texto(r.materia),
            tipo: texto(r.tipo_alvara),
            expedicao: texto(r.data_expedicao_alvara) || null,
            expedicaoIncontroverso: texto(r.data_expedicao_alvara_incontroverso) || null,
            valor: numero(r.valor_alvara),
            valorIncontroverso: numero(r.valor_alvara_incontroverso),
        }))
    const todos = [
        ...lista(l.cs0.execucao_alvara_expedido_lista_NG, 'Condenação'),
        ...lista(l.as0.execucao_acordos_alvara_expedido_lista_NG, 'Acordo'),
    ].sort((a, b) => (b.expedicao ?? '').localeCompare(a.expedicao ?? ''))
    return {
        condenacao: dias(l.cs0.execucao_alvaras_expedidos_por_dia_NG),
        acordos: dias(l.as0.execucao_acordos_alvaras_expedidos_por_dia_NG),
        lista: todos,
    }
}

// Por mês de um ano (12 valores) ou por dia de um mês: as somas de quantidade e valor dos alvarás.
export function alvarasPorMes(dias: AlvaraDia[], ano: string) {
    const qtd = Array<number>(12).fill(0)
    const valor = Array<number>(12).fill(0)
    for (const d of dias) {
        if (d.data.slice(0, 4) !== ano) continue
        const m = Number(d.data.slice(5, 7)) - 1
        if (m < 0 || m > 11) continue
        qtd[m] += d.quantidade
        valor[m] = Math.round((valor[m] + d.valor) * 100) / 100
    }
    return { qtd, valor }
}

export function alvarasPorDia(dias: AlvaraDia[], ano: string, mes: number) {
    const total = new Date(Number(ano), mes + 1, 0).getDate()
    const prefixo = `${ano}-${String(mes + 1).padStart(2, '0')}-`
    const qtd = Array<number>(total).fill(0)
    const valor = Array<number>(total).fill(0)
    for (const d of dias) {
        if (!d.data.startsWith(prefixo)) continue
        const i = Number(d.data.slice(8, 10)) - 1
        qtd[i] += d.quantidade
        valor[i] = Math.round((valor[i] + d.valor) * 100) / 100
    }
    return { dias: total, qtd, valor }
}

// Feriados fixos da v1 (ExecucaoAlvaraExpedidoList): MM-DD. Os móveis não entram, como na v1.
const FERIADOS = new Set(['01-01', '04-21', '05-01', '09-07', '10-12', '11-02', '11-15', '11-20', '12-25'])
const util = (d: Date) => d.getUTCDay() !== 0 && d.getUTCDay() !== 6 && !FERIADOS.has(d.toISOString().slice(5, 10))

// Previsão de compensação: a expedição + 5 dias úteis (ISO 'aaaa-mm-dd').
export function previsaoCompensacao(expedicao: string): string {
    const d = new Date(`${expedicao.slice(0, 10)}T00:00:00Z`)
    let n = 0
    while (n < 5) {
        d.setUTCDate(d.getUTCDate() + 1)
        if (util(d)) n++
    }
    return d.toISOString().slice(0, 10)
}

// Dias úteis de hoje até a previsão (negativo = atraso).
export function diasUteisAte(previsao: string, hoje: string): number {
    const a = new Date(`${hoje.slice(0, 10)}T00:00:00Z`)
    const b = new Date(`${previsao.slice(0, 10)}T00:00:00Z`)
    if (a.getTime() === b.getTime()) return 0
    const sinal = b > a ? 1 : -1
    let n = 0
    const d = new Date(a)
    while (d.getTime() !== b.getTime()) {
        d.setUTCDate(d.getUTCDate() + sinal)
        if (util(d)) n += sinal
    }
    return n
}
