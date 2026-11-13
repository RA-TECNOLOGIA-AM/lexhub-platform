import type { DataSource, SourcesResponse, Unit } from '../../types/index.ts'
import { minAgo } from './helpers.ts'
import { me } from './users.ts'

// As fontes da LexGroup no mock, no mesmo formato de api.list_sources (migration 20261113180000_unidades_fontes.sql).
// Mapa combinado em 13/11: NG = LexPre, LexFlow, banco NG, 2 planilhas; LAAM = LexPre, LexFlow, banco LA,
// planilha do financeiro; LARJ = LexPre, LexFlow e o banco NG (gerenciado pela unidade Nicolas Gomes).
// Datas relativas a agora (minAgo), para "há 4 min" continuar verdade no F5.

// Unidade pelo código, reaproveitando os nomes do users.ts (sem repetir 'Nicolas Gomes' aqui).
const unit = (code: string): Unit => me.units.find((u) => u.code === code)!

// Uma fonte saudável que sincronizou há `min` minutos; o resto vem por `over`.
const healthy = (
    min: number,
    over: Omit<DataSource, 'syncedAt' | 'failures' | 'status' | 'rows' | 'managedBy'> & Partial<DataSource>,
): DataSource => ({
    syncedAt: minAgo(min),
    rows: null,
    failures: 0,
    status: 'healthy',
    managedBy: null,
    ...over,
})

const lexpre = (escritorio: number) =>
    healthy(7, {
        id: 'lexpre',
        kind: 'database',
        group: 'product',
        name: 'LexPre',
        detail: `Comercial e pré-protocolo · escritório ${escritorio}`,
    })

const lexflow = (rows: number) =>
    healthy(6, {
        id: 'lexflow',
        kind: 'flow',
        group: 'product',
        name: 'LexFlow',
        detail: 'Execução, acordos, recursal e publicações',
        rows,
    })

const ngDatabase = (managedBy: string | null) =>
    healthy(4, {
        id: 'ng',
        kind: 'database',
        group: 'connection',
        name: 'Sistema jurídico NG',
        detail: 'Postgres · somente leitura',
        rows: 18_000,
        managedBy,
    })

export const sources: SourcesResponse = {
    syncEveryMin: 10,
    unitLimit: { used: 3, total: 5 },
    canManageUnits: true,
    units: [
        {
            unit: unit('NG'),
            timezone: 'America/Manaus',
            dashboards: 14,
            lastFailure: {
                at: minAgo(180),
                source: 'Planilha do protocolo passado',
                message: 'planilha não encontrada',
            },
            sources: [
                lexflow(9_000),
                lexpre(1),
                ngDatabase(null),
                healthy(9, {
                    id: 'sheets_financeiro_ng',
                    kind: 'sheet',
                    group: 'connection',
                    name: 'Planilha do financeiro',
                    detail: 'Google Sheets · conta de serviço',
                }),
                {
                    id: 'sheets_protocolo_passado_ng',
                    kind: 'sheet',
                    group: 'connection',
                    name: 'Planilha do protocolo passado',
                    detail: 'Google Sheets · conta de serviço',
                    managedBy: null,
                    syncedAt: minAgo(180),
                    rows: null,
                    failures: 2,
                    status: 'late',
                },
            ],
        },
        {
            unit: unit('LA_AM'),
            timezone: 'America/Manaus',
            dashboards: 12,
            lastFailure: null,
            sources: [
                lexflow(7_000),
                lexpre(2),
                healthy(5, {
                    id: 'laadv',
                    kind: 'database',
                    group: 'connection',
                    name: 'Sistema jurídico LA',
                    detail: 'Postgres · somente leitura',
                    rows: 15_000,
                }),
                {
                    id: 'sheets_financeiro_la',
                    kind: 'sheet',
                    group: 'connection',
                    name: 'Planilha do financeiro',
                    detail: 'Google Sheets · conta de serviço',
                    managedBy: null,
                    syncedAt: null,
                    rows: null,
                    failures: 0,
                    status: 'waiting',
                },
            ],
        },
        {
            unit: unit('LA_RJ'),
            timezone: 'America/Sao_Paulo',
            dashboards: 9,
            lastFailure: null,
            sources: [lexflow(3_000), lexpre(3), ngDatabase(unit('NG').name)],
        },
    ],
}
