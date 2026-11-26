import { useEffect, useSyncExternalStore } from 'react'
import { dataClient } from '../services/client.ts'

// Módulo: o número de chaves de API pendentes (o selo do menu do Desenvolvedor), igual a usePendingRequests.
// A página Chaves de API manda atualizar depois de cada decisão.
let count = 0
const listeners = new Set<() => void>()

function setCount(next: number) {
    count = next
    listeners.forEach((notify) => notify())
}

// Busca de novo no servidor. Erro: zera o selo, sem atrapalhar a tela.
export async function refreshPendingApiKeys(org: string): Promise<void> {
    try {
        setCount(org ? await dataClient.countPendingApiKeys(org) : 0)
    } catch {
        setCount(0)
    }
}

const subscribe = (notify: () => void) => {
    listeners.add(notify)
    return () => listeners.delete(notify)
}

// Lê o número e, quando `enabled` (só Desenvolvedor), busca ao montar e ao trocar de organização.
export function usePendingApiKeys(org: string, enabled: boolean): number {
    useEffect(() => {
        if (enabled) void refreshPendingApiKeys(org)
    }, [org, enabled])
    const value = useSyncExternalStore(subscribe, () => count)
    return enabled ? value : 0
}
