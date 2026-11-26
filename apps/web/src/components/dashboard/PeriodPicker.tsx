import { useRef, useState } from 'react'
import { Icon } from '../ui/Icon.tsx'
import { RangeCalendar } from '../ui/RangeCalendar.tsx'
import { useDismiss } from '../../hooks/useDismiss.ts'
import { formatBr } from '../../lib/calendar.ts'
import { PRESETS, periodError, periodLabel, presetPeriod, todayIso, type Period } from '../../lib/period.ts'

type PeriodPickerProps = {
    value: Period | null // período em uso (null = o padrão do servidor)
    onChange: (period: Period) => void // só é chamado com um período válido
}

// Módulo: o botão "1 a 30 de out. de 2026" e o painel para escolher qualquer período (atalhos + De/Até).
// As regras (validar, texto, atalhos) ficam em lib/period.ts; aqui é só a tela.
export function PeriodPicker({ value, onChange }: PeriodPickerProps) {
    const [open, setOpen] = useState(false)
    const [draft, setDraft] = useState<Period>(value ?? presetPeriod('este-mes')) // o que está sendo escolhido
    const root = useRef<HTMLDivElement>(null)
    const button = useRef<HTMLButtonElement>(null)

    useDismiss({
        open,
        onClose: () => setOpen(false),
        isInside: (target) => !!root.current?.contains(target),
        returnFocus: button,
    })

    const [active, setActive] = useState<'from' | 'to'>('from') // a ponta que o calendário preenche
    const [calKey, setCalKey] = useState(0) // trocar = o calendário reabre na data da ponta ativa

    const error = periodError(draft)

    // Abrir sempre começa do período em uso (cancelar descarta o rascunho).
    function toggle() {
        if (!open) {
            setDraft(value ?? presetPeriod('este-mes'))
            setActive('from')
            setCalKey((k) => k + 1)
        }
        setOpen((o) => !o)
    }

    function focusEnd(end: 'from' | 'to') {
        setActive(end)
        setCalKey((k) => k + 1)
    }

    // Clique no calendário: preenche a ponta ativa. Escolher De passa para Até (sem pular o mês mostrado).
    // Se a ordem inverter, as pontas se ajustam em vez de deixar um período impossível.
    function pick(iso: string) {
        if (active === 'from') {
            setDraft({ from: iso, to: draft.to && draft.to < iso ? iso : draft.to })
            setActive('to')
        } else {
            setDraft(iso < draft.from ? { from: iso, to: draft.from } : { ...draft, to: iso })
        }
    }

    function choosePreset(range: Period) {
        setDraft(range)
        setActive('from')
        setCalKey((k) => k + 1)
    }

    function apply() {
        if (error) return
        onChange(draft)
        setOpen(false)
        button.current?.focus()
    }

    return (
        <div className="popover-wrap" ref={root}>
            <button
                ref={button}
                className="btn"
                type="button"
                aria-expanded={open}
                aria-haspopup="dialog"
                onClick={toggle}
            >
                <Icon name="calendar" size={16} />
                {value ? periodLabel(value) : 'Período padrão'}
            </button>
            {open && (
                <div className="card popover period-popover" role="dialog" aria-label="Escolher período">
                    <div className="period-presets">
                        {PRESETS.map((p) => {
                            const range = presetPeriod(p.key)
                            const pressed = range.from === draft.from && range.to === draft.to
                            return (
                                <button
                                    key={p.key}
                                    type="button"
                                    className="pill"
                                    aria-pressed={pressed}
                                    onClick={() => choosePreset(range)}
                                >
                                    {p.label}
                                </button>
                            )
                        })}
                    </div>
                    <div className="period-fields">
                        {(['from', 'to'] as const).map((end) => (
                            <div key={end} className="period-field">
                                <span className="lbl">{end === 'from' ? 'De' : 'Até'}</span>
                                <button
                                    type="button"
                                    className="field date-trigger"
                                    aria-pressed={active === end}
                                    onClick={() => focusEnd(end)}
                                >
                                    {formatBr(draft[end]) || 'dd/mm/aaaa'}
                                    <Icon name="calendar" size={15} />
                                </button>
                            </div>
                        ))}
                    </div>
                    <RangeCalendar
                        key={calKey}
                        from={draft.from}
                        to={draft.to}
                        start={draft[active] || todayIso()}
                        max={todayIso()}
                        today={todayIso()}
                        onPick={pick}
                    />
                    {error && <p className="small period-error">{error}</p>}
                    <div className="popover-actions">
                        <button className="btn" type="button" onClick={() => setOpen(false)}>
                            Cancelar
                        </button>
                        <button className="btn btn-primary" type="button" disabled={!!error} onClick={apply}>
                            Aplicar
                        </button>
                    </div>
                </div>
            )}
        </div>
    )
}
