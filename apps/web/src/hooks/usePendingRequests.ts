import { useEffect, useSyncExternalStore } from 'react'
import { dataClient } from '../services/client.ts'

// Módulo: o número de pedidos de acesso pendentes (o selo do menu da equipe RA).
// Um valor só para o app inteiro: o menu lê; a página de pedidos manda atualizar depois de cada decisão.
let count = 0
const listeners = new Set<() => void>()

function setCount(next: number) {
    count = next
    listeners.forEach((notify) => notify())
}

// Busca de novo no servidor. Erro (ex.: sem permissão): zera o selo, sem atrapalhar a tela.
export async function refreshPendingRequests(): Promise<void> {
    try {
        setCount(await dataClient.countPendingAccessRequests())
    } catch {
        setCount(0)
    }
}

const subscribe = (notify: () => void) => {
    listeners.add(notify)
    return () => listeners.delete(notify)
}

// Lê o número e, quando `enabled` (só equipe RA), busca ao montar.
export function usePendingRequests(enabled: boolean): number {
    useEffect(() => {
        if (enabled) void refreshPendingRequests()
    }, [enabled])
    const value = useSyncExternalStore(subscribe, () => count)
    return enabled ? value : 0
}
