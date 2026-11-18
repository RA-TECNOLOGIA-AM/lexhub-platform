import { useEffect, useState } from 'react'

// Módulo: um valor que só acompanha o original depois de ele ficar `ms` sem mudar.
// Na montagem já vem igual ao original (a primeira busca não espera).
// Uso: cliques seguidos nos filtros viram uma busca só, com o último estado.
export function useDebouncedValue<T>(value: T, ms: number): T {
    const [settled, setSettled] = useState(value)
    useEffect(() => {
        const timer = setTimeout(() => setSettled(value), ms)
        return () => clearTimeout(timer)
    }, [value, ms])
    return settled
}
