import type { JulgadosAcordaosResponse } from '../../pages/dashboards/julgados-acordaos/types.ts'
import type { DashboardFilters, DashboardQuery } from '../../types/index.ts'
import { metaFor } from './helpers.ts'

// Julgados Acórdãos fictício: uma base de acórdãos inventada (determinística, sem Math.random) e as mesmas contas
// da API em cima dela, com o período e os filtros da tela. Assim, no mock, clicar num gráfico filtra de verdade.
// NG usa os nomes _NG (várias UFs e os recursos ao STJ/STF); LA_AM usa _LA e LA_RJ usa _RJ, como as rotas da v1.

type Categoria = 'procedente' | 'improcedente' | 'extinto'

type Linha = {
    id: number
    numero: string
    materia: string
    competencia: string
    comarca: string
    uf: string
    relator: string
    categoria: Categoria | null
    status2g: string
    motivo: string
    ajuizamento: string | null
    sentenca: string
    acordao: string | null
    valorCausa: number
    valorAcordao: number | null
    embargos: string | null
    statusEmbargos: string
    resultadoEmbargos: string | null
    fase: string
    subfase: string
    situacao: string
}

const HOJE = '2026-11-16'
const INICIO = '2024-07-01'
const MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
const MATERIAS = [
    'ANP',
    'ANP',
    'CESTA',
    'PARC_CRED_PESS',
    'SEGURO',
    'MORA',
    'JUROS_ABUSIVOS',
    'TIT_CAP',
    'EMISSAO_EXTRATO',
]
const COMPETENCIAS = ['Cível', 'Cível', 'Juizado Especial Cível', 'Consumidor', 'Fazenda Pública']
const RELATORES = [
    'Ana Paula Ribeiro',
    'Carlos Eduardo Menezes',
    'Flávia Nogueira',
    'João Batista Farias',
    'Mariana Couto',
    'Paulo Henrique Lins',
    'Roberta Sales',
    'Sérgio Albuquerque',
]
const MOTIVOS_EXTINCAO = [
    'Ilegitimidade passiva',
    'Falta de interesse de agir',
    'Litispendência',
    'Abandono da causa',
    '',
]
const MOTIVOS_IMPROCEDENCIA = ['Ausência de provas', 'Contratação regular', 'Prescrição', 'Decadência', '']
const SITUACOES = ['ATIVO', 'ATIVO', 'ATIVO', 'ATIVO', 'ATIVO', 'ATIVO', 'ARQUIVADO', 'SUSPENSO/SOBRESTADO']
const STATUS_EMBARGO_ORDEM = [
    'Revertido Ganho',
    'Ganho Ampliado',
    'Ganho Reduzido',
    'Status Mantido',
    'Revertido Perda',
    'Revisar Classificação',
    'Sem resultado lançado',
]

// Comarcas por UF (a primeira de cada UF é a capital) e o peso de cada UF.
type Unidade = { suf: 'NG' | 'LA' | 'RJ'; linhas: number; ufs: [string, number, string[]][]; seed: number }
const UNIDADES: Record<string, Unidade> = {
    NG: {
        suf: 'NG',
        linhas: 820,
        seed: 7,
        ufs: [
            ['AM', 0.78, ['Manaus', 'Manaus', 'Manaus', 'Parintins', 'Itacoatiara', 'Manacapuru', 'Tefé', 'Coari']],
            ['AC', 0.06, ['Rio Branco', 'Cruzeiro do Sul']],
            ['PA', 0.06, ['Belém', 'Santarém']],
            ['MA', 0.04, ['São Luís']],
            ['BA', 0.03, ['Salvador']],
            ['PB', 0.02, ['João Pessoa']],
            ['RJ', 0.01, ['Rio de Janeiro']],
        ],
    },
    LA_AM: {
        suf: 'LA',
        linhas: 480,
        seed: 13,
        ufs: [['AM', 1, ['Manaus', 'Manaus', 'Parintins', 'Itacoatiara', 'Manacapuru', 'Humaitá']]],
    },
    LA_RJ: {
        suf: 'RJ',
        linhas: 300,
        seed: 29,
        ufs: [
            ['RJ', 1, ['Rio de Janeiro', 'Rio de Janeiro', 'Niterói', 'Duque de Caxias', 'Nova Iguaçu', 'São Gonçalo']],
        ],
    },
}

// Gerador pseudoaleatório com semente (o mesmo mock a cada carga).
function gerador(seed: number) {
    let s = seed
    return () => {
        s = (s * 1103515245 + 12345) % 2147483648
        return s / 2147483648
    }
}

const dia = (iso: string) => new Date(`${iso}T12:00:00Z`).getTime()
const somar = (iso: string, dias: number) => new Date(dia(iso) + dias * 86_400_000).toISOString().slice(0, 10)
const entre = (iso: string) => Math.round((dia(iso) - dia(INICIO)) / 86_400_000)
const diasEntre = (a: string, b: string) => Math.round((dia(b) - dia(a)) / 86_400_000)

function gerar(u: Unidade): Linha[] {
    const r = gerador(u.seed)
    const pick = <T>(xs: T[]) => xs[Math.floor(r() * xs.length)]
    const span = entre(HOJE) - 2
    return Array.from({ length: u.linhas }, (_, i) => {
        // Mais acórdãos nos meses recentes (a base cresce com o tempo).
        const acordao = somar(INICIO, Math.floor(span * Math.sqrt(r())))
        const x = r()
        const categoria: Categoria | null =
            x < 0.46 ? 'procedente' : x < 0.76 ? 'improcedente' : x < 0.91 ? 'extinto' : null
        let uf = u.ufs[0]
        let acc = r()
        for (const item of u.ufs) {
            acc -= item[1]
            if (acc <= 0) {
                uf = item
                break
            }
        }
        const sentenca = somar(acordao, -(90 + Math.floor(r() * 420)))
        const ajuizamento = i % 37 === 5 ? null : somar(sentenca, -(200 + Math.floor(r() * 900)))
        const temEmbargos = r() < 0.26
        const embargos = temEmbargos ? somar(acordao, 20 + Math.floor(r() * 100)) : null
        const e = r()
        const statusEmbargos = !embargos
            ? ''
            : e < 0.45
              ? 'REJEITADOS'
              : e < 0.62
                ? categoria === 'procedente'
                    ? 'REVERTEU IMPROCEDÊNCIA'
                    : 'REVERTEU PROCEDÊNCIA'
                : e < 0.72
                  ? 'AUMENTOU A CONDENAÇÃO'
                  : e < 0.8
                    ? 'REDUZIU A CONDENAÇÃO'
                    : e < 0.84
                      ? 'PREJUDICADOS'
                      : ''
        const resultadoEmbargos = !embargos
            ? null
            : statusEmbargos === 'REJEITADOS'
              ? 'Status Mantido'
              : statusEmbargos === 'REVERTEU PROCEDÊNCIA'
                ? 'Revertido Ganho'
                : statusEmbargos === 'REVERTEU IMPROCEDÊNCIA'
                  ? 'Revertido Perda'
                  : statusEmbargos === 'AUMENTOU A CONDENAÇÃO'
                    ? 'Ganho Ampliado'
                    : statusEmbargos === 'REDUZIU A CONDENAÇÃO'
                      ? 'Ganho Reduzido'
                      : statusEmbargos === 'PREJUDICADOS'
                        ? 'Revisar Classificação'
                        : 'Sem resultado lançado'
        const subida = r()
        const subfase =
            u.suf === 'NG' && categoria === 'improcedente' && subida < 0.12
                ? 'Recurso Especial (STJ)'
                : u.suf === 'NG' && categoria === 'improcedente' && subida < 0.17
                  ? 'Recurso Extraordinário (STF)'
                  : pick([
                        'Aguardando trânsito em julgado',
                        'Trânsito em julgado',
                        'Arquivado',
                        'Cumprimento de sentença',
                    ])
        return {
            id: 90_000 + i,
            numero: `${String(600_000 + i * 37).padStart(7, '0')}${String(10 + (i % 89)).padStart(2, '0')}${ajuizamento?.slice(0, 4) ?? '2022'}804${uf[0] === 'RJ' ? '0001' : '0012'}`,
            materia: i % 61 === 3 ? '' : pick(MATERIAS),
            competencia: i % 83 === 9 ? '' : pick(COMPETENCIAS),
            comarca: i % 71 === 4 ? '' : pick(uf[2]),
            uf: i % 97 === 11 ? '' : uf[0],
            relator: i % 47 === 2 ? '' : pick(RELATORES),
            categoria,
            status2g:
                categoria === 'procedente'
                    ? pick(['Procedente', 'Parcialmente procedente', 'Procedente com proveito econômico'])
                    : categoria === 'improcedente'
                      ? 'Improcedente'
                      : categoria === 'extinto'
                        ? 'Extinto sem resolução de mérito'
                        : pick(['Sentença anulada', 'Encerrado 1G', '']),
            motivo:
                categoria === 'extinto'
                    ? pick(MOTIVOS_EXTINCAO)
                    : categoria === 'improcedente'
                      ? pick(MOTIVOS_IMPROCEDENCIA)
                      : '',
            ajuizamento,
            sentenca,
            // Alguns com mérito e sem a data: não entram em nenhuma contagem (faixa "Atenção").
            acordao: i % 101 === 7 && categoria !== null ? null : acordao,
            valorCausa: Math.round((8_000 + r() * 52_000) * 100) / 100,
            valorAcordao:
                categoria === 'procedente' && i % 29 !== 1 ? Math.round((2_500 + r() * 22_000) * 100) / 100 : null,
            embargos: embargos && embargos <= HOJE ? embargos : null,
            statusEmbargos,
            resultadoEmbargos: embargos && embargos <= HOJE ? resultadoEmbargos : null,
            fase: categoria === null ? 'Recursal' : pick(['Recursal', 'Trânsito em julgado', 'Execução']),
            subfase,
            situacao: pick(SITUACOES),
        }
    })
}

const BASES = new Map<string, Linha[]>()
const baseDa = (unit: string, u: Unidade) => {
    const pronta = BASES.get(unit) ?? gerar(u)
    BASES.set(unit, pronta)
    return pronta
}

// Os nomes que a API usa quando falta o dado.
const materia = (l: Linha) => l.materia || 'Sem matéria'
const comarca = (l: Linha) => l.comarca || 'Sem comarca'
const competencia = (l: Linha) => l.competencia || 'Sem competência'
const motivo = (l: Linha) => l.motivo || 'Não informado'
const ano = (l: Linha) => l.ajuizamento?.slice(0, 4) ?? 'Sem data de ajuizamento'

// Os filtros da tela (E entre filtros, OU dentro de cada um, sem diferenciar maiúsculas), como a API.
function passa(l: Linha, f: DashboardFilters): boolean {
    const tem = (lista: string[] | undefined, v: string | null) =>
        !lista?.length || (v !== null && v !== '' && lista.some((x) => x.toLowerCase() === v.toLowerCase()))
    return (
        tem(f.materia_julgados, materia(l)) &&
        tem(f.relator_julgados, l.relator) &&
        tem(f.comarca_julgados, comarca(l)) &&
        tem(f.competencia_julgados, competencia(l)) &&
        tem(f.categoria_julgados, l.categoria) &&
        tem(f.uf_julgados, l.uf) &&
        tem(f.motivo_extincao_julgados, motivo(l)) &&
        tem(f.ano_ajuizamento_julgados, ano(l)) &&
        tem(f.resultado_embargos_julgados, l.resultadoEmbargos) &&
        tem(f.situacao_processo, l.situacao)
    )
}

const noPeriodo = (d: string | null, de: string, ate: string) => d !== null && d >= de && d <= ate
const somaDe = (xs: number[]) => xs.reduce((s, v) => s + v, 0)
const media = (xs: number[]) => (xs.length ? somaDe(xs) / xs.length : null)
const variacao = (atual: number | null, anterior: number | null) =>
    atual === null || anterior === null || anterior === 0
        ? null
        : Math.round(((atual - anterior) / anterior) * 10000) / 100

function agrupar(linhas: Linha[], chave: (l: Linha) => string) {
    const m = new Map<string, Linha[]>()
    for (const l of linhas) m.set(chave(l), [...(m.get(chave(l)) ?? []), l])
    return [...m.entries()].map(([name, ls]) => ({ name, linhas: ls }))
}

const contagem = (linhas: Linha[], chave: (l: Linha) => string) =>
    agrupar(linhas, chave)
        .map((g) => ({ name: g.name, value: g.linhas.length }))
        .sort((a, b) => b.value - a.value || a.name.localeCompare(b.name))

// Os números do card no intervalo (para o período e o anterior).
function kpis(base: Linha[], de: string, ate: string) {
    const acs = base.filter((l) => noPeriodo(l.acordao, de, ate))
    const cat = (c: Categoria) => acs.filter((l) => l.categoria === c)
    const procedentes = cat('procedente')
    const comEmbargo = base.filter((l) => l.resultadoEmbargos !== null && noPeriodo(l.embargos, de, ate))
    return {
        acs,
        comEmbargo,
        total: acs.length,
        procedentes: procedentes.length,
        improcedentes: cat('improcedente').length,
        extintos: cat('extinto').length,
        nao_classificados: acs.filter((l) => l.categoria === null).length,
        tempo_medio_dias: media(acs.map((l) => diasEntre(l.sentenca, l.acordao ?? l.sentenca))),
        // Só os que têm as duas datas (o acórdão e o de embargos).
        embargos_tempo_medio_dias: media(
            comEmbargo.flatMap((l) => (l.acordao && l.embargos ? [diasEntre(l.acordao, l.embargos)] : [])),
        ),
        valor_procedentes: Math.round(somaDe(procedentes.map((l) => l.valorCausa)) * 100) / 100,
        valor_fixado_procedentes: Math.round(somaDe(procedentes.map((l) => l.valorAcordao ?? 0)) * 100) / 100,
        embargados: comEmbargo.length,
        revertidos: comEmbargo.filter((l) => l.resultadoEmbargos === 'Revertido Ganho').length,
    }
}

const COMPARAVEIS = [
    'total',
    'procedentes',
    'improcedentes',
    'extintos',
    'nao_classificados',
    'tempo_medio_dias',
    'valor_procedentes',
    'valor_fixado_procedentes',
    'embargados',
    'revertidos',
] as const

function improcedencias(linhas: Linha[], todas: Linha[], uf: (l: Linha) => string | null) {
    const imp = linhas.filter((l) => l.categoria === 'improcedente')
    const tempoPorComarca = new Map(
        agrupar(
            todas.filter((l) => l.acordao),
            comarca,
        ).map((g) => [g.name, media(g.linhas.map((l) => diasEntre(l.sentenca, l.acordao ?? l.sentenca)))]),
    )
    return {
        porComarca: agrupar(imp, comarca)
            .map((g) => ({
                name: g.name,
                value: g.linhas.length,
                valor_causa: Math.round(somaDe(g.linhas.map((l) => l.valorCausa)) * 100) / 100,
                // A UF da comarca (a do primeiro processo que tem UF), como _uf_por_comarca da API.
                uf: g.linhas.map(uf).find((x) => x !== null) ?? null,
                tempo_medio_dias: tempoPorComarca.get(g.name) ?? null,
            }))
            .sort((a, b) => b.value - a.value),
        porMotivo: contagem(imp, motivo),
        porRelator: contagem(
            imp.filter((l) => l.relator),
            (l) => l.relator,
        ),
        total: imp.length,
        valor: Math.round(somaDe(imp.map((l) => l.valorCausa)) * 100) / 100,
        stj: imp.filter((l) => l.subfase.includes('STJ')).length,
        stf: imp.filter((l) => l.subfase.includes('STF')).length,
    }
}

const iniciais = (nome: string) =>
    nome
        .split(' ')
        .filter(Boolean)
        .map((p) => p[0])
        .slice(0, 2)
        .join('')
        .toUpperCase()

export function julgadosAcordaosFor(unit: string, query?: DashboardQuery): JulgadosAcordaosResponse {
    const meta = metaFor(unit, 'LexFlow')
    const u = UNIDADES[unit]
    if (!u) return { meta, stats: {} }
    const S = u.suf
    const de = query?.from ?? meta.from
    const ate = query?.to ?? meta.to
    const duracao = diasEntre(de, ate) + 1
    const deAnterior = somar(de, -duracao)
    const ateAnterior = somar(de, -1)

    const todas = baseDa(unit, u)
    const base = todas.filter((l) => passa(l, query?.filters ?? {}))
    const atual = kpis(base, de, ate)
    const anterior = kpis(base, deAnterior, ateAnterior)
    const historico = base.filter((l) => l.acordao !== null)
    const ufDaComarca = (l: Linha) => l.uf || null

    const stats: Record<string, unknown> = {}
    for (const k of COMPARAVEIS) {
        stats[`julgados_acordao_${k}_${S}`] = atual[k]
        stats[`comparativo_julgados_acordao_${k}_${S}`] = variacao(atual[k], anterior[k])
    }
    stats[`julgados_acordao_embargos_tempo_medio_dias_${S}`] = atual.embargos_tempo_medio_dias
    stats[`julgados_acordao_uf_opcoes_${S}`] = [...new Set(todas.map((l) => l.uf).filter(Boolean))].sort()
    stats[`julgados_comarca_opcoes_${S}`] = [...new Set(todas.map((l) => l.comarca).filter(Boolean))].sort()

    // Faixa "Atenção": histórico todo, independente do período (como a API).
    const faltando: { numero_processo: string; campo: string }[] = []
    const conta = (campo: string, linhas: Linha[]) => {
        for (const l of linhas) faltando.push({ numero_processo: l.numero, campo })
        return linhas.length
    }
    stats[`julgados_acordao_sem_relator_${S}`] = conta(
        'Relator',
        historico.filter((l) => !l.relator),
    )
    stats[`julgados_acordao_sem_materia_${S}`] = conta(
        'Matéria',
        historico.filter((l) => !l.materia),
    )
    stats[`julgados_acordao_sem_comarca_${S}`] = conta(
        'Comarca',
        historico.filter((l) => !l.comarca),
    )
    stats[`julgados_acordao_sem_competencia_${S}`] = conta(
        'Competência',
        historico.filter((l) => !l.competencia),
    )
    stats[`julgados_acordao_sem_uf_${S}`] = conta(
        'UF',
        historico.filter((l) => !l.uf),
    )
    stats[`julgados_acordao_sem_valor_pe_${S}`] = conta(
        'Valor do acórdão',
        historico.filter((l) => l.status2g === 'Procedente com proveito econômico' && l.valorAcordao === null),
    )
    stats[`julgados_acordao_merito_sem_data_${S}`] = conta(
        'Data do acórdão (mérito lançado)',
        base.filter((l) => l.acordao === null && l.categoria !== null),
    )
    stats[`julgados_acordao_data_sem_merito_${S}`] = conta(
        'Mérito do acórdão (data lançada)',
        historico.filter((l) => l.categoria === null && l.status2g === ''),
    )
    stats[`julgados_acordao_dados_faltando_${S}`] = faltando

    // Estudo das Improcedências: entrada (período) e estoque (base inteira já julgada).
    const entrada = improcedencias(atual.acs, historico, ufDaComarca)
    const estoque = improcedencias(historico, historico, ufDaComarca)
    stats[`julgados_acordao_improcedencia_valor_${S}`] = entrada.valor
    stats[`julgados_acordao_improcedencia_total_estoque_${S}`] = estoque.total
    stats[`julgados_acordao_improcedencia_valor_estoque_${S}`] = estoque.valor
    stats[`julgados_acordao_total_estoque_${S}`] = historico.length
    if (S === 'NG') {
        stats.julgados_acordao_improcedencia_stj_NG = entrada.stj
        stats.julgados_acordao_improcedencia_stf_NG = entrada.stf
        stats.julgados_acordao_improcedencia_stj_estoque_NG = estoque.stj
        stats.julgados_acordao_improcedencia_stf_estoque_NG = estoque.stf
    }

    // Ranking de relatores: os acórdãos classificados do período, da maior taxa de procedência para a menor.
    const ranking = agrupar(
        atual.acs.filter((l) => l.relator && l.categoria),
        (l) => l.relator,
    )
        .map((g) => {
            const fav = g.linhas.filter((l) => l.categoria === 'procedente').length
            const des = g.linhas.filter((l) => l.categoria === 'improcedente').length
            const outros = g.linhas.length - fav - des
            const pct = (v: number) => Math.round((v / g.linhas.length) * 1000) / 10
            return {
                name: g.name,
                initials: iniciais(g.name),
                total_casos: g.linhas.length,
                taxa_sucesso: pct(fav),
                fav,
                des,
                outros,
                percent_fav: pct(fav),
                percent_des: pct(des),
                percent_outros: pct(outros),
            }
        })
        .sort(
            (a, b) => b.taxa_sucesso - a.taxa_sucesso || b.total_casos - a.total_casos || a.name.localeCompare(b.name),
        )

    // Histórico mês a mês por categoria ('nov 2026', como a API).
    const porMes = (c: Categoria) =>
        agrupar(
            historico.filter((l) => l.categoria === c),
            (l) => (l.acordao ?? '').slice(0, 7),
        )
            .sort((a, b) => a.name.localeCompare(b.name))
            .map((g) => ({
                name: `${MESES[Number(g.name.slice(5, 7)) - 1]} ${g.name.slice(0, 4)}`,
                value: g.linhas.length,
            }))

    const embargosNoPeriodo = atual.comEmbargo.map((l) => l.resultadoEmbargos)

    return {
        meta,
        dashboard: `julgados_acordaos_${S}`,
        stats,
        [`ranking_relatores_acordao_julgados_${S}`]: ranking,
        [`julgados_acordao_por_materia_${S}`]: contagem(atual.acs, materia),
        [`historico_julgados_acordao_por_materia_${S}`]: contagem(historico, materia),
        [`julgados_acordao_por_competencia_${S}`]: contagem(atual.acs, competencia),
        [`julgados_acordao_por_comarca_${S}`]: contagem(atual.acs, comarca),
        [`julgados_acordao_por_motivo_extincao_${S}`]: contagem(
            atual.acs.filter((l) => l.categoria === 'extinto'),
            motivo,
        ),
        [`julgados_acordao_por_ano_ajuizamento_${S}`]: agrupar(atual.acs, ano)
            .map((g) => ({
                name: g.name,
                value: g.linhas.length,
                valor_causa: Math.round(somaDe(g.linhas.map((l) => l.valorCausa)) * 100) / 100,
            }))
            .sort((a, b) => a.name.localeCompare(b.name)),
        [`julgados_acordao_embargos_resultado_${S}`]: STATUS_EMBARGO_ORDEM.map((name) => ({
            name,
            value: embargosNoPeriodo.filter((r) => r === name).length,
        })),
        [`julgados_acordao_procedentes_por_mes_${S}`]: porMes('procedente'),
        [`julgados_acordao_improcedentes_por_mes_${S}`]: porMes('improcedente'),
        [`julgados_acordao_extintos_por_mes_${S}`]: porMes('extinto'),
        [`julgados_acordao_lista_${S}`]: atual.acs.map((l) => ({
            id: l.id,
            numero_processo: l.numero,
            fase: l.fase,
            subfase: l.subfase,
            status_2g: l.status2g,
            uf: l.uf,
            relator: l.relator,
            data_acordao: l.acordao,
            status_acordao_embargos: l.statusEmbargos,
            data_acordao_embargos: l.embargos,
        })),
        [`julgados_acordao_improcedencia_por_comarca_${S}`]: entrada.porComarca,
        [`julgados_acordao_improcedencia_por_comarca_estoque_${S}`]: estoque.porComarca,
        [`julgados_acordao_improcedencia_por_motivo_${S}`]: entrada.porMotivo,
        [`julgados_acordao_improcedencia_por_motivo_estoque_${S}`]: estoque.porMotivo,
        [`julgados_acordao_improcedencia_por_relator_${S}`]: entrada.porRelator,
        [`julgados_acordao_improcedencia_por_relator_estoque_${S}`]: estoque.porRelator,
    }
}
