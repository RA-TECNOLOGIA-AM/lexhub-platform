import type { Point } from '../../../types/index.ts'
import type { RubricaValor } from '../comercial-lexpre/types.ts'

// Contas da tela da Comissão Comercial (LexPre), sem React (testadas em comissao.test.ts).

export type LinhaRubrica = { rubrica: string; acoes: number; valorAm: number | null; total: number | null }
export type OrdemRubricas = { key: 'rubrica' | 'acoes'; dir: 'asc' | 'desc' }

// Tabela "Valor das Rubricas" da v1: as ações por rubrica do gráfico (mesmo canal) com o VALOR_AM e o total da
// API, casados pelo nome sem caixa. Rubrica sem valor cadastrado fica com "—" (null). Total = soma dos totais.
export function linhasValorRubricas(
    pontos: Point[],
    tabela: RubricaValor[],
    ordem: OrdemRubricas,
): { linhas: LinhaRubrica[]; totalAcoes: number; totalValor: number } {
    const valores = new Map(tabela.map((t) => [t.rubrica.trim().toUpperCase(), t]))
    const linhas = pontos.map((p) => {
        const rubrica = String(p.name ?? '').trim() || '—'
        const v = valores.get(rubrica.toUpperCase())
        return { rubrica, acoes: Number(p.value) || 0, valorAm: v ? v.valor_am : null, total: v ? v.total : null }
    })
    const dir = ordem.dir === 'asc' ? 1 : -1
    linhas.sort((a, b) =>
        ordem.key === 'rubrica'
            ? a.rubrica.localeCompare(b.rubrica, 'pt-BR') * dir
            : (a.acoes - b.acoes) * dir || a.rubrica.localeCompare(b.rubrica, 'pt-BR'),
    )
    return {
        linhas,
        totalAcoes: linhas.reduce((s, l) => s + l.acoes, 0),
        totalValor: linhas.reduce((s, l) => s + (l.total ?? 0), 0),
    }
}

// Clicar no cabeçalho: a mesma coluna inverte; outra começa em A→Z (rubrica) ou maior→menor (ações).
export const proximaOrdem = (atual: OrdemRubricas, key: OrdemRubricas['key']): OrdemRubricas =>
    atual.key === key
        ? { key, dir: atual.dir === 'asc' ? 'desc' : 'asc' }
        : { key, dir: key === 'rubrica' ? 'asc' : 'desc' }
