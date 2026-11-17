import type { MesHistorico, Previsao, ReflexoMes } from './types.ts'

// A lógica da página Financeiro Estratégico (sem React; testada em financeiroEstrategico.test.ts), a mesma da
// página da v1 (FinanceiroEstrategicoNG.tsx).

export const MESES_CURTOS = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

// "Ticket Médio / Receita / Entradas por Mês": uma linha por ano, jan–dez; mês sem TED fica vazio (null).
export function seriesPorAno(
    historico: MesHistorico[],
    campo: 'receita' | 'entradas' | 'ticket_medio',
): { ano: number; valores: (number | null)[] }[] {
    const anos = [...new Set(historico.map((m) => m.ano))].sort((a, b) => a - b)
    return anos.map((ano) => ({
        ano,
        valores: Array.from({ length: 12 }, (_, i) => {
            const p = historico.find((m) => m.ano === ano && m.mes === i + 1)
            return p && p.entradas > 0 ? p[campo] : null
        }),
    }))
}

// "Reflexo do Mês": uma barra por mês (de ajuizamento ou do TED), com o ano no rótulo; sem data primeiro.
// O valor do filtro "Ano de ajuizamento" de cada barra é o ano dela ("Sem data" sem data), como na v1.
export function barrasReflexo(pontos: ReflexoMes[]) {
    return pontos.map((p) => ({
        rotulo: p.ano === null || p.mes === null ? 'Sem data' : `${MESES_CURTOS[p.mes - 1]} / ${p.ano}`,
        ano: p.ano === null ? 'Sem data' : String(p.ano),
        receita: p.receita,
        entradas: p.entradas,
    }))
}

// O gráfico "Receita anual — real e previsão": anos fechados (real), o ano atual (até hoje + o que ainda deve
// entrar) e o ano previsto (cenário base + a faixa até o maior cenário). Uma coluna por ano, em 4 partes.
export function colunasPrevisao(p: Previsao) {
    const base = p.cenarios.find((c) => c.id === p.cenario_base)?.valor ?? 0
    const fechados = p.receita_anual_real.filter((r) => r.ano < p.ano_atual)
    const restante = Math.max(0, p.ano_atual_estimado - p.ano_atual_ate_hoje)
    const acima = p.faixa ? Math.max(0, p.faixa.maximo - base) : 0
    return {
        anos: [...fechados.map((r) => String(r.ano)), String(p.ano_atual), String(p.ano_previsto)],
        real: [...fechados.map((r) => r.receita), p.ano_atual_ate_hoje, 0],
        restante: [...fechados.map(() => 0), restante, 0],
        previsto: [...fechados.map(() => 0), 0, base],
        faixa: [...fechados.map(() => 0), 0, acima],
        base,
    }
}

// Os 12 meses como opções do seletor de mês do modal (valor = número do mês, como a API pede).
export const OPCOES_MES = MESES_CURTOS.map((rotulo, i) => ({ value: String(i + 1), label: rotulo }))
