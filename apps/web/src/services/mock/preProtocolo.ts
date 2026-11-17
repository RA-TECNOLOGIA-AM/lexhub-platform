import type { PreProtocoloResponse } from '../../pages/dashboards/pre-protocolo/setores.ts'
import type { DashboardQuery, Point } from '../../types/index.ts'
import { orgDocumentosFor } from './orgDocumentos.ts'
import { pendenciasFor } from './pendencias.ts'
import { peticionamentoFor } from './peticionamento.ts'
import { protocoloFor } from './protocolo.ts'

// Pré-protocolo fictício: o mesmo que a API faz (app/dashboards/pre_protocolo.py), com os mocks dos 4 setores
// (LexPre). Os mocks dos setores não têm a produção diária por funcionário: aqui a do setor é dividida entre
// as pessoas da média por funcionário (dia a dia, em partes que mudam com o dia).
function porFuncionario(dias: Point[], pessoas: string[]): Record<string, Point[]> {
    if (pessoas.length === 0) return {}
    const out: Record<string, Point[]> = Object.fromEntries(pessoas.map((p) => [p, []]))
    dias.forEach((d, i) => {
        let resto = d.value
        pessoas.forEach((p, k) => {
            const parte =
                k === pessoas.length - 1
                    ? resto
                    : Math.round((d.value * (((i + k) % 3) + 1)) / (pessoas.length * 2 + 1))
            const v = Math.max(0, Math.min(resto, parte))
            resto -= v
            if (v > 0) out[p].push({ name: d.name, value: v })
        })
    })
    return out
}

export function preProtocoloFor(unit: string, query: DashboardQuery): PreProtocoloResponse {
    const pend = pendenciasFor(unit, query)
    const org = orgDocumentosFor(unit, query)
    const pet = peticionamentoFor(unit, query)
    const prot = protocoloFor(unit, query)
    const nomes = (pts: Point[]) => pts.map((p) => p.name)
    return {
        meta: prot.meta,
        pendencias: {
            stats: pend.stats,
            por_dia: pend.pendencias_resolvidas_por_dia,
            por_dia_por_funcionario: porFuncionario(
                pend.pendencias_resolvidas_por_dia,
                nomes(pend.media_pendencias_resolvidas_por_funcionario),
            ),
        },
        org_documentos: {
            stats: org.stats,
            por_dia: org.resolvidos_por_dia_org,
            por_dia_por_funcionario: porFuncionario(
                org.resolvidos_por_dia_org,
                nomes(org.media_resolvidos_por_funcionario),
            ),
        },
        peticionamento: {
            stats: pet.stats,
            por_dia: pet.peticionados_por_dia,
            por_dia_por_funcionario: porFuncionario(
                pet.peticionados_por_dia,
                nomes(pet.media_peticionado_por_funcionario),
            ),
        },
        protocolo: {
            stats: prot.stats,
            por_dia: prot.protocolados_por_dia,
            por_dia_por_funcionario: porFuncionario(
                prot.protocolados_por_dia,
                nomes(prot.media_protocolados_por_funcionario),
            ),
        },
    }
}
