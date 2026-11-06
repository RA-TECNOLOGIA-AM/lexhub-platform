import { createMockClient } from './mockClient.ts'
import type { DashboardCatalog, DashboardQuery, Me, PendenciasResponse, ProtocoloResponse } from './types.ts'

// A única porta de entrada para dados. As telas só conhecem esta interface;
// trocar o mock pela API real = escrever outra implementação e mudar createDataClient.
export interface DataClient {
    getMe(): Promise<Me>
    listDashboards(org: string): Promise<DashboardCatalog>
    getProtocolo(query: DashboardQuery): Promise<ProtocoloResponse>
    getPendencias(query: DashboardQuery): Promise<PendenciasResponse>
}

function createDataClient(): DataClient {
    const source = import.meta.env.VITE_DATA_SOURCE ?? 'mock'
    if (source === 'mock') return createMockClient()
    throw new Error(`VITE_DATA_SOURCE="${source}" ainda não implementado`)
}

export const dataClient = createDataClient()