import type { V1GenericoResponse } from '../v1Stats.ts'

// As rotas da v1 da Execução Condenação e da Execução Acordos são uma por escritório (NG, LA, RJ), com os mesmos
// campos e o sufixo da unidade no nome. As telas leem os nomes da NG; esta regra (a mesma de
// generico_v1.nome_na_unidade na API) dá o nome na unidade da resposta. Só lógica pura (testada em unidade.test.ts).

export type Unidade = 'NG' | 'LA' | 'RJ'

// 'x_NG' -> 'x_LA'; 'x_NG_detalhe' / 'x_detalhe' -> 'x_LA_detalhe'; sem sufixo ('tre') -> 'tre_LA'. Os campos
// novos da V2 ('..._historico') têm o mesmo nome em todas.
export function nomeNaUnidade(nome: string, u: Unidade): string {
    if (u === 'NG' || nome.endsWith('_historico')) return nome
    if (nome.endsWith('_NG')) return `${nome.slice(0, -3)}_${u}`
    if (nome.endsWith('_NG_detalhe')) return `${nome.slice(0, -'_NG_detalhe'.length)}_${u}_detalhe`
    if (nome.endsWith('_detalhe')) return `${nome.slice(0, -'_detalhe'.length)}_${u}_detalhe`
    return `${nome}_${u}`
}

// A unidade pela rota da v1 que respondeu (o campo `dashboard`); null = outra rota (ex.: mock sem dados).
const ROTAS_EXECUCAO: Record<string, Unidade> = { execucao: 'NG', execucao_LA: 'LA', execucao_RJ: 'RJ' }
const ROTAS_ACORDOS: Record<string, Unidade> = {
    execucao_acordos_NG: 'NG',
    execucao_acordos_LA: 'LA',
    execucao_acordos_RJ: 'RJ',
}

export const unidadeExecucao = (data: V1GenericoResponse): Unidade | null =>
    ROTAS_EXECUCAO[data.dashboard ?? ''] ?? null

export const unidadeAcordos = (data: V1GenericoResponse): Unidade | null => ROTAS_ACORDOS[data.dashboard ?? ''] ?? null
