import { useCallback, useEffect, useState, type ReactNode } from 'react'
import { dataClient } from '../services/client.ts'
import { DataError } from '../services/errors.ts'
import type { Me } from '../types/index.ts'
import { AuthContext, type AuthValue } from './auth-context.ts'
import { loadSession, type SessionState } from './session.ts'

// Guarda quem está logado e entrega isso para o app inteiro via contexto.
export function AuthProvider({ children }: { children: ReactNode }) {
    const [me, setMe] = useState<Me | null>(null)
    const [noAccess, setNoAccess] = useState<AuthValue['noAccess']>(null)
    const [loading, setLoading] = useState(true)
    const [rememberLocation, setRememberLocation] = useState(true)

    // O estado da sessão vira me + noAccess (os dois nunca ficam preenchidos juntos).
    const apply = useCallback((state: SessionState) => {
        setMe(state.status === 'signed-in' ? state.me : null)
        setNoAccess(state.status === 'no-access' ? { email: state.email } : null)
    }, [])

    // Ao abrir o app (ou dar F5, ou voltar do Google): já existe sessão? Com organização?
    useEffect(() => {
        let ignore = false
        loadSession(dataClient)
            .then((state) => {
                if (!ignore) apply(state)
            })
            .finally(() => {
                if (!ignore) setLoading(false)
            })
        return () => {
            ignore = true
        }
    }, [apply])

    // Depois de entrar: confere a sessão. Entrou, mas a API não respondeu = erro para a tela mostrar.
    async function afterSignIn() {
        setRememberLocation(true)
        const state = await loadSession(dataClient)
        if (state.status === 'signed-out') {
            throw new DataError(0, 'Você entrou, mas não foi possível carregar o seu acesso. Tente de novo.')
        }
        apply(state)
    }

    async function signIn(email: string, password: string) {
        await dataClient.signIn(email, password)
        await afterSignIn()
    }

    // Na API, o navegador sai para o Google: nada a fazer aqui (a volta recarrega o app e o
    // useEffect acima confere a sessão). No mock, entra direto: confere a sessão como no signIn.
    async function signInWithGoogle() {
        if ((await dataClient.signInWithGoogle()) === 'signed-in') await afterSignIn()
    }

    // Confere de novo se a pessoa já tem acesso (ex.: pedido aprovado). Com acesso, o login leva ao hub.
    async function refreshSession() {
        const state = await loadSession(dataClient)
        if (state.status === 'signed-out') {
            throw new DataError(0, 'Não foi possível conferir o seu acesso. Tente de novo.')
        }
        apply(state)
    }

    // Padrão: 'Sair' do usuário (o próximo login vai para o hub).
    // returnHere: true = sessão caiu (401); o próximo login volta para a mesma página.
    async function signOut({ returnHere = false }: { returnHere?: boolean } = {}) {
        await dataClient.signOut()
        setRememberLocation(returnHere)
        apply({ status: 'signed-out' })
    }

    // useCallback: a mesma função entre renderizações, para o OrgScope poder usá-la num useEffect
    // sem buscar o "me" de novo a cada renderização.
    const switchOrg = useCallback(async (slug: string) => {
        setMe(await dataClient.getMe(slug))
    }, [])

    return (
        <AuthContext
            value={{
                me,
                noAccess,
                loading,
                rememberLocation,
                signIn,
                signInWithGoogle,
                signOut,
                switchOrg,
                refreshSession,
            }}
        >
            {children}
        </AuthContext>
    )
}
