import { useEffect, useRef, useState } from 'react'
import { prefersReducedMotion, tween } from '../../lib/countUp.ts'

type CountUpProps = {
    value: number
    format: (v: number) => string // o mesmo formato da tela (fmt.int, fmt.brl, fmt.duracao...)
    duration?: number // ms
}

// Módulo: número que "vai carregando" até o valor, como na v1. Ao abrir a página conta a partir de 0;
// quando o valor muda (filtro, período, Atualizar) conta do número atual até o novo.
// O leitor de tela recebe só o valor final; quem pediu menos movimento no sistema vê o final direto.
export function CountUp({ value, format, duration = 900 }: CountUpProps) {
    const reduced = prefersReducedMotion()
    const [shown, setShown] = useState(0)
    const current = useRef(0) // de onde a próxima animação sai (pega a anterior no meio, se for o caso)

    useEffect(() => {
        if (reduced) return
        const from = current.current
        if (from === value) return
        const start = performance.now()
        let frame = 0
        const step = (now: number) => {
            const t = (now - start) / duration
            const v = t >= 1 ? value : tween(from, value, t)
            current.current = v
            setShown(v)
            if (t < 1) frame = requestAnimationFrame(step)
        }
        frame = requestAnimationFrame(step)
        return () => cancelAnimationFrame(frame)
    }, [value, duration, reduced])

    return (
        <>
            <span aria-hidden="true">{format(reduced ? value : shown)}</span>
            <span className="sr-only">{format(value)}</span>
        </>
    )
}
