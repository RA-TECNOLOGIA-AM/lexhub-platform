import { useLayoutEffect, useRef, useState } from 'react'

// Largura de um elemento, acompanhando a tela: o SVG dos gráficos é desenhado em pixels reais
// (texto sem distorcer). Sem ResizeObserver (testes), fica na largura inicial.
export function useWidth<T extends HTMLElement>(initial = 600) {
    const ref = useRef<T>(null)
    const [width, setWidth] = useState(initial)
    useLayoutEffect(() => {
        const el = ref.current
        if (!el) return
        const measure = () => {
            const w = Math.floor(el.getBoundingClientRect().width)
            if (w > 0) setWidth(w)
        }
        measure()
        if (typeof ResizeObserver === 'undefined') return
        const observer = new ResizeObserver(measure)
        observer.observe(el)
        return () => observer.disconnect()
    }, [])
    return [ref, width] as const
}
