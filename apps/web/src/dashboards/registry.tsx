import type { ComponentType } from 'react'
import type { Meta } from '../data/types.ts'
import { DashboardView } from './DashboardView.tsx'
import { protocolo } from './protocolo/index.ts'
import type { DashboardModule } from './types.ts'
import { pendencias } from './pendencias/index.ts'

// Transforma um módulo de dashboard numa página pronta (que não recebe parâmetros).
function toPage<T extends { meta: Meta }>(module: DashboardModule<T>): ComponentType {
    return function DashboardModulePage() {
        return <DashboardView module={module} />
    }
}

// Todos os dashboards que já têm página na V2, pela key. Dashboard novo = uma linha aqui.
export const DASHBOARD_PAGES: Record<string, ComponentType> = {
    [protocolo.key]: toPage(protocolo),
    [pendencias.key]: toPage(pendencias),
}