import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import { Icon } from './Icon.tsx'
import {
    MONTH_NAMES,
    MONTH_SHORT,
    WEEKDAYS,
    addDays,
    addMonths,
    isoOf,
    monthGrid,
    partsOf,
    rangeRole,
} from '../../lib/calendar.ts'

type RangeCalendarProps = {
    from: string // 'AAAA-MM-DD' (pode estar vazio)
    to: string
    start: string // a data que abre o calendário (o mês mostrado e o dia com foco)
    min?: string // dias antes disto ficam desligados
    max?: string // dias depois disto ficam desligados
    today?: string // dia marcado como hoje
    onPick: (iso: string) => void
}

// Módulo: calendário de um mês com a faixa De→Até pintada, nas cores do tema.
// Quem usa decide o que o clique faz (onPick); aqui é só mostrar e navegar.
// Teclado: setas mudam o dia, PageUp/PageDown mudam o mês, Enter escolhe.
// Para abrir em outra data, troque a `key` do componente.
export function RangeCalendar({ from, to, start, min, max, today, onPick }: RangeCalendarProps) {
    const [focus, setFocus] = useState(start) // o dia com foco (tabindex 0)
    const [mode, setMode] = useState<'days' | 'months'>('days')
    const [yearView, setYearView] = useState(partsOf(start).y) // o ano da grade de meses
    const grid = useRef<HTMLDivElement>(null)
    const moved = useRef(false) // o foco mudou pelo teclado: levar o foco do navegador junto

    const { y, m } = partsOf(focus)
    // O mês inteiro fica fora dos limites? (desliga o mês na grade e as setas)
    const monthOut = (yy: number, mm: number) =>
        (!!min && isoOf(yy, mm + 1, 0) < min) || (!!max && isoOf(yy, mm, 1) > max)

    useEffect(() => {
        if (!moved.current) return
        moved.current = false
        grid.current?.querySelector<HTMLButtonElement>('[tabindex="0"]')?.focus()
    }, [focus, mode])

    function goMonth(delta: number) {
        setFocus(clamp(addMonths(focus, delta)))
    }

    // O foco nunca para num dia desligado.
    function clamp(iso: string) {
        if (min && iso < min) return min
        return max && iso > max ? max : iso
    }

    function onGridKey(e: KeyboardEvent) {
        const step: Record<string, () => string> = {
            ArrowLeft: () => addDays(focus, -1),
            ArrowRight: () => addDays(focus, 1),
            ArrowUp: () => addDays(focus, -7),
            ArrowDown: () => addDays(focus, 7),
            PageUp: () => addMonths(focus, -1),
            PageDown: () => addMonths(focus, 1),
        }
        const next = step[e.key]
        if (!next) return
        e.preventDefault()
        moved.current = true
        setFocus(clamp(next()))
    }

    function pickMonth(month: number) {
        const last = new Date(yearView, month + 1, 0).getDate()
        setFocus(clamp(isoOf(yearView, month, Math.min(partsOf(focus).d, last))))
        setMode('days')
        moved.current = true
    }

    if (mode === 'months') {
        const canPrevYear = !monthOut(yearView - 1, 11)
        const canNextYear = !monthOut(yearView + 1, 0)
        return (
            <div className="cal">
                <div className="cal-head">
                    <button
                        type="button"
                        className="cal-nav"
                        aria-label="Ano anterior"
                        disabled={!canPrevYear}
                        onClick={() => setYearView(yearView - 1)}
                    >
                        <Icon name="chevron-left" size={16} />
                    </button>
                    <button
                        type="button"
                        className="cal-title"
                        onClick={() => setMode('days')}
                        aria-label="Voltar para os dias"
                    >
                        {yearView}
                    </button>
                    <button
                        type="button"
                        className="cal-nav"
                        aria-label="Próximo ano"
                        disabled={!canNextYear}
                        onClick={() => setYearView(yearView + 1)}
                    >
                        <Icon name="chevron-right" size={16} />
                    </button>
                </div>
                <div className="cal-months" ref={grid}>
                    {MONTH_SHORT.map((label, i) => {
                        const disabled = monthOut(yearView, i)
                        const current = yearView === y && i === m
                        return (
                            <button
                                key={label}
                                type="button"
                                className="cal-month"
                                aria-current={current ? 'date' : undefined}
                                tabIndex={current ? 0 : -1}
                                disabled={disabled}
                                onClick={() => pickMonth(i)}
                            >
                                {label}
                            </button>
                        )
                    })}
                </div>
            </div>
        )
    }

    const canPrev = !monthOut(y, m - 1)
    const canNext = !monthOut(y, m + 1)
    return (
        <div className="cal">
            <div className="cal-head">
                <button
                    type="button"
                    className="cal-nav"
                    aria-label="Mês anterior"
                    disabled={!canPrev}
                    onClick={() => goMonth(-1)}
                >
                    <Icon name="chevron-left" size={16} />
                </button>
                <button
                    type="button"
                    className="cal-title"
                    aria-label={`${MONTH_NAMES[m]} de ${y}: escolher mês e ano`}
                    onClick={() => {
                        setYearView(y)
                        setMode('months')
                    }}
                >
                    {MONTH_NAMES[m]} de {y}
                    <Icon name="chevron-down" size={14} />
                </button>
                <button
                    type="button"
                    className="cal-nav"
                    aria-label="Próximo mês"
                    disabled={!canNext}
                    onClick={() => goMonth(1)}
                >
                    <Icon name="chevron-right" size={16} />
                </button>
            </div>
            <div className="cal-week" aria-hidden="true">
                {WEEKDAYS.map((w, i) => (
                    <span key={i}>{w}</span>
                ))}
            </div>
            <div className="cal-days" role="grid" ref={grid} onKeyDown={onGridKey}>
                {monthGrid(y, m).map((cell) => {
                    const role = rangeRole(cell.iso, from, to)
                    const disabled = (!!min && cell.iso < min) || (!!max && cell.iso > max)
                    return (
                        <button
                            key={cell.iso}
                            type="button"
                            className="cal-day"
                            data-range={role ?? undefined}
                            data-out={cell.inMonth ? undefined : ''}
                            data-today={cell.iso === today ? '' : undefined}
                            aria-pressed={role === 'start' || role === 'end' || role === 'single'}
                            aria-label={`${cell.day} de ${MONTH_NAMES[partsOf(cell.iso).m]} de ${partsOf(cell.iso).y}`}
                            tabIndex={cell.iso === focus ? 0 : -1}
                            disabled={disabled}
                            onClick={() => {
                                setFocus(cell.iso)
                                onPick(cell.iso)
                            }}
                        >
                            {cell.day}
                        </button>
                    )
                })}
            </div>
        </div>
    )
}
