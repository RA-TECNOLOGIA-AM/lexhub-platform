import { useEffect } from 'react'
import { dataClient } from '../services/client.ts'

// Última abertura registrada por org/unidade/dashboard nesta aba: evita mandar de novo em menos de 5 min
// (o efeito duplo do React em dev, voltar e abrir de novo). O banco também ignora repetição (é ele que garante).
const REPEAT_MS = 5 * 60 * 1000
const lastSent = new Map<string, number>()

// Módulo: registra na Auditoria que a pessoa abriu este dashboard ("Dashboards abertos").
// Uma vez por org/unidade/dashboard: trocar período, filtros ou a atualização automática não registram.
// Falhou (ex.: sem acesso) = segue a vida: nunca impede o dashboard de abrir.
export function useLogDashboardView(org: string, unit: string, dashboardKey: string): void {
    useEffect(() => {
        if (!org || !unit || !dashboardKey) return
        const key = `${org}/${unit}/${dashboardKey}`
        const now = Date.now()
        if (now - (lastSent.get(key) ?? 0) < REPEAT_MS) return
        lastSent.set(key, now)
        dataClient.logDashboardView(org, unit, dashboardKey).catch(() => {})
    }, [org, unit, dashboardKey])
}
