import { useEffect, useState } from 'react'

// A seção "atual" é a última cujo topo já passou desta linha (px do topo da janela): logo abaixo da barra do topo.
const LINE = 120

// Módulo: qual seção da página está na tela agora (para marcar o sumário). Recebe os ids, devolve um deles.
// Lê na rolagem (passiva) e ao mudar de tamanho; no fim da página, marca a última (ela pode nem chegar à linha).
export function useActiveSection(ids: string[]): string | null {
    const [active, setActive] = useState<string | null>(ids[0] ?? null)
    const key = ids.join('|')

    useEffect(() => {
        const list = key ? key.split('|') : []
        function update() {
            const atEnd = window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4
            if (atEnd && list.length) return setActive(list[list.length - 1])
            let current = list[0] ?? null
            for (const id of list) {
                const el = document.getElementById(id)
                if (el && el.getBoundingClientRect().top <= LINE) current = id
            }
            setActive(current)
        }
        update()
        window.addEventListener('scroll', update, { passive: true })
        window.addEventListener('resize', update)
        return () => {
            window.removeEventListener('scroll', update)
            window.removeEventListener('resize', update)
        }
    }, [key])

    return active
}
