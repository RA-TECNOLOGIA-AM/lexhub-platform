import { useEffect, useRef, useState } from 'react'
import { Icon } from '../ui/Icon.tsx'
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
// Usa o <dialog> do navegador: ele prende o foco dentro da janela, fecha com Esc e escurece o fundo.
// Quem usa só a desenha quando está aberta; ao abrir, todos os campos começam marcados (como na v1).
export function ExportDialog({ title, groups, onClose, onExport }: ExportDialogProps) {
    const dialog = useRef<HTMLDialogElement>(null)
    const all = allSlugs(groups)
    const [selected, setSelected] = useState<string[]>(all)
    const [busy, setBusy] = useState<ExportFormat | null>(null)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        dialog.current?.showModal()
    }, [])

    // Fecha o <dialog> antes de sumir com ele: assim o navegador libera a página e devolve o foco ao botão "Exportar".
    function close() {
        dialog.current?.close()
        onClose()
    }

    async function run(format: ExportFormat) {
        setBusy(format)
        setError(null)
        try {
            await onExport(format, orderedSelection(groups, selected))
            close()
        } catch (err) {
            setError(toDataError(err).message)
            setBusy(null)
        }
    }

    const none = selected.length === 0
    return (
        <dialog
            ref={dialog}
            className="export-dialog"
            aria-labelledby="export-title"
            onCancel={(event) => {
                event.preventDefault() // o Esc fecha pelo nosso close(), não direto pelo navegador
                close()
            }}
        >
            <div className="export-head">
                <div className="row" style={{ justifyContent: 'space-between', flexWrap: 'nowrap' }}>
                    <h2 className="h2" id="export-title" style={{ margin: 0 }}>
                        Exportar relatório de {title}
                    </h2>
                    <button className="iconbtn" type="button" aria-label="Fechar" onClick={close}>
                        <Icon name="close" size={16} />
                    </button>
                </div>
                <p className="muted small" style={{ margin: '6px 0 0' }}>
                    Quais campos você quer no relatório? O período e os filtros aplicados no dashboard serão usados na
                    exportação.
                </p>
            </div>

            <div className="export-body">
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
            </div>

            <div className="export-foot">
                {error && (
                    <p className="small period-error" style={{ flex: '1 1 100%' }}>
                        {error}
                    </p>
                )}
                <button className="btn" type="button" onClick={close}>
                    Cancelar
                </button>
                <button className="btn" type="button" disabled={none || !!busy} onClick={() => run('csv')}>
                    <Icon name="download" size={16} />
                    {busy === 'csv' ? 'Exportando…' : 'Exportar CSV'}
                </button>
                <button className="btn btn-primary" type="button" disabled={none || !!busy} onClick={() => run('xlsx')}>
                    <Icon name="sheet" size={16} />
                    {busy === 'xlsx' ? 'Exportando…' : 'Exportar XLSX'}
                </button>
            </div>
        </dialog>
    )
}
