import type { Point } from '../../../types/index.ts'

// Contas comuns dos dashboards de setor (Protocolo, Peticionamento...) no layout novo, sem React
// (testadas em setor.test.ts). Tudo sai do que a API já manda: nada aqui inventa número.

// Meta diária de demandas por funcionário da v1 (a linha "Meta: 20"). A V2 manda `metas` quando a regra
// for definida; até lá, vale a da v1.
export const META_POR_FUNCIONARIO_V1 = 20

// Os nomes que a v1 usa quando falta o dado ("Sem matéria", "Sem funcionário"): aparecem no gráfico,
// mas não viram filtro.
export const isPlaceholder = (name: string) => /^sem (matéria|materia|funcionário|funcionario)$/i.test(name.trim())

// Parte de um todo em % (0 quando o todo é 0).
export const share = (part: number, whole: number) => (whole > 0 ? (part / whole) * 100 : 0)

export type Funcionario = {
    name: string
    feitos: number // o que o setor entregou no período (protocolados, peticionados...)
    pendentes: number // na fila agora (não depende do período)
    mediaDiaria: number | null // entregas por dia trabalhado no período
    valorCausa: number
    valorSecundario: number | null // ex.: valor já protocolado (Peticionamento); null = o setor não tem
}

// As listas por funcionário que a API manda (nomes de cada dashboard -> estes).
export type ListasPorFuncionario = {
    feitos: Point[]
    pendentes: Point[]
    media: Point[]
    valor: Point[]
    valorSecundario?: Point[]
}

// Uma linha por pessoa juntando as listas, do maior total (feitos + pendentes) ao menor.
// Quem só tem pendente também aparece.
export function funcionarios(l: ListasPorFuncionario): Funcionario[] {
    const byName = new Map<string, Funcionario>()
    const get = (name: string) => {
        const row = byName.get(name) ?? {
            name,
            feitos: 0,
            pendentes: 0,
            mediaDiaria: null,
            valorCausa: 0,
            valorSecundario: l.valorSecundario ? 0 : null,
        }
        byName.set(name, row)
        return row
    }
    for (const p of l.feitos) get(p.name).feitos += p.value
    for (const p of l.pendentes) get(p.name).pendentes += p.value
    for (const p of l.media) get(p.name).mediaDiaria = p.value
    for (const p of l.valor) get(p.name).valorCausa += p.value
    for (const p of l.valorSecundario ?? []) {
        const row = get(p.name)
        row.valorSecundario = (row.valorSecundario ?? 0) + p.value
    }
    return [...byName.values()].sort(
        (a, b) => b.feitos + b.pendentes - (a.feitos + a.pendentes) || a.name.localeCompare(b.name),
    )
}

// "Raimunda Moura" -> "RM"; "Ana" -> "A".
export function initials(name: string): string {
    const parts = name.trim().split(/\s+/).filter(Boolean)
    const first = parts[0]?.[0] ?? '?'
    const last = parts.length > 1 ? parts[parts.length - 1][0] : ''
    return (first + last).toUpperCase()
}

// Setores para onde uma demanda pode ser devolvida (a chave dá a cor: .dev-<chave>).
export type DestinoDevolucao = 'peticionamento' | 'org_doc' | 'pendencia'

export type Devolucoes = {
    total: number
    partes: { key: DestinoDevolucao; label: string; value: number; pct: number }[]
}

// O resumo da seção Devolução: total e a parte de cada setor (os % somam 100 quando há devolução).
export function devolucoes(partes: { key: DestinoDevolucao; label: string; value: number }[]): Devolucoes {
    const total = partes.reduce((sum, p) => sum + p.value, 0)
    return { total, partes: partes.map((p) => ({ ...p, pct: share(p.value, total) })) }
}

// A frase do rodapé de um card de devolução, pela variação vs mês anterior.
export function leituraDevolucao(
    value: number,
    comparativo: number | null,
): { text: string; tone: 'ok' | 'danger' | 'neutral' } {
    if (value === 0) return { text: 'Nenhuma devolução pendente', tone: 'neutral' }
    if (comparativo === null || comparativo === 0) return { text: 'Sem variação', tone: 'neutral' }
    if (comparativo >= 50) return { text: 'Aumento crítico de devolução', tone: 'danger' }
    if (comparativo > 0) return { text: 'Aumento nas devoluções', tone: 'danger' }
    if (comparativo <= -50) return { text: 'Forte queda nas devoluções', tone: 'ok' }
    return { text: 'Queda nas devoluções', tone: 'ok' }
}

// Fila pequena é saudável; acima de 5% pede atenção e acima de 15%, ação.
export const filaTone = (pct: number) => (pct < 5 ? 'ok' : pct < 15 ? 'warn' : 'danger')

// Índice do mês em andamento numa série jan–dez de um ano (null = o ano não é o atual).
export function mesParcial(year: number, today: Date = new Date()): number | null {
    return year === today.getFullYear() ? today.getMonth() : null
}
