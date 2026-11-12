import type { Meta } from '../../../types/index.ts'

// Os 4 setores do pré-protocolo e onde cada número está no `stats` do dashboard LexPre do setor
// (os mesmos campos que a página "Dashboard Geral Pré Protocolo (LexPre)" da v1 lê).
export type SetorKey = 'pendencias' | 'org_documentos' | 'peticionamento' | 'protocolo'

export type Setor = {
    key: SetorKey
    label: string
    resolvidos: string
    comparativoResolvidos: string
    represados: string // acumulado, não depende do período
    tempoMedio: string // dias
    comparativoTempoMedio: string
}

export const SETORES: readonly Setor[] = [
    {
        key: 'pendencias',
        label: 'Pendência',
        resolvidos: 'pendencias_resolvidas',
        comparativoResolvidos: 'comparativo_pendencias_resolvidas',
        represados: 'pendencias_nao_resolvidas',
        tempoMedio: 'media_tempo_resolvidos_pendencia',
        comparativoTempoMedio: 'comparativo_tempo_medio_resolvidos_pendencia',
    },
    {
        key: 'org_documentos',
        label: 'Org. Documentos',
        resolvidos: 'resolvidos_total.total',
        comparativoResolvidos: 'resolvidos_total.comparativo',
        represados: 'represados',
        tempoMedio: 'media_tempo_resolvidos',
        comparativoTempoMedio: 'comparativo_tempo_medio_resolvidos',
    },
    {
        key: 'peticionamento',
        label: 'Peticionamento',
        resolvidos: 'total_peticionados.total',
        comparativoResolvidos: 'total_peticionados.comparativo',
        represados: 'represados',
        tempoMedio: 'media_tempo_peticionado',
        comparativoTempoMedio: 'comparativo_tempo_medio_peticionado',
    },
    {
        key: 'protocolo',
        label: 'Protocolo',
        resolvidos: 'protocolados_total.total',
        comparativoResolvidos: 'protocolados_total.comparativo',
        represados: 'represados',
        tempoMedio: 'media_tempo_protocolado',
        comparativoTempoMedio: 'comparativo_tempo_medio_protocolado',
    },
]

// Resposta de GET .../dashboards/pre-protocolo: o `stats` de cada setor + `meta`.
// No mock vem só `meta`: qualquer setor ou campo pode faltar e a tela mostra '—'.
export type PreProtocoloResponse = { meta: Meta } & Partial<Record<SetorKey, { stats?: unknown }>>

// Número no caminho ('a.b') do `stats` do setor; ausente, null ou não numérico = null.
export function lerSetor(data: PreProtocoloResponse, setor: SetorKey, caminho: string): number | null {
    let v: unknown = data[setor]?.stats
    for (const parte of caminho.split('.')) {
        v = v !== null && typeof v === 'object' ? (v as Record<string, unknown>)[parte] : undefined
    }
    return typeof v === 'number' ? v : null
}
