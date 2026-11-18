import type { JulgadosSentencasResponse } from '../../pages/dashboards/julgados-sentencas/types.ts'
import type { DashboardQuery } from '../../types/index.ts'
import { julgadosAcordaosFor } from './julgadosAcordaos.ts'

// Julgados Sentenças fictício: a mesma base inventada do Julgados Acórdãos (mock/julgadosAcordaos.ts), com os nomes
// da rota julgados_<U> da v1 (sentença, juiz). Só para ver a tela no mock: os números são os dos acórdãos, e os
// Estudos de Extinção reaproveitam o recorte das improcedências (o mock não tem a base de extintas à parte).

// Nome do campo de acórdão -> nome do campo de sentença (sem o sufixo da unidade).
function renomear(base: string): string {
    const trocas: [RegExp, string][] = [
        [/^ranking_relatores_acordao_julgados$/, 'ranking_juizes_sentenca_julgados'],
        [/^historico_julgados_acordao_por_materia$/, 'historico_julgados_por_materia'],
        [/^julgados_acordao_por_(materia|competencia|comarca|motivo_extincao|ano_ajuizamento)$/, 'julgados_por_$1'],
        [/^julgados_acordao_uf_opcoes$/, 'julgados_uf_opcoes'],
        [/^julgados_acordao_improcedencia_por_relator(_estoque)?$/, 'julgados_improcedencia_por_juiz$1'],
        [/^julgados_acordao_improcedencia_(.*)$/, 'julgados_improcedencia_$1'],
        [/^julgados_acordao_sem_relator$/, 'julgados_sentenca_sem_juiz'],
        [/^julgados_acordao_(.*)$/, 'julgados_sentenca_$1'],
        [/^comparativo_julgados_acordao_(.*)$/, 'comparativo_julgados_sentenca_$1'],
    ]
    for (const [de, para] of trocas) if (de.test(base)) return base.replace(de, para)
    return base
}

function renomearChaves(obj: Record<string, unknown>, suf: string): Record<string, unknown> {
    const fim = `_${suf}`
    return Object.fromEntries(
        Object.entries(obj).map(([k, v]) =>
            k.endsWith(fim) ? [`${renomear(k.slice(0, -fim.length))}${fim}`, v] : [k, v],
        ),
    )
}

// Uma linha da lista de acórdãos com os nomes da lista de sentenças.
const linhaSentenca = (r: Record<string, unknown>) => ({
    id: r.id,
    numero_processo: r.numero_processo,
    fase: r.fase,
    subfase: r.subfase,
    status_1g: r.status_2g,
    uf: r.uf,
    juiz: r.relator,
    data_sentenca: r.data_acordao,
    status_sentenca_embargos: r.status_acordao_embargos,
    data_sentenca_embargos: r.data_acordao_embargos,
})

export function julgadosSentencasFor(unit: string, query?: DashboardQuery): JulgadosSentencasResponse {
    // O juiz filtra como o relator na base fictícia.
    const filtros = query?.filters ?? {}
    const q: DashboardQuery | undefined = query && {
        ...query,
        filters: { ...filtros, relator_julgados: filtros.juiz_julgados },
    }
    const ac = julgadosAcordaosFor(unit, q)
    const rota = /^julgados_acordaos_(NG|LA|RJ)$/.exec(ac.dashboard ?? '')
    if (!rota) return { meta: ac.meta, stats: {} }
    const S = rota[1]
    const { meta, dashboard: _dashboard, stats = {}, ...raiz } = ac
    const r = renomearChaves(raiz, S)
    const st = renomearChaves(stats, S)
    const lista = r[`julgados_sentenca_lista_${S}`]
    r[`julgados_sentenca_lista_${S}`] = Array.isArray(lista) ? lista.map(linhaSentenca) : []
    // Estudos de Extinção: o mesmo recorte das improcedências (só no mock).
    for (const sufixo of ['', '_estoque']) {
        r[`julgados_extincao_por_comarca${sufixo}_${S}`] = r[`julgados_improcedencia_por_comarca${sufixo}_${S}`]
        r[`julgados_extincao_por_juiz${sufixo}_${S}`] = r[`julgados_improcedencia_por_juiz${sufixo}_${S}`]
    }
    r[`julgados_extincao_por_motivo_estoque_${S}`] = r[`julgados_por_motivo_extincao_${S}`]
    st[`julgados_extincao_total_estoque_${S}`] = st[`julgados_improcedencia_total_estoque_${S}`]
    st[`julgados_extincao_valor_${S}`] = st[`julgados_improcedencia_valor_${S}`]
    st[`julgados_extincao_valor_estoque_${S}`] = st[`julgados_improcedencia_valor_estoque_${S}`]
    st[`julgados_extincao_revertida_2g_${S}`] = 0
    st[`julgados_extincao_revertida_2g_estoque_${S}`] = 0
    st[`julgados_improcedencia_revertida_2g_${S}`] = 0
    st[`julgados_improcedencia_revertida_2g_estoque_${S}`] = 0
    return { meta, dashboard: `julgados_${S}`, stats: st, ...r }
}
