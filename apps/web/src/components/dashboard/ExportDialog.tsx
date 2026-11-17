import { useState } from 'react'
import { Icon } from '../ui/Icon.tsx'
import { Modal } from '../ui/Modal.tsx'
import { Segmented } from '../ui/Segmented.tsx'
import { toDataError } from '../../services/errors.ts'
import {
    allSlugs,
    defaultOptions,
    orderedSelection,
    selectionLabel,
    toggleSlug,
    type ExportFormat,
    type ExportReport,
} from '../../lib/exportFields.ts'

type ExportDialogProps = {
    title: string // nome do dashboard ('Protocolo')
    reports: ExportReport[] // os relatórios do dashboard (o LexPre tem um só, sem opções)
    onClose: () => void
    // rejeitou = mostra o erro aqui. relatorio/opcoes: o relatório escolhido e as escolhas dele (ex.: o recorte).
    onExport: (
        format: ExportFormat,
        campos: string[],
        relatorio?: string,
        opcoes?: Record<string, string>,
    ) => Promise<void>
}

// Módulo: a janela "Exportar relatório" (a mesma da v1, uma só para todos os dashboards).
// Usa o Modal da casa (foco preso, Esc fecha, fundo escurecido).
// Quem usa só a desenha quando está aberta; ao abrir, todos os campos começam marcados (como na v1).
// Com mais de um relatório (ex.: Processos e Atividades nos Acordos), escolher outro volta a marcar todos os campos
// dele; as opções (ex.: o recorte Entradas/Saídas/Total) aparecem acima dos campos, como na v1.
export function ExportDialog({ title, reports, onClose, onExport }: ExportDialogProps) {
    const [indice, setIndice] = useState(0)
    const report = reports[indice] ?? reports[0]
    const groups = report.groups
    const all = allSlugs(groups)
    const [selected, setSelected] = useState<string[]>(all)
    const [opcoes, setOpcoes] = useState<Record<string, string>>(defaultOptions(report))
    const trocarRelatorio = (i: number) => {
        setIndice(i)
        setSelected(allSlugs(reports[i].groups))
        setOpcoes(defaultOptions(reports[i]))
    }
    const [busy, setBusy] = useState<ExportFormat | null>(null)
    const [error, setError] = useState<string | null>(null)

    async function run(format: ExportFormat) {
        setBusy(format)
        setError(null)
        try {
            const temOpcoes = (report.options ?? []).length > 0
            await onExport(
                format,
                orderedSelection(groups, selected),
                report.key ?? undefined,
                temOpcoes ? opcoes : undefined,
            )
            onClose()
        } catch (err) {
            setError(toDataError(err).message)
            setBusy(null)
        }
    }

    const none = selected.length === 0
    return (
        <Modal
            title={`Exportar relatório de ${title}`}
            description="Quais campos você quer no relatório? O período e os filtros aplicados no dashboard serão usados na exportação."
            onClose={onClose}
            footer={
                <>
                    {error && (
                        <p className="small period-error" style={{ flex: '1 1 100%' }}>
                            {error}
                        </p>
                    )}
                    <button className="btn" type="button" onClick={onClose}>
                        Cancelar
                    </button>
                    <button className="btn" type="button" disabled={none || !!busy} onClick={() => run('csv')}>
                        <Icon name="download" size={16} />
                        {busy === 'csv' ? 'Exportando…' : 'Exportar CSV'}
                    </button>
                    <button
                        className="btn btn-primary"
                        type="button"
                        disabled={none || !!busy}
                        onClick={() => run('xlsx')}
                    >
                        <Icon name="sheet" size={16} />
                        {busy === 'xlsx' ? 'Exportando…' : 'Exportar XLSX'}
                    </button>
                </>
            }
        >
            {(reports.length > 1 || (report.options ?? []).length > 0) && (
                <div className="export-opcoes">
                    {reports.length > 1 && (
                        <div className="export-opcao">
                            <span className="export-group-title">Relatório</span>
                            <Segmented
                                label="Relatório"
                                options={reports.map((r, i) => ({ value: String(i), label: r.title }))}
                                value={String(indice)}
                                onChange={(v) => trocarRelatorio(Number(v))}
                            />
                        </div>
                    )}
                    {(report.options ?? []).map((o) => (
                        <div key={o.key} className="export-opcao">
                            <span className="export-group-title">{o.label}</span>
                            <Segmented
                                label={o.label}
                                options={o.choices}
                                value={opcoes[o.key] ?? o.choices[0]?.value}
                                onChange={(v) => setOpcoes({ ...opcoes, [o.key]: v })}
                            />
                        </div>
                    ))}
                </div>
            )}
            <div className="export-toolbar">
                <span className="muted small">{selectionLabel(selected.length, all.length)}</span>
                <span className="small">
                    <button className="link-btn" type="button" onClick={() => setSelected(all)}>
                        Selecionar todos
                    </button>
                    {' · '}
                    <button className="link-btn" type="button" onClick={() => setSelected([])}>
                        Desmarcar todos
                    </button>
                </span>
            </div>
            {groups.map((g) => (
                <fieldset key={g.group} className="filter-group">
                    <legend className="export-group-title">{g.group}</legend>
                    <div className="export-fields">
                        {g.fields.map((f) => (
                            <label key={f.slug} className="check">
                                <input
                                    type="checkbox"
                                    checked={selected.includes(f.slug)}
                                    onChange={() => setSelected(toggleSlug(selected, f.slug))}
                                />
                                {f.label}
                            </label>
                        ))}
                    </div>
                </fieldset>
            ))}
        </Modal>
    )
}
