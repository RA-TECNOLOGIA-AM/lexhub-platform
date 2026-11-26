import { useRef, useState } from 'react'
import { Icon } from './Icon.tsx'
import { RangeCalendar } from './RangeCalendar.tsx'
import { useDismiss } from '../../hooks/useDismiss.ts'
import { formatBr } from '../../lib/calendar.ts'

type DateFieldProps = {
    label: string // texto acima do campo (e nome do painel para leitor de tela)
    value: string // 'AAAA-MM-DD'
    onChange: (iso: string) => void // chamado ao clicar num dia
    min?: string
    max?: string
    today?: string
    range?: { from: string; to: string } // faixa a pintar (ex.: De→Até do filtro); sem ela, só o dia escolhido
    className?: string // classe do contêiner (ex.: 'filter' na barra de filtros)
}

// Módulo: um campo de data que abre o calendário do tema num painel (no lugar do date nativo).
// Escolher um dia fecha o painel; Esc e clique fora também.
export function DateField({ label, value, onChange, min, max, today, range, className }: DateFieldProps) {
    const [open, setOpen] = useState(false)
    const root = useRef<HTMLDivElement>(null)
    const button = useRef<HTMLButtonElement>(null)

    useDismiss({
        open,
        onClose: () => setOpen(false),
        isInside: (target) => !!root.current?.contains(target),
        returnFocus: button,
    })

    return (
        <div className={`popover-wrap date-field ${className ?? ''}`} ref={root}>
            <span className="lbl">{label}</span>
            <button
                ref={button}
                type="button"
                className="field date-trigger"
                aria-expanded={open}
                aria-haspopup="dialog"
                aria-label={`${label}: ${formatBr(value) || 'sem data'}`}
                onClick={() => setOpen((o) => !o)}
            >
                {formatBr(value) || 'dd/mm/aaaa'}
                <Icon name="calendar" size={15} />
            </button>
            {open && (
                <div className="card popover date-popover" role="dialog" aria-label={`Escolher data: ${label}`}>
                    <RangeCalendar
                        from={range?.from ?? value}
                        to={range?.to ?? value}
                        start={value || today || max || ''}
                        min={min}
                        max={max}
                        today={today}
                        onPick={(iso) => {
                            onChange(iso)
                            setOpen(false)
                            button.current?.focus()
                        }}
                    />
                </div>
            )}
        </div>
    )
}
