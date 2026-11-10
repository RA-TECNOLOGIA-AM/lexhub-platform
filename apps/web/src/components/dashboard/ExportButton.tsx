import { useRef, useState } from 'react'
import { Icon } from '../ui/Icon.tsx'
import type { ExportFormat, ExportGroup } from '../../lib/exportFields.ts'
import { ExportDialog } from './ExportDialog.tsx'

type ExportButtonProps = {
    canExport: boolean // decidido pelo servidor (regra do setor)
    title: string
    groups: ExportGroup[] // [] = dashboard ainda sem relatório
    onExport: (format: ExportFormat, campos: string[]) => Promise<void>
}

// Módulo: o botão "Exportar" e a janela que ele abre.
// Sem permissão: não aparece. Sem campos (páginas-base): aparece desativado, explicando o porquê.
export function ExportButton({ canExport, title, groups, onExport }: ExportButtonProps) {
    const [open, setOpen] = useState(false)
    const button = useRef<HTMLButtonElement>(null)

    if (!canExport) return null

    const empty = groups.length === 0
    function close() {
        setOpen(false)
        button.current?.focus() // a janela some; o foco volta para quem a abriu
    }

    return (
        <>
            <button
                ref={button}
                className="btn btn-primary"
                type="button"
                disabled={empty}
                title={empty ? 'Sem dados para exportar ainda' : undefined}
                onClick={() => setOpen(true)}
            >
                <Icon name="download" size={16} />
                Exportar
            </button>
            {open && <ExportDialog title={title} groups={groups} onClose={close} onExport={onExport} />}
        </>
    )
}
