// O número do sino: não lidas + pedidos de acesso pendentes + avisos de limite do plano;
// nada = sem número; acima de 9 vira "9+".
export function bellCount(unread: number, pending: number, planAlerts = 0): string | null {
    const total = unread + pending + planAlerts
    if (total <= 0) return null
    return total > 9 ? '9+' : String(total)
}
