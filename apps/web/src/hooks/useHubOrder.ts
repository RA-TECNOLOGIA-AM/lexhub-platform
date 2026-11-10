import { useState } from 'react'
import { dataClient } from '../services/client.ts'
import { moveKey } from '../lib/hubOrder.ts'
import { useAsync } from './useAsync.ts'

// Módulo: a ordem dos cards do hub da pessoa numa organização.
// Parâmetro: a organização. Devolve: ready, order (keys salvas) e move(keys, active, over).
// Esconde: de onde vem (dataClient) e a troca otimista (o card muda na hora; se salvar falhar, volta).
export function useHubOrder(org: string) {
    // Sem ordem salva (ou se falhar) o hub usa a ordem do catálogo: não vale mostrar erro por isso.
    const { data, loading } = useAsync(() => dataClient.getHubOrder(org).catch(() => [] as string[]), [org])
    // O que a pessoa arrastou nesta visita. Guarda a org junto: trocar de org volta a valer o que veio do servidor.
    const [changed, setChanged] = useState<{ org: string; keys: string[] } | null>(null)

    const order = changed?.org === org ? changed.keys : (data ?? [])

    // keys = a ordem completa que está na tela; move `active` para o lugar de `over` e salva.
    function move(keys: string[], active: string, over: string) {
        const next = moveKey(keys, active, over)
        if (next === keys) return // soltou no mesmo lugar: nada a salvar
        const previous = order
        setChanged({ org, keys: next })
        dataClient.setHubOrder(org, next).catch(() => setChanged({ org, keys: previous })) // falhou: desfaz
    }

    return { ready: !loading, order, move }
}
