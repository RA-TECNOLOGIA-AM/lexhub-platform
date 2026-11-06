import type { DataClient } from './client.ts'
import { DataError } from './errors.ts'
import { catalog, me, pendencias, protocolo } from './mock-data.ts'

// Simula a rede: um pouco de espera faz o "carregando" aparecer de verdade.
const LATENCY_MS = 300
const wait = () => new Promise((resolve) => setTimeout(resolve, LATENCY_MS))

// Devolve uma cópia: assim uma tela que altere o objeto não estraga o mock das outras.
const copy = <T>(value: T): T => structuredClone(value)

// Mesma regra da API: dashboard fora das unidades liberadas = 403.
function checkAccess(dashboardKey: string, unit: string) {
    const dash = catalog.available.find((d) => d.key === dashboardKey)
    if (!dash || !dash.units.includes(unit)) {
        throw new DataError(403, 'Você não tem acesso a este dashboard nesta unidade')
    }
}

export function createMockClient(): DataClient {
    return {
        async getMe() {
            await wait()
            return copy(me)
        },

        async listDashboards() {
            await wait()
            return copy(catalog)
        },

        async getProtocolo(query) {
            await wait()
            checkAccess('protocolo-lexpre', query.unit)
            const meta = { ...protocolo.meta, unit: query.unit, from: query.from ?? protocolo.meta.from, to: query.to ?? protocolo.meta.to }
            return copy({ ...protocolo, meta })
        },

        async getPendencias(query) {
            await wait()
            checkAccess('pendencias', query.unit)
            const meta = { ...pendencias.meta, unit: query.unit, from: query.from ?? pendencias.meta.from, to: query.to ?? pendencias.meta.to }
            return copy({ ...pendencias, meta })
        },
    }
}