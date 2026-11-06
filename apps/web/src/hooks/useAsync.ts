import { useEffect, useState, type DependencyList } from 'react'
import { toDataError, type DataError } from '../data/errors.ts'

export type AsyncState<T> = {
    data: T | null // último resultado (fica na tela enquanto a próxima busca não chega)
    error: DataError | null
    loading: boolean
}

// Módulo: o ciclo "buscando -> dados | erro" de qualquer chamada assíncrona.
// Parâmetros: a função que busca (fetcher) e do que ela depende (deps); quando deps muda, busca de novo.
// Esconde: o useEffect, o estado e a proteção contra resposta atrasada (ignore).
export function useAsync<T>(fetcher: () => Promise<T>, deps: DependencyList): AsyncState<T> {
    const [state, setState] = useState<AsyncState<T>>({ data: null, error: null, loading: true })

    // A lista de dependências é um parâmetro (deps): o linter só confere listas escritas aqui,
    // então a regra fica desligada só neste trecho. Quem confere as deps é quem chama o useAsync.
    /* eslint-disable react-hooks/exhaustive-deps */
    useEffect(() => {
        let ignore = false
        setState((prev) => ({ ...prev, loading: true }))
        fetcher()
            .then((data) => {
                if (!ignore) setState({ data, error: null, loading: false })
            })
            .catch((err: unknown) => {
                if (!ignore) setState({ data: null, error: toDataError(err), loading: false })
            })
        return () => {
            ignore = true
        }
    }, deps)
    /* eslint-enable react-hooks/exhaustive-deps */

    return state
}