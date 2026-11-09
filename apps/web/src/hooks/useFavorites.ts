import { useEffect, useRef, useState } from 'react'
import { dataClient } from '../data/client.ts'
import { withViewTransition } from '../lib/viewTransition.ts'

// Módulo: os favoritos do usuário logado numa organização.
// Parâmetro: a organização. Devolve: ready, isFavorite(key) e toggle(key).
// Esconde: de onde vêm (dataClient) e a troca otimista (a estrela muda na hora; se falhar, volta).
export function useFavorites(org: string) {
    const [keys, setKeys] = useState<string[] | null>(null) // null = ainda carregando
    // A lista mais recente, sem esperar o React desenhar: com a animação, o estado só muda no
    // quadro seguinte, e dois cliques rápidos leriam a lista antiga (o 2º clique não desfaria o 1º).
    const latest = useRef<string[]>([])

    useEffect(() => {
        let ignore = false
        dataClient
            .listFavorites(org)
            .then((list) => {
                if (ignore) return
                latest.current = list
                setKeys(list)
            })
            .catch(() => {
                // Sem favoritos o hub funciona igual; não vale mostrar erro por isso.
                if (!ignore) setKeys([])
            })
        return () => {
            ignore = true
        }
    }, [org])

    function toggle(key: string) {
        const favorite = !latest.current.includes(key)
        const apply = (add: boolean) => {
            const others = latest.current.filter((k) => k !== key)
            const next = add ? [...others, key] : others
            latest.current = next
            // Lê latest na hora de aplicar: se duas animações se atropelarem, o navegador pode rodar as
            // mudanças fora de ordem, e assim a tela fica sempre com a lista mais recente.
            withViewTransition(() => setKeys(latest.current)) // muda na tela já, com animação
        }
        apply(favorite)
        dataClient.setFavorite(org, key, favorite).catch(() => apply(!favorite)) // falhou: desfaz
    }

    const list = keys ?? []
    return { ready: keys !== null, isFavorite: (key: string) => list.includes(key), toggle }
}
