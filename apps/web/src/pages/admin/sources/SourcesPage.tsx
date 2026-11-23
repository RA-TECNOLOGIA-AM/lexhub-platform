import { useState } from 'react'
import { Link, useLocation, useParams, useSearchParams } from 'react-router'
import { PageHeader } from '../../../components/layout/PageHeader.tsx'
import { Kpi } from '../../../components/dashboard/Kpi.tsx'
import { Icon } from '../../../components/ui/Icon.tsx'
import { Notice } from '../../../components/ui/Notice.tsx'
import { ErrorState } from '../../../components/states/ErrorState.tsx'
import { LoadingState } from '../../../components/states/LoadingState.tsx'
import { dataClient } from '../../../services/client.ts'
import { toDataError } from '../../../services/errors.ts'
import { useAsync } from '../../../hooks/useAsync.ts'
import { SourceList } from './SourceList.tsx'
import { UnitNav } from './UnitNav.tsx'
import { SourceDetailDialog } from './SourceDetailDialog.tsx'
import { UnitFormDialog } from './UnitFormDialog.tsx'
import { ConnectSourceDialog } from './ConnectSourceDialog.tsx'
import { DeleteUnitDialog } from './DeleteUnitDialog.tsx'
import type { DataSource, ProductKey, UnitInput } from '../../../types/index.ts'
import { lastFailureLabel, pickUnit, syncNote } from './sourcesView.ts'
import { withFreshness } from './sourceFreshness.ts'
import { timezoneLabel } from './unitForm.ts'

// O formulário aberto: criar, ou editar a unidade que está na tela.
type UnitForm = { mode: 'create' } | { mode: 'edit'; unit: UnitInput }

// A página só junta as peças: busca as fontes, lê a unidade da URL (?unidade=NG) e monta menu, indicadores e lista.
export function SourcesPage() {
    const { org = '' } = useParams()
    // Aberta por Clientes (/plataforma/clientes/:org/unidades): a plataforma entra sem ser membro do cliente.
    const fromPlatform = useLocation().pathname.startsWith('/plataforma/')
    const [version, setVersion] = useState(0) // muda depois de gravar: busca a lista de novo
    const { data, error } = useAsync(() => dataClient.getSources(org), [org, version])
    // A hora de cada fonte vem do cache da API, igual ao card do hub. Falhou = a tela segue com o que o
    // Supabase devolveu (nunca derruba a página).
    const keys = data ? [...new Set(data.units.flatMap((u) => u.sources.map((s) => s.id)))].sort() : []
    const { data: freshness } = useAsync(
        () => (keys.length ? dataClient.getSourcesFreshness(org, keys) : Promise.resolve(null)),
        [org, keys.join(','), version], // version: ligou/desligou ou testou, a API pode ter esquecido a hora
    )
    const [params, setParams] = useSearchParams()
    const [notice, setNotice] = useState<string | null>(null)
    const [open, setOpen] = useState<DataSource | null>(null) // a fonte do modal de detalhe
    const [form, setForm] = useState<UnitForm | null>(null)
    const [connecting, setConnecting] = useState(false) // o modal Conectar fonte
    const [deleting, setDeleting] = useState<{ code: string; name: string } | null>(null) // o modal Excluir unidade

    if (error) return <ErrorState error={error} />
    if (!data) return <LoadingState />

    const picked = pickUnit(data.units, params.get('unidade'))
    const current = picked && withFreshness(picked, freshness)
    const pickUnitCode = (code: string) => setParams({ unidade: code }, { replace: true })

    async function saveUnit(unit: UnitInput) {
        const saved =
            form?.mode === 'create' ? await dataClient.createUnit(org, unit) : await dataClient.updateUnit(org, unit)
        setVersion((v) => v + 1)
        pickUnitCode(saved.unit.code)
    }

    // Volta a unidade sem as fontes próprias (foram apagadas com as senhas na exclusão).
    async function restoreUnit(code: string) {
        try {
            const restored = await dataClient.restoreUnit(org, code)
            setVersion((v) => v + 1)
            pickUnitCode(restored.unit.code)
            setNotice(
                `${restored.unit.name} foi restaurada. As fontes próprias dela não voltam: conecte de novo se precisar.`,
            )
        } catch (err) {
            setNotice(toDataError(err).message)
        }
    }

    async function linkOffice(product: ProductKey, ref: string) {
        if (!current) return
        await dataClient.linkProductOffice(org, current.unit.code, product, ref)
        setVersion((v) => v + 1)
        setNotice(`Escritório ligado a ${current.unit.name}. Os dashboards aparecem quando forem ativados para ela.`)
    }

    // Só a TI da LexGroup conecta fontes (o servidor confere de novo).
    const connect = data.canManageSources && current ? () => setConnecting(true) : undefined

    return (
        <>
            <PageHeader
                title={`${data.orgName} › Unidades e fontes de dados`}
                badge={fromPlatform ? <span className="badge pro">Plataforma</span> : undefined}
                description={syncNote()}
                actions={
                    connect && (
                        <button className="btn btn-primary" type="button" onClick={connect}>
                            <Icon name="plug" size={16} />
                            Conectar fonte
                        </button>
                    )
                }
            />
            <div className="stack">
                {fromPlatform && (
                    <Link className="muted small" to="/plataforma/clientes">
                        ← Voltar para Clientes
                    </Link>
                )}
                {notice && <Notice message={notice} onClose={() => setNotice(null)} />}
                <div className="sources-cols">
                    <UnitNav
                        units={data.units}
                        selected={current?.unit.code}
                        limit={data.unitLimit}
                        onPick={pickUnitCode}
                        onAdd={data.canManageUnits ? () => setForm({ mode: 'create' }) : undefined}
                        deleted={data.deletedUnits}
                        onRestore={data.canManageUnits ? restoreUnit : undefined}
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
                            <SourceList sources={current.sources} onOpen={setOpen} onConnect={connect} />
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
                    freshness={freshness?.[open.id]}
                    onChanged={() => setVersion((v) => v + 1)}
                    onDisconnected={() => {
                        setOpen(null)
                        setVersion((v) => v + 1)
                        setNotice(`${open.name} foi desconectada de ${current.unit.name}.`)
                    }}
                    onClose={() => setOpen(null)}
                />
            )}
            {connecting && current && (
                <ConnectSourceDialog
                    unit={current.unit}
                    sources={current.sources}
                    loadOffices={(product) => dataClient.listProductOffices(product)}
                    onLink={linkOffice}
                    loadConnectInfo={() => dataClient.getConnectInfo()}
                    inspectSheet={(url) => dataClient.inspectSheet(url)}
                    onConnect={(input) => dataClient.connectSource(org, current.unit.code, input)}
                    onSaved={() => {
                        setVersion((v) => v + 1)
                        setNotice(
                            `Fonte conectada a ${current.unit.name}. Ela aparece como "Aguardando dashboards" até o ` +
                                'analista ligar os dashboards a ela.',
                        )
                    }}
                    onClose={() => setConnecting(false)}
                />
            )}
            {deleting && (
                <DeleteUnitDialog
                    org={org}
                    unit={deleting}
                    onDeleted={() => {
                        setParams({}, { replace: true })
                        setVersion((v) => v + 1)
                        setNotice(
                            `${deleting.name} foi excluída. Fica arquivada por 30 dias antes de ser apagada de vez.`,
                        )
                    }}
                    onClose={() => setDeleting(null)}
                />
            )}
            {form && (
                <UnitFormDialog
                    mode={form.mode}
                    initial={form.mode === 'edit' ? form.unit : undefined}
                    existingCodes={data.units.map((u) => u.unit.code)}
                    orgName={data.orgName}
                    onDelete={
                        form.mode === 'edit'
                            ? () => {
                                  setDeleting({ code: form.unit.code, name: form.unit.name })
                                  setForm(null)
                              }
                            : undefined
                    }
                    onSave={saveUnit}
                    onClose={() => setForm(null)}
                />
            )}
        </>
    )
}
