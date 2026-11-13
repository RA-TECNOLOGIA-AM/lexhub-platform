import { useState } from 'react'
import { Icon } from '../ui/Icon.tsx'
import { Modal } from '../ui/Modal.tsx'
import { toDataError } from '../../services/errors.ts'
import {
    allSlugs,
    orderedSelection,
    selectionLabel,
    toggleSlug,
    type ExportFormat,
    type ExportGroup,
} from '../../lib/exportFields.ts'

type ExportDialogProps = {
    title: string // nome do dashboard ('Protocolo')
    groups: ExportGroup[] // os campos que o dashboard declarou
    onClose: () => void
    onExport: (format: ExportFormat, campos: string[]) => Promise<void> // rejeitou = mostra o erro aqui
}

// Módulo: a janela "Exportar relatório" (a mesma da v1, uma só para todos os dashboards).
// Usa o Modal da casa (foco preso, Esc fecha, fundo escurecido).
// Quem usa só a desenha quando está aberta; ao abrir, todos os campos começam marcados (como na v1).
export function ExportDialog({ title, groups, onClose, onExport }: ExportDialogProps) {
    const all = allSlugs(groups)
    const [selected, setSelected] = useState<string[]>(all)
    const [busy, setBusy] = useState<ExportFormat | null>(null)
    const [error, setError] = useState<string | null>(null)

    async function run(format: ExportFormat) {
        setBusy(format)
        setError(null)
        try {
            await onExport(format, orderedSelection(groups, selected))
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
