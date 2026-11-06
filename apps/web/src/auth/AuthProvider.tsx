import { useEffect, useState, type ReactNode } from 'react'
import { dataClient } from '../data/client.ts'
import type { Me } from '../data/types.ts'
import { AuthContext } from './auth-context.ts'

// Guarda quem está logado e entrega isso para o app inteiro via contexto.
export function AuthProvider({ children }: { children: ReactNode }) {
    const [me, setMe] = useState<Me | null>(null)
    const [loading, setLoading] = useState(true)
    const [rememberLocation, setRememberLocation] = useState(true)
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
        setRememberLocation(true)
        setMe(await dataClient.getMe())
    }

    // Padrão: 'Sair' do usuário (o próximo login vai para o hub).
    // returnHere: true = sessão caiu (401); o próximo login volta para a mesma página.
    async function signOut({ returnHere = false }: { returnHere?: boolean } = {}) {
        await dataClient.signOut()
        setRememberLocation(returnHere)
        setMe(null)
    }
    return <AuthContext value={{ me, loading, rememberLocation, signIn, signOut }}>{children}</AuthContext>
}
