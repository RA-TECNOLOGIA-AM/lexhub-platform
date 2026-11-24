import { useEffect } from 'react'
import { getSupport } from '../lib/supportSession.ts'
import { dataClient } from '../services/client.ts'

// Última abertura registrada por org/unidade/dashboard nesta aba: evita mandar de novo em menos de 5 min
// (o efeito duplo do React em dev, voltar e abrir de novo). O banco também ignora repetição (é ele que garante).
const REPEAT_MS = 5 * 60 * 1000
const lastSent = new Map<string, number>()

// Registra uma abertura (no máximo uma a cada 5 min por org/unidade/dashboard).
// Em modo suporte não chama nada: quem vê como o membro não é o membro (a API audita o suporte à parte).
export function logViewOnce(
    org: string,
    unit: string,
    dashboardKey: string,
    log: (org: string, unit: string, dashboardKey: string) => Promise<void> = (o, u, k) =>
        dataClient.logDashboardView(o, u, k),
): void {
    if (!org || !unit || !dashboardKey || getSupport()) return
    const key = `${org}/${unit}/${dashboardKey}`
    const now = Date.now()
    if (now - (lastSent.get(key) ?? 0) < REPEAT_MS) return
    lastSent.set(key, now)
    log(org, unit, dashboardKey).catch(() => {})
}

// Módulo: registra na Auditoria que a pessoa abriu este dashboard ("Dashboards abertos").
// Uma vez por org/unidade/dashboard: trocar período, filtros ou a atualização automática não registram.
// Falhou (ex.: sem acesso) = segue a vida: nunca impede o dashboard de abrir.
export function useLogDashboardView(org: string, unit: string, dashboardKey: string): void {
    useEffect(() => {
        logViewOnce(org, unit, dashboardKey)
    }, [org, unit, dashboardKey])
}
