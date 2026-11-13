// O número do sino: não lidas + pedidos de acesso pendentes; nada = sem número; acima de 9 vira "9+".
export function bellCount(unread: number, pending: number): string | null {
    const total = unread + pending
    if (total <= 0) return null
    return total > 9 ? '9+' : String(total)
}
