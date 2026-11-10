import { useRef, useState } from 'react'
import { Icon } from '../ui/Icon.tsx'
import { useDismiss } from '../../hooks/useDismiss.ts'
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

    const error = periodError(draft)

    // Abrir sempre começa do período em uso (cancelar descarta o rascunho).
    function toggle() {
        if (!open) setDraft(value ?? presetPeriod('este-mes'))
        setOpen((o) => !o)
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
                <div className="card popover" role="dialog" aria-label="Escolher período">
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
                                    onClick={() => setDraft(range)}
                                >
                                    {p.label}
                                </button>
                            )
                        })}
                    </div>
                    <div className="period-fields">
                        <label>
                            <span className="lbl">De</span>
                            <input
                                className="field"
                                type="date"
                                value={draft.from}
                                max={todayIso()}
                                onChange={(e) => setDraft({ ...draft, from: e.target.value })}
                            />
                        </label>
                        <label>
                            <span className="lbl">Até</span>
                            <input
                                className="field"
                                type="date"
                                value={draft.to}
                                max={todayIso()}
                                onChange={(e) => setDraft({ ...draft, to: e.target.value })}
                            />
                        </label>
                    </div>
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
