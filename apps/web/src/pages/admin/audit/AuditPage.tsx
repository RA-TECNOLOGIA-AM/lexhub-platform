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
import { AUDIT_COLUMNS } from './auditColumns.tsx'
import { AuditFilters } from './AuditFilters.tsx'
import { actorsOf, filterEvents, filterFromParams, paramsFromFilter, type AuditFilter } from './auditView.ts'

// A página só junta as peças: busca os eventos, aplica o filtro da URL e mostra a tabela.
export function AuditPage() {
    const { org = '' } = useParams()
    const { data, error } = useAsync(() => dataClient.getAudit(org), [org])
    const [notice, setNotice] = useState<string | null>(null)

    const [params, setParams] = useSearchParams()
    const filter = filterFromParams(params)
    const setFilter = (next: AuditFilter) => setParams(paramsFromFilter(next), { replace: true })

    if (error) return <ErrorState error={error} />
    if (!data) return <LoadingState />

    return (
        <>
            <PageHeader
                title="Auditoria"
                description="Entradas, exportações, mudanças de acesso e sessões de suporte. Guardado por pelo menos 6 meses."
                actions={
                    <button
                        className="btn"
                        type="button"
                        onClick={() =>
                            setNotice(
                                'Exportar a auditoria ainda não está disponível: precisa ficar registrado no servidor.',
                            )
                        }
                    >
                        <Icon name="download" size={16} />
                        Exportar CSV
                    </button>
                }
            />
            <div className="stack">
                {notice && <Notice message={notice} onClose={() => setNotice(null)} />}
                <AuditFilters value={filter} actors={actorsOf(data.events)} onChange={setFilter} />
                <DataTable
                    columns={AUDIT_COLUMNS}
                    rows={filterEvents(data.events, filter)}
                    rowKey={(e) => e.id}
                    rowClassName={(e) => (e.kind === 'support' ? 'row-support' : undefined)}
                    empty="Nenhum evento com esses filtros."
                />
            </div>
        </>
    )
}
