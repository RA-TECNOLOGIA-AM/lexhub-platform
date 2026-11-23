const DAY_MS = 24 * 60 * 60 * 1000

// Módulo: quando a limpeza apaga de vez o que foi excluído/encerrado ('em 12 dias', 'amanhã', 'hoje').
// Conta dias inteiros para cima: faltando 2 h ainda é "hoje"; faltando 25 h, "amanhã".
export function purgeWhen(purgeAt: string, now: number = Date.now()): string {
    const days = Math.ceil((new Date(purgeAt).getTime() - now) / DAY_MS)
    if (days <= 0) return 'hoje'
    if (days === 1) return 'amanhã'
    return `em ${days} dias`
}
