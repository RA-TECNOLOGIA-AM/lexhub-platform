import type { IconName } from '../../../components/ui/Icon.tsx'
import type { Tone } from '../../../components/dashboard/tone.ts'
import type { Meta, Point } from '../../../types/index.ts'

// Os 4 setores do pré-protocolo e onde cada número está no `stats` do dashboard LexPre do setor
// (os mesmos campos que a página "Dashboard Geral Pré Protocolo (LexPre)" da v1 lê).
export type SetorKey = 'pendencias' | 'org_documentos' | 'peticionamento' | 'protocolo'

export type Setor = {
    key: SetorKey
    label: string
    icon: IconName
    tone: Tone // a faixa e o ícone do card
    cor: string // a linha da produção diária (as cores da v1: amarelo, vermelho, verde e laranja)
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
        icon: 'alert',
        tone: 'warn',
        cor: 'var(--warn-dot)',
        resolvidos: 'pendencias_resolvidas',
        comparativoResolvidos: 'comparativo_pendencias_resolvidas',
        represados: 'pendencias_nao_resolvidas',
        tempoMedio: 'media_tempo_resolvidos_pendencia',
        comparativoTempoMedio: 'comparativo_tempo_medio_resolvidos_pendencia',
    },
    {
        key: 'org_documentos',
        label: 'Org. Documentos',
        icon: 'layers',
        tone: 'danger',
        cor: 'var(--danger)',
        resolvidos: 'resolvidos_total.total',
        comparativoResolvidos: 'resolvidos_total.comparativo',
        represados: 'represados',
        tempoMedio: 'media_tempo_resolvidos',
        comparativoTempoMedio: 'comparativo_tempo_medio_resolvidos',
    },
    {
        key: 'peticionamento',
        label: 'Peticionamento',
        icon: 'sheet',
        tone: 'ok',
        cor: 'var(--ok-dot)',
        resolvidos: 'total_peticionados.total',
        comparativoResolvidos: 'total_peticionados.comparativo',
        represados: 'represados',
        tempoMedio: 'media_tempo_peticionado',
        comparativoTempoMedio: 'comparativo_tempo_medio_peticionado',
    },
    {
        key: 'protocolo',
        label: 'Protocolo',
        icon: 'check-circle',
        tone: 'accent',
        cor: 'var(--chart-1)',
        resolvidos: 'protocolados_total.total',
        comparativoResolvidos: 'protocolados_total.comparativo',
        represados: 'represados',
        tempoMedio: 'media_tempo_protocolado',
        comparativoTempoMedio: 'comparativo_tempo_medio_protocolado',
    },
]

// Resposta de GET .../dashboards/pre-protocolo: de cada setor, o `stats` e a produção diária (a do setor e a
// de cada funcionário, name = 'AAAA-MM-DD') + `meta`. Qualquer setor ou campo pode faltar (a tela mostra '—').
export type DadosSetor = { stats?: unknown; por_dia?: Point[]; por_dia_por_funcionario?: Record<string, Point[]> }
export type PreProtocoloResponse = { meta: Meta } & Partial<Record<SetorKey, DadosSetor>>

// A produção diária de um setor: a do setor ('' = todos) ou a de um funcionário.
export function serieDiaria(data: PreProtocoloResponse, setor: SetorKey, funcionario = ''): Point[] {
    const d = data[setor]
    return (funcionario ? d?.por_dia_por_funcionario?.[funcionario] : d?.por_dia) ?? []
}

// Os funcionários que produziram no setor no período (as opções do filtro do gráfico), em ordem alfabética.
export function funcionariosDoSetor(data: PreProtocoloResponse, setor: SetorKey): string[] {
    return Object.keys(data[setor]?.por_dia_por_funcionario ?? {}).sort((a, b) => a.localeCompare(b, 'pt-BR'))
}

// Número no caminho ('a.b') do `stats` do setor; ausente, null ou não numérico = null.
export function lerSetor(data: PreProtocoloResponse, setor: SetorKey, caminho: string): number | null {
    let v: unknown = data[setor]?.stats
    for (const parte of caminho.split('.')) {
        v = v !== null && typeof v === 'object' ? (v as Record<string, unknown>)[parte] : undefined
    }
    return typeof v === 'number' ? v : null
}
