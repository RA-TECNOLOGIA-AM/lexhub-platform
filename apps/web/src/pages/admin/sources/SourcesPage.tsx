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
import { UnitFormDialog } from './UnitFormDialog.tsx'
import type { DataSource, UnitInput } from '../../../types/index.ts'
import { lastFailureLabel, pickUnit, syncNote } from './sourcesView.ts'
import { timezoneLabel } from './unitForm.ts'

// Conectar fonte ainda não existe (depende do worker de sincronização): o botão aparece e explica isso.
const SOON = 'ainda não está disponível. Fale com a equipe RA.'

// O formulário aberto: criar, ou editar a unidade que está na tela.
type UnitForm = { mode: 'create' } | { mode: 'edit'; unit: UnitInput }

// A página só junta as peças: busca as fontes, lê a unidade da URL (?unidade=NG) e monta menu, indicadores e lista.
export function SourcesPage() {
    const { org = '' } = useParams()
    const [version, setVersion] = useState(0) // muda depois de gravar: busca a lista de novo
    const { data, error } = useAsync(() => dataClient.getSources(org), [org, version])
    const [params, setParams] = useSearchParams()
    const [notice, setNotice] = useState<string | null>(null)
    const [open, setOpen] = useState<DataSource | null>(null) // a fonte do modal de detalhe
    const [form, setForm] = useState<UnitForm | null>(null)

    if (error) return <ErrorState error={error} />
    if (!data) return <LoadingState />

    const current = pickUnit(data.units, params.get('unidade'))
    const pickUnitCode = (code: string) => setParams({ unidade: code }, { replace: true })

    async function saveUnit(unit: UnitInput) {
        const saved =
            form?.mode === 'create' ? await dataClient.createUnit(org, unit) : await dataClient.updateUnit(org, unit)
        setVersion((v) => v + 1)
        pickUnitCode(saved.unit.code)
    }

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
                        onPick={pickUnitCode}
                        onAdd={data.canManageUnits ? () => setForm({ mode: 'create' }) : undefined}
                    />
                    {current && (
                        <div className="sources-main">
                            <div className="grid grid-kpi">
                                <Kpi label="Dashboards alimentados" value={current.dashboards} />
                                <Kpi
                                    label="Fuso da unidade"
                                    value={
                                        <span className="kpi-text">
                                            {timezoneLabel(current.timezone)}
                                            {data.canManageUnits && (
                                                <button
                                                    className="btn kpi-edit"
                                                    type="button"
                                                    aria-label={`Editar ${current.unit.name}`}
                                                    onClick={() =>
                                                        setForm({
                                                            mode: 'edit',
                                                            unit: {
                                                                code: current.unit.code,
                                                                name: current.unit.name,
                                                                timezone: current.timezone,
                                                            },
                                                        })
                                                    }
                                                >
                                                    Editar
                                                </button>
                                            )}
                                        </span>
                                    }
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
            {form && (
                <UnitFormDialog
                    mode={form.mode}
                    initial={form.mode === 'edit' ? form.unit : undefined}
                    existingCodes={data.units.map((u) => u.unit.code)}
                    onSave={saveUnit}
                    onClose={() => setForm(null)}
                />
            )}
        </>
    )
}
