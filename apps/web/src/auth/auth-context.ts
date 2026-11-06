import { createContext, useContext } from 'react'
import type { Me } from '../data/types.ts'

export type AuthValue = {
    me: Me | null // null = ninguém logado
    loading: boolean // true enquanto confere se já existe sessão (ao abrir o app)
    // false depois de um 'Sair' do usuário: aí o próximo login vai para o hub, não para a página anterior
    rememberLocation: boolean
    signIn(email: string, password: string): Promise<void>
    // returnHere: true quando a sessão caiu (401) e o usuário deve voltar para a mesma página depois de entrar
    signOut(options?: { returnHere?: boolean }): Promise<void>
}

export const AuthContext = createContext<AuthValue | null>(null)

// Qualquer componente dentro do <AuthProvider> lê a sessão com useAuth().
export function useAuth(): AuthValue {
    const value = useContext(AuthContext)
    if (!value) throw new Error('useAuth() precisa estar dentro de <AuthProvider>')
    return value
}