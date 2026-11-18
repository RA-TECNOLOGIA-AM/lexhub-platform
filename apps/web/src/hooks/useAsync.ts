import { useEffect, useState, type DependencyList } from 'react'
import { toDataError, type DataError } from '../services/errors.ts'

export type AsyncState<T> = {
    data: T | null // último resultado (fica na tela enquanto a próxima busca não chega)
    error: DataError | null
    loading: boolean
}

// Módulo: o ciclo "buscando -> dados | erro" de qualquer chamada assíncrona.
// Parâmetros: a função que busca (fetcher) e do que ela depende (deps); quando deps muda, busca de novo.
// Esconde: o useEffect, o estado e a proteção contra resposta atrasada. A busca anterior é cancelada
// (o fetcher recebe o signal; quem o repassa ao fetch libera a conexão e a API pula o cálculo).
export function useAsync<T>(fetcher: (signal: AbortSignal) => Promise<T>, deps: DependencyList): AsyncState<T> {
    const [state, setState] = useState<AsyncState<T>>({ data: null, error: null, loading: true })

    // A lista de dependências é um parâmetro (deps): o linter só confere listas escritas aqui,
    // então a regra fica desligada só neste trecho. Quem confere as deps é quem chama o useAsync.
    /* eslint-disable react-hooks/exhaustive-deps */
    useEffect(() => {
        const controller = new AbortController()
        const { signal } = controller
        setState((prev) => ({ ...prev, loading: true }))
        fetcher(signal)
            .then((data) => {
                if (!signal.aborted) setState({ data, error: null, loading: false })
            })
            .catch((err: unknown) => {
                if (!signal.aborted) setState({ data: null, error: toDataError(err), loading: false })
            })
        return () => controller.abort()
    }, deps)
    /* eslint-enable react-hooks/exhaustive-deps */

    return state
}
