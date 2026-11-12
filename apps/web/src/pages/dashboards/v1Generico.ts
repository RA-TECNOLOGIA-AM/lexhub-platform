import type { ComponentType } from 'react'
import { dataClient } from '../../services/client.ts'
import type { Meta } from '../../types/index.ts'
import type { DashboardModule } from './types.ts'

// Resposta dos dashboards "genéricos" da v1 lidos do banco NG (Protocolo, Peticionamento, Org. de
// documentos, Pendências, Comercial, Comissão e Marketing): a DashboardResponse da v1 + `meta`.
// Em `stats` os números vêm soltos e os comparativos em campos `comparativo_*`, com os mesmos nomes
// na NG e no RJ. No mock vem `stats: {}`: qualquer valor pode faltar e a tela mostra '—'.
export type V1GenericoResponse = {
    meta: Meta
    dashboard?: string // nome do dashboard na v1 (ex.: 'protocolo', 'protocolo_RJ')
    stats?: Record<string, unknown>
}

// Leitor de `stats`: campo ausente, null ou não numérico vira null ('—' na tela, Delta some).
export function statsReader(data: V1GenericoResponse): (campo: string) => number | null {
    const stats = data.stats ?? {}
    return (campo) => {
        const v = stats[campo]
        return typeof v === 'number' ? v : null
    }
}

// Módulo de um dashboard genérico do NG: a key do catálogo/API e o miolo da página.
export function v1GenericoModule(
    key: string,
    Content: ComponentType<{ data: V1GenericoResponse }>,
): DashboardModule<V1GenericoResponse> {
    return {
        key,
        fetch: (query) => dataClient.getDashboardData<V1GenericoResponse>(key, query),
        Content,
    }
}
