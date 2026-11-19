import { useState } from 'react'
import { useParams, useSearchParams } from 'react-router'
import { PageHeader } from '../../../components/layout/PageHeader.tsx'
import { ErrorState } from '../../../components/states/ErrorState.tsx'
import { LoadingState } from '../../../components/states/LoadingState.tsx'
import { DataTable } from '../../../components/ui/DataTable.tsx'
import { Icon } from '../../../components/ui/Icon.tsx'
import { Notice } from '../../../components/ui/Notice.tsx'
import { useAsync } from '../../../hooks/useAsync.ts'
import { dataClient } from '../../../services/client.ts'
import { AUDIT_COLUMNS, NEVER_COLUMNS } from './auditColumns.tsx'
import { AuditFilters } from './AuditFilters.tsx'
import { saveFile } from '../../../lib/download.ts'
import {
    actorsOf,
    auditCsv,
    auditFilename,
    filterEvents,
    filterFromParams,
    filterNever,
    NEVER,
    neverAccessed,
    neverCsv,
    paramsFromFilter,
    type AuditFilter,
} from './auditView.ts'

// A página só junta as peças: busca os eventos, aplica o filtro da URL e mostra a tabela.
export function AuditPage() {
    const { org = '' } = useParams()
    const { data, error } = useAsync(() => dataClient.getAudit(org), [org])
    const [notice, setNotice] = useState<string | null>(null)

    const [params, setParams] = useSearchParams()
    const filter = filterFromParams(params)
    const setFilter = (next: AuditFilter) => setParams(paramsFromFilter(next), { replace: true })

    const [exporting, setExporting] = useState(false)

    // "Nunca acessou" vem dos membros (last_seen_at), não dos eventos: só busca quando escolhido.
    const never = filter.kind === NEVER
    const members = useAsync(() => (never ? dataClient.listMembers(org) : Promise.resolve(null)), [org, never])

    if (error) return <ErrorState error={error} />
    if (never && members.error) return <ErrorState error={members.error} />
    if (!data || (never && !members.data)) return <LoadingState />

    const neverAll = never && members.data ? neverAccessed(members.data) : []
    const neverRows = filterNever(neverAll, filter.actor)
    const rows = never ? [] : filterEvents(data.events, filter)
    const count = never ? neverRows.length : rows.length

    // Exporta o que está na tela (mesmos filtros). Primeiro registra no servidor; se falhar, não baixa.
    async function exportCsv() {
        setExporting(true)
        setNotice(null)
        try {
            await dataClient.logAuditExport(org, filter, count)
            const csv = never ? neverCsv(neverRows) : auditCsv(rows)
            saveFile(new Blob([csv], { type: 'text/csv;charset=utf-8' }), auditFilename(org))
        } catch (e) {
            setNotice(e instanceof Error ? e.message : 'Não foi possível exportar a auditoria.')
        } finally {
            setExporting(false)
        }
    }

    return (
        <>
            <PageHeader
                title="Auditoria"
                description="Entradas, exportações, mudanças de acesso e sessões de suporte. Guardado por pelo menos 6 meses."
                actions={
                    <button className="btn" type="button" disabled={exporting || count === 0} onClick={exportCsv}>
                        <Icon name="download" size={16} />
                        {exporting ? 'Exportando…' : 'Exportar CSV'}
                    </button>
                }
            />
            <div className="stack">
                {notice && <Notice message={notice} onClose={() => setNotice(null)} />}
                <AuditFilters
                    value={filter}
                    actors={never ? neverAll.map((r) => r.name) : actorsOf(data.events)}
                    onChange={setFilter}
                />
                {never ? (
                    <DataTable
                        columns={NEVER_COLUMNS}
                        rows={neverRows}
                        rowKey={(r) => r.id}
                        empty="Todo mundo já acessou."
                    />
                ) : (
                    <DataTable
                        columns={AUDIT_COLUMNS}
                        rows={rows}
                        rowKey={(e) => e.id}
                        rowClassName={(e) => (e.kind === 'support' ? 'row-support' : undefined)}
                        empty="Nenhum evento com esses filtros."
                    />
                )}
            </div>
        </>
    )
}
