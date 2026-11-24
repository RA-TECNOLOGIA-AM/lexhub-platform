import { useRef, useState } from 'react'
import { Icon } from '../ui/Icon.tsx'
import type { ExportFormat, ExportReport } from '../../lib/exportFields.ts'
import { ExportDialog } from './ExportDialog.tsx'
import { useSupportSession } from '../../contexts/support-context.ts'
import { SUPPORT_READ_ONLY } from '../../lib/supportSession.ts'

type ExportButtonProps = {
    canExport: boolean // decidido pelo servidor (regra do setor)
    title: string
    reports: ExportReport[] // [] = dashboard ainda sem relatório; o LexPre tem um só, sem opções
    initialReport?: string | null // o relatório que a janela abre escolhido (key; null = o principal)
    onExport: (
        format: ExportFormat,
        campos: string[],
        relatorio?: string,
        opcoes?: Record<string, string>,
    ) => Promise<void>
}

// Módulo: o botão "Exportar" e a janela que ele abre.
// Sem permissão: não aparece. Sem campos (páginas-base): aparece desativado, explicando o porquê.
// Modo suporte: no lugar do botão, o texto "Somente leitura no modo suporte" (exportar é escrita na auditoria).
export function ExportButton({ canExport, title, reports, initialReport, onExport }: ExportButtonProps) {
    const [open, setOpen] = useState(false)
    const button = useRef<HTMLButtonElement>(null)
    const support = useSupportSession()

    if (support) return <span className="muted small support-ro">{SUPPORT_READ_ONLY}</span>
    if (!canExport) return null

    const empty = reports.every((r) => r.groups.length === 0)
    function close() {
        setOpen(false)
        button.current?.focus() // a janela some; o foco volta para quem a abriu
    }

    return (
        <>
            <button
                ref={button}
                className="btn"
                type="button"
                disabled={empty}
                title={empty ? 'Sem dados para exportar ainda' : undefined}
                onClick={() => setOpen(true)}
            >
                <Icon name="download" size={16} />
                Exportar
            </button>
            {open && (
                <ExportDialog
                    title={title}
                    reports={reports}
                    initialReport={initialReport}
                    onClose={close}
                    onExport={onExport}
                />
            )}
        </>
    )
}
