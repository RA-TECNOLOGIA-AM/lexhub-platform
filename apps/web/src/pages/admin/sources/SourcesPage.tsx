import { useState } from 'react'
import { useParams, useSearchParams } from 'react-router'
import { PageHeader } from '../../../components/layout/PageHeader.tsx'
import { Kpi } from '../../../components/dashboard/Kpi.tsx'
import { Icon } from '../../../components/ui/Icon.tsx'
import { Notice } from '../../../components/ui/Notice.tsx'
import { ErrorState } from '../../../components/states/ErrorState.tsx'
import { LoadingState } from '../../../components/states/LoadingState.tsx'
import { dataClient } from '../../../services/client.ts'
import { useAsync } from '../../../hooks/useAsync.ts'
import { SourceList } from './SourceList.tsx'
import { UnitNav } from './UnitNav.tsx'
import { SourceDetailDialog } from './SourceDetailDialog.tsx'
import type { DataSource } from '../../../types/index.ts'
import { lastFailureLabel, pickUnit, syncNote } from './sourcesView.ts'

// Conectar fonte e criar unidade ainda não existem: os botões aparecem e explicam isso.
const SOON = 'ainda não está disponível. Fale com a equipe RA.'

// A página só junta as peças: busca as fontes, lê a unidade da URL (?unidade=NG) e monta menu, indicadores e lista.
export function SourcesPage() {
    const { org = '' } = useParams()
    const { data, error } = useAsync(() => dataClient.getSources(org), [org])
    const [params, setParams] = useSearchParams()
    const [notice, setNotice] = useState<string | null>(null)
    const [open, setOpen] = useState<DataSource | null>(null) // a fonte do modal de detalhe

    if (error) return <ErrorState error={error} />
    if (!data) return <LoadingState />

    const current = pickUnit(data.units, params.get('unidade'))
    return (
        <>
            <PageHeader
                title="Unidades e fontes de dados"
                description={syncNote(data.syncEveryMin)}
                actions={
                    <button
                        className="btn btn-primary"
                        type="button"
                        onClick={() => setNotice(`Conectar fonte ${SOON}`)}
                    >
                        <Icon name="plug" size={16} />
                        Conectar fonte
                    </button>
                }
            />
            <div className="stack">
                {notice && <Notice message={notice} onClose={() => setNotice(null)} />}
                <div className="sources-cols">
                    <UnitNav
                        units={data.units}
                        selected={current?.unit.code}
                        limit={data.unitLimit}
                        onPick={(code) => setParams({ unidade: code }, { replace: true })}
                        onAdd={() => setNotice(`Criar unidade ${SOON}`)}
                    />
                    {current && (
                        <div className="sources-main">
                            <div className="grid grid-kpi">
                                <Kpi label="Dashboards alimentados" value={current.dashboards} />
                                <Kpi
                                    label="Fuso da unidade"
                                    value={<span className="kpi-text">{current.timezone}</span>}
                                />
                                <Kpi
                                    label="Última falha"
                                    value={<span className="kpi-text">{lastFailureLabel(current)}</span>}
                                    tone={current.lastFailure ? 'warn' : undefined}
                                />
                            </div>
                            <SourceList sources={current.sources} onOpen={setOpen} />
                        </div>
                    )}
                </div>
            </div>
            {open && current && (
                <SourceDetailDialog
                    org={org}
                    unit={current.unit.code}
                    source={open.id}
                    name={open.name}
                    onClose={() => setOpen(null)}
                />
            )}
        </>
    )
}
