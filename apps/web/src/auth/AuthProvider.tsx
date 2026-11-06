import { useEffect, useState, type ReactNode } from 'react'
import { dataClient } from '../data/client.ts'
import type { Me } from '../data/types.ts'
import { AuthContext } from './auth-context.ts'

// Guarda quem está logado e entrega isso para o app inteiro via contexto.
export function AuthProvider({ children }: { children: ReactNode }) {
    const [me, setMe] = useState<Me | null>(null)
    const [loading, setLoading] = useState(true)

    // Ao abrir o app (ou dar F5): já existe sessão? getMe() responde ou dá 401.
    useEffect(() => {
        let ignore = false
        dataClient
            .getMe()
            .then((data) => {
                if (!ignore) setMe(data)
            })
            .catch(() => {
                if (!ignore) setMe(null)
            })
            .finally(() => {
                if (!ignore) setLoading(false)
            })
        return () => {
            ignore = true
        }
    }, [])

    async function signIn(email: string, password: string) {
        await dataClient.signIn(email, password)
        setMe(await dataClient.getMe())
    }

    async function signOut() {
        await dataClient.signOut()
        setMe(null)
    }

    return <AuthContext value={{ me, loading, signIn, signOut }}>{children}</AuthContext>
}