import type { PlanUsage } from '../types/index.ts'

// Módulo: quando um limite do plano está perto de acabar ou já acabou (as regras, sem React).
// Só olha o que o plano limita de verdade: assentos, unidades e fontes. O histórico (24 de 24 meses)
// "cheio" é o normal, não é aviso.

export const NEAR_LIMIT = 0.8 // a partir de 80% do teto o aviso aparece

const WATCHED = ['seats', 'units', 'sources']

export type LimitAlert = {
    key: string
    label: string
    used: number
    total: number
    level: 'near' | 'full' // near = perto do teto; full = chegou (ou passou)
}

// Os avisos de uma resposta de cobrança, o mais cheio primeiro. Sem teto (null) nunca avisa.
export function limitAlerts(usage: PlanUsage[]): LimitAlert[] {
    const alerts: LimitAlert[] = []
    for (const u of usage) {
        if (!WATCHED.includes(u.key) || u.total === null || u.total <= 0) continue
        if (u.used >= u.total) alerts.push({ key: u.key, label: u.label, used: u.used, total: u.total, level: 'full' })
        else if (u.used / u.total >= NEAR_LIMIT)
            alerts.push({ key: u.key, label: u.label, used: u.used, total: u.total, level: 'near' })
    }
    return alerts.sort((a, b) => b.used / b.total - a.used / a.total)
}

// 'Assentos: 56 de 60'
export const alertText = (a: LimitAlert): string => `${a.label}: ${a.used} de ${a.total}`

// O aviso de assentos para quem vai convidar; null = sobra espaço ou o plano não tem teto.
export function seatAlert(usage: PlanUsage[] | null | undefined): LimitAlert | null {
    return limitAlerts(usage ?? []).find((a) => a.key === 'seats') ?? null
}
