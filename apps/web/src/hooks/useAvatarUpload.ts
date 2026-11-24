import { useRef, useState, type ChangeEvent } from 'react'
import { useAuth } from '../contexts/auth-context.ts'
import { AVATAR_ACCEPT, avatarFileError, toAvatarBlob } from '../lib/avatarImage.ts'
import { dataClient } from '../services/client.ts'
import { DataError, toDataError } from '../services/errors.ts'

// Módulo: trocar ou tirar a própria foto de perfil (popover do avatar e Configurações → Perfil).
// Quem usa desenha os botões e o <input type="file"> com as props de `input`; o hook confere o arquivo,
// corta, envia, atualiza o avatar em toda a tela e guarda o erro para mostrar ali mesmo.
export function useAvatarUpload() {
    const { setAvatarPath } = useAuth()
    const [busy, setBusy] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const fileInput = useRef<HTMLInputElement>(null)

    async function run(action: () => Promise<string | null>) {
        setBusy(true)
        setError(null)
        try {
            setAvatarPath(await action())
        } catch (err) {
            setError(toDataError(err).message)
        } finally {
            setBusy(false)
        }
    }

    function onChange(e: ChangeEvent<HTMLInputElement>) {
        const file = e.target.files?.[0]
        e.target.value = '' // escolher a mesma foto de novo também dispara
        if (!file) return
        const invalid = avatarFileError(file)
        if (invalid) {
            setError(invalid)
            return
        }
        void run(async () => {
            const image = await toAvatarBlob(file).catch(() => {
                throw new DataError(0, 'Não foi possível ler esta foto.')
            })
            return dataClient.uploadMyAvatar(image)
        })
    }

    return {
        busy,
        error,
        clearError: () => setError(null),
        choose: () => fileInput.current?.click(), // abre o seletor de arquivo
        remove: () =>
            void run(async () => {
                await dataClient.removeMyAvatar()
                return null
            }),
        input: { ref: fileInput, type: 'file', accept: AVATAR_ACCEPT, hidden: true, onChange } as const,
    }
}
