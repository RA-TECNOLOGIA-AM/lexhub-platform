import type { ReplicasResponse } from '../../pages/dashboards/replicas/replicas.ts'
import { intermediariasFor } from './intermediarias.ts'

// Réplicas fictícias (NG e LA), no formato da resposta da V2 (app/dashboards/replicas.py): a mesma estrutura das
// Pendências Intermediárias fictícias, com os nomes deste dashboard, as atividades do setor e a taxa de procedência.

const ATIVIDADES = {
    NG: ['ELABORAR RÉPLICA SIMPLES', 'ANÁLISE DE VIABILIDADE - RÉPLICA', 'ELABORAR RÉPLICA ESPECÍFICA'],
    LA: ['ELABORAR RÉPLICA'],
}

export function replicasFor(unit: string): ReplicasResponse {
    const base = intermediariasFor(unit)
    if (!('stats' in base)) return { meta: base.meta }
    const u = base.unidade === 'LA' ? 'LA' : 'NG' // o RJ segue o NG
    const renomeia = (k: string) => k.replace('intermediarias', 'replicas')
    const out: Record<string, unknown> = {}
    for (const [k, v] of Object.entries(base)) {
        if (k === 'stats' || k.startsWith('dilacoes_')) continue
        out[renomeia(k)] = v
    }
    const atividades = ATIVIDADES[u]
    const porAtividade = atividades.map((name, i) => ({ name, value: [52, 14, 6][i] }))
    out.replicas_processos_por_atividade_NG = porAtividade
    out.replicas_processos_por_atividade_por_prazo_NG = porAtividade
    for (const lista of ['replicas_atividades_lista_NG', 'replicas_por_prazo_lista_NG']) {
        out[lista] = (out[lista] as Record<string, unknown>[]).map((t, i) => ({
            ...t,
            descricao: 'RÉPLICA',
            atividade: atividades[i % atividades.length],
            pessoa_setor: `${u === 'NG' ? 'RÉPLICA' : 'RÉPLICAS'} - ${atividades[i % atividades.length]}`,
        }))
    }
    const stats = Object.fromEntries(
        Object.entries(base.stats ?? {})
            .filter(([k]) => !k.startsWith('dilacoes_'))
            .map(([k, v]) => [renomeia(k), v]),
    )
    return {
        ...out,
        meta: base.meta,
        unidade: base.unidade,
        stats: {
            ...stats,
            replicas_procedencia_total_processos_NG: 105,
            replicas_procedencia_total_decididos_NG: 24,
            replicas_procedencia_procedentes_NG: 7,
            replicas_procedencia_pendentes_NG: 81,
            replicas_taxa_procedencia_NG: 29.2,
        },
    }
}
