import { createContext, useContext, useSyncExternalStore } from 'react'
import { getSupport, onSupportChange } from '../lib/supportSession.ts'
import type { SupportSession } from '../types/index.ts'

export type SupportState = {
    session: SupportSession | null // null = fora do modo suporte
    // Owner/Dev: inicia a sessão (o servidor confere), guarda e vai para o hub do membro.
    start(membershipId: string, name: string, reason: string): Promise<void>
    // Encerra (falha é ignorada), limpa e volta à gaveta do membro em Membros.
    exit(): Promise<void>
    notice: string | null // "A sessão de suporte venceu" (o layout mostra; null = nada)
    clearNotice(): void
}

export const SupportContext = createContext<SupportState | null>(null)

// Qualquer componente dentro do <SupportProvider> lê e controla o modo suporte com useSupport().
export function useSupport(): SupportState {
    const value = useContext(SupportContext)
    if (!value) throw new Error('useSupport() precisa estar dentro de <SupportProvider>')
    return value
}

// Só a sessão, direto do guardado (lib/supportSession.ts), sem precisar do provider: serve aos botões que
// somem no modo (estrela, arrastar, exportar), que também aparecem em testes e telas fora do provider.
export function useSupportSession(): SupportSession | null {
    return useSyncExternalStore(onSupportChange, getSupport, getSupport)
}
