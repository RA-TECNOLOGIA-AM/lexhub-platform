import type { FilterField } from '../../../lib/filters.ts'
import type { DashboardFilters } from '../../../types/index.ts'
import { criarMemoriaOpcoes, SITUACOES } from '../julgados-acordaos/filters.ts'
import { CATEGORIAS, STATUS_EMBARGOS } from '../julgados-acordaos/julgados.ts'
import { lerJulgadosSentencas, type JulgadosSentencas } from './fields.ts'
import type { JulgadosSentencasResponse } from './types.ts'

// Os filtros do Julgados Sentenças (sem React; testados em filters.test.ts). Os nomes dos parâmetros são os da v1
// (_parse_julgados_sentenca_filtros): listas cumulativas, E entre filtros e OU dentro de cada um. Iguais aos do
// Julgados Acórdãos, com o juiz (1G) no lugar do relator. A janela Filtros tem UF, situação do processo e matéria; os
// outros se ligam clicando nos cards e gráficos e aparecem só nas etiquetas de filtros ativos (fromChart).

export type SentencasFilterKey =
    | 'materia_julgados'
    | 'juiz_julgados'
    | 'comarca_julgados'
    | 'competencia_julgados'
    | 'categoria_julgados'
    | 'uf_julgados'
    | 'motivo_extincao_julgados'
    | 'ano_ajuizamento_julgados'
    | 'resultado_embargos_julgados'

// O valor que vai para o filtro ao clicar num gráfico (como na v1): sem espaço sobrando, UF em maiúsculas; vazio
// não filtra (null).
export function valorDoFiltro(key: SentencasFilterKey, raw: string): string | null {
    const v = raw.trim()
    if (!v) return null
    return key === 'uf_julgados' ? v.toUpperCase() : v
}

const toOptions = (values: string[]) => values.map((value) => ({ value, label: value }))

// As matérias do período e do histórico (na v1, os dois gráficos por matéria da página).
export const materiasDaResposta = (j: JulgadosSentencas): string[] =>
    [...j.porMateria, ...j.historicoPorMateria].map((p) => p.name)

const memoria = criarMemoriaOpcoes()

export function sentencasFilters(
    data: JulgadosSentencasResponse,
    current: DashboardFilters = {},
    lembrar: ReturnType<typeof criarMemoriaOpcoes> = memoria,
): FilterField[] {
    const j = lerJulgadosSentencas(data)
    const materias = lembrar(`${data.meta.unit}:materia`, materiasDaResposta(j), current.materia_julgados ?? [])
    const doGrafico = (key: SentencasFilterKey, label: string, options: FilterField['options'] = []): FilterField => ({
        key,
        label,
        options,
        fromChart: true,
    })
    const fields: FilterField[] = [
        { key: 'uf_julgados', label: 'UF', options: toOptions(j.ufOpcoes) },
        { key: 'situacao_processo', label: 'Situação do processo', options: SITUACOES },
        { key: 'materia_julgados', label: 'Matéria', options: toOptions(materias) },
        doGrafico('juiz_julgados', 'Juiz'),
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
