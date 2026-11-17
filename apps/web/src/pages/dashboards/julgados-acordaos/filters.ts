import type { FilterField } from '../../../lib/filters.ts'
import type { DashboardFilters } from '../../../types/index.ts'
import { lerJulgadosAcordaos, type JulgadosAcordaos } from './fields.ts'
import { CATEGORIAS, STATUS_EMBARGOS } from './julgados.ts'
import type { JulgadosAcordaosResponse } from './types.ts'

// Os filtros do Julgados Acórdãos (sem React; testados em filters.test.ts). Os nomes dos parâmetros são os da v1
// (_parse_julgados_acordao_filtros): listas cumulativas, E entre filtros e OU dentro de cada um. Como na v1, a
// janela Filtros tem UF, situação do processo e matéria; os outros se ligam clicando nos cards e gráficos e
// aparecem só nas etiquetas de filtros ativos (fromChart).

export type JulgadosFilterKey =
    | 'materia_julgados'
    | 'relator_julgados'
    | 'comarca_julgados'
    | 'competencia_julgados'
    | 'categoria_julgados'
    | 'uf_julgados'
    | 'motivo_extincao_julgados'
    | 'ano_ajuizamento_julgados'
    | 'resultado_embargos_julgados'

// Situação do processo no LexFlow (filtro transversal da v1, lib/situacaoProcesso.ts). Sem nenhuma = todas.
export const SITUACOES = [
    { value: 'ATIVO', label: 'Ativo' },
    { value: 'SUSPENSO/SOBRESTADO', label: 'Suspenso / Sobrestado' },
    { value: 'ARQUIVADO', label: 'Arquivado' },
]

// O valor que vai para o filtro ao clicar num gráfico, como os toggles da página da v1: sem espaço sobrando, UF em
// maiúsculas; vazio não filtra (null).
export function valorDoFiltro(key: JulgadosFilterKey, raw: string): string | null {
    const v = raw.trim()
    if (!v) return null
    return key === 'uf_julgados' ? v.toUpperCase() : v
}

// Opções de matéria que não somem enquanto se filtra (useOpcoesFiltroMateria da v1): sem matéria escolhida,
// acompanham os dados; com alguma escolhida, as já vistas ficam (os gráficos encolhem para o que foi escolhido, e
// ainda dá para somar outra). O escolhido sempre aparece. Em ordem alfabética; '—' e vazio ficam de fora.
export function opcoesMantidas(anteriores: string[], atuais: string[], escolhidas: string[]): string[] {
    const limpas = (xs: string[]) => xs.map((s) => s.trim()).filter((s) => s !== '' && s !== '—')
    const base = new Set(escolhidas.length > 0 ? [...anteriores, ...limpas(atuais)] : limpas(atuais))
    for (const s of escolhidas) base.add(s)
    return [...base].sort((a, b) => a.localeCompare(b, 'pt-BR'))
}

// Memória das matérias já vistas, por unidade (o estado do hook da v1, fora do React).
export function criarMemoriaOpcoes() {
    const vistas = new Map<string, string[]>()
    return (chave: string, atuais: string[], escolhidas: string[]): string[] => {
        const opcoes = opcoesMantidas(vistas.get(chave) ?? [], atuais, escolhidas)
        vistas.set(chave, opcoes)
        return opcoes
    }
}

const toOptions = (values: string[]) => values.map((value) => ({ value, label: value }))

// As matérias do período e do histórico (na v1, os dois gráficos por matéria da página).
export const materiasDaResposta = (j: JulgadosAcordaos): string[] =>
    [...j.porMateria, ...j.historicoPorMateria].map((p) => p.name)

const memoria = criarMemoriaOpcoes()

export function julgadosFilters(
    data: JulgadosAcordaosResponse,
    current: DashboardFilters = {},
    lembrar: ReturnType<typeof criarMemoriaOpcoes> = memoria,
): FilterField[] {
    const j = lerJulgadosAcordaos(data)
    const materias = lembrar(`${data.meta.unit}:materia`, materiasDaResposta(j), current.materia_julgados ?? [])
    // Só etiqueta: o valor é o próprio rótulo, menos categoria e embargos (os textos das etiquetas da v1).
    const doGrafico = (key: JulgadosFilterKey, label: string, options: FilterField['options'] = []): FilterField => ({
        key,
        label,
        options,
        fromChart: true,
    })
    const fields: FilterField[] = [
        { key: 'uf_julgados', label: 'UF', options: toOptions(j.ufOpcoes) },
        { key: 'situacao_processo', label: 'Situação do processo', options: SITUACOES },
        { key: 'materia_julgados', label: 'Matéria', options: toOptions(materias) },
        doGrafico('relator_julgados', 'Relator'),
        doGrafico('comarca_julgados', 'Comarca'),
        doGrafico('competencia_julgados', 'Competência'),
        doGrafico(
            'categoria_julgados',
            'Categoria',
            CATEGORIAS.map((c) => ({ value: c.value, label: c.label })),
        ),
        doGrafico('motivo_extincao_julgados', 'Motivo'),
        doGrafico('ano_ajuizamento_julgados', 'Ano de ajuizamento'),
        doGrafico(
            'resultado_embargos_julgados',
            'Resultado dos embargos',
            STATUS_EMBARGOS.map((s) => ({ value: s.name, label: `Embargos: ${s.name}` })),
        ),
    ]
    return fields.filter((f) => f.key !== 'uf_julgados' || f.options.length > 0) // como na v1: sem UF na base, sem o filtro
}
