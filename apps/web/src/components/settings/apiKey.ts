import type { ApiKeyExtraRequest } from '../../types/index.ts'

// Regras do pedido de chave de API, iguais às de api.request_api_key (o banco confere de novo).
export const MAX_DAYS = 365
export const DEFAULT_DAYS = 90
export const MIN_JUSTIFICATION = 10

// Datas como texto AAAA-MM-DD (o <input type="date"> usa esse formato).
export function addDays(day: string, days: number): string {
    const d = new Date(`${day}T12:00:00Z`)
    d.setUTCDate(d.getUTCDate() + days)
    return d.toISOString().slice(0, 10)
}

export function todayInBrazil(now: number = Date.now()): string {
    return new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Sao_Paulo' }).format(now)
}

// "Vale até" de um setor extra: o banco guarda o instante logo depois do último dia; mostra o último dia.
export function validUntil(expiresAt: string): string {
    return new Date(Date.parse(expiresAt) - 1000).toLocaleDateString('pt-BR', { timeZone: 'America/Sao_Paulo' })
}

// null = pode enviar; texto = o que falta.
export function validateRequest(base: string[], extras: ApiKeyExtraRequest[], today: string): string | null {
    if (base.length === 0 && extras.length === 0) {
        return 'Você não tem setor cadastrado: peça ao menos um setor extra.'
    }
    const max = addDays(today, MAX_DAYS)
    const seen = new Set<string>()
    for (const e of extras) {
        if (!e.setor) return 'Escolha o setor de cada setor extra.'
        if (seen.has(e.setor)) return `O setor ${e.setor} está pedido mais de uma vez.`
        seen.add(e.setor)
        if (e.justificativa.trim().length < MIN_JUSTIFICATION) {
            return `A justificativa do setor extra precisa de pelo menos ${MIN_JUSTIFICATION} caracteres.`
        }
        if (!(e.validade > today && e.validade <= max)) {
            return `A validade do setor extra deve ser entre amanhã e ${MAX_DAYS} dias.`
        }
    }
    return null
}
