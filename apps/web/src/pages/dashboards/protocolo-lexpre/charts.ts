import type { Point } from '../../../types/index.ts'

// Contas da tela do Protocolo (LexPre), sem React (testadas em charts.test.ts).
// Tudo sai do que a API já manda: nada aqui inventa número.

// Os nomes que a v1 usa quando falta o dado ("Sem matéria", "Sem funcionário"): aparecem no gráfico,
// mas não viram filtro.
export const isPlaceholder = (name: string) => /^sem (matéria|materia|funcionário|funcionario)$/i.test(name.trim())

// Parte de um todo em % (0 quando o todo é 0).
export const share = (part: number, whole: number) => (whole > 0 ? (part / whole) * 100 : 0)

export type Funcionario = {
    name: string
    protocolados: number // no período
    represados: number // agora (não depende do período)
    mediaDiaria: number | null // protocolados por dia trabalhado no período
    valorCausa: number
}

// Uma linha por pessoa juntando as listas por funcionário, do maior total (protocolados + represados) ao menor.
// Quem só tem represado também aparece.
export function funcionarios(data: {
    protocolados_por_funcionario: Point[]
    represados_por_funcionario: Point[]
    media_protocolados_por_funcionario: Point[]
    valor_causa_por_funcionario: Point[]
}): Funcionario[] {
    const byName = new Map<string, Funcionario>()
    const get = (name: string) => {
        const row = byName.get(name) ?? { name, protocolados: 0, represados: 0, mediaDiaria: null, valorCausa: 0 }
        byName.set(name, row)
        return row
    }
    for (const p of data.protocolados_por_funcionario) get(p.name).protocolados += p.value
    for (const p of data.represados_por_funcionario) get(p.name).represados += p.value
    for (const p of data.media_protocolados_por_funcionario) get(p.name).mediaDiaria = p.value
    for (const p of data.valor_causa_por_funcionario) get(p.name).valorCausa += p.value
    return [...byName.values()].sort(
        (a, b) => b.protocolados + b.represados - (a.protocolados + a.represados) || a.name.localeCompare(b.name),
    )
}

// "Raimunda Moura" -> "RM"; "Sem funcionário" -> "SF".
export function initials(name: string): string {
    const parts = name.trim().split(/\s+/).filter(Boolean)
    const first = parts[0]?.[0] ?? '?'
    const last = parts.length > 1 ? parts[parts.length - 1][0] : ''
    return (first + last).toUpperCase()
}

export type Devolucoes = {
    total: number
    partes: { key: 'peticionamento' | 'org_doc' | 'pendencia'; label: string; value: number; pct: number }[]
}

// O resumo da seção Devolução: total e a parte de cada setor (os % somam 100 quando há devolução).
export function devolucoes(s: {
    devolvido_peticionamento: number
    devolvido_org_doc: number
    devolvido_pendencia: number
}): Devolucoes {
    const total = s.devolvido_peticionamento + s.devolvido_org_doc + s.devolvido_pendencia
    const parte = (key: Devolucoes['partes'][number]['key'], label: string, value: number) => ({
        key,
        label,
        value,
        pct: share(value, total),
    })
    return {
        total,
        partes: [
            parte('peticionamento', 'Peticionamento', s.devolvido_peticionamento),
            parte('org_doc', 'Org Doc', s.devolvido_org_doc),
            parte('pendencia', 'Pendência', s.devolvido_pendencia),
        ],
    }
}

// A frase do rodapé de um card de devolução, pela variação vs mês anterior.
export function leituraDevolucao(
    value: number,
    comparativo: number | null,
): { text: string; tone: 'ok' | 'danger' | 'neutral' } {
    if (value === 0) return { text: 'Nenhuma devolução pendente', tone: 'neutral' }
    if (comparativo === null || comparativo === 0) return { text: 'Estável vs mês anterior', tone: 'neutral' }
    if (comparativo >= 50) return { text: 'Aumento crítico de devolução', tone: 'danger' }
    if (comparativo > 0) return { text: 'Aumento nas devoluções', tone: 'danger' }
    if (comparativo <= -50) return { text: 'Forte queda nas devoluções', tone: 'ok' }
    return { text: 'Queda nas devoluções', tone: 'ok' }
}

// Índice do mês em andamento numa série jan–dez de um ano (null = o ano não é o atual).
export function mesParcial(year: number, today: Date = new Date()): number | null {
    return year === today.getFullYear() ? today.getMonth() : null
}
