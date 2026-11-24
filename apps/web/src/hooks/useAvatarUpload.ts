import { useEffect, useRef, useState, type ChangeEvent } from 'react'
import { useAuth } from '../contexts/auth-context.ts'
import type { CropArea } from '../lib/avatarCrop.ts'
import { AVATAR_ACCEPT, avatarFileError, toAvatarBlob } from '../lib/avatarImage.ts'
import { dataClient } from '../services/client.ts'
import { DataError, toDataError } from '../services/errors.ts'

// Módulo: trocar ou tirar a própria foto de perfil (popover do avatar e Configurações → Perfil).
// Escolher o arquivo abre o "Ajustar foto do perfil" (props em `crop`, para quem usa renderizar o
// <AvatarCropDialog>); "Salvar foto" corta a área escolhida, envia e atualiza o avatar em toda a tela.
// Quem usa desenha os botões e o <input type="file"> com as props de `input`.
export function useAvatarUpload() {
    const { setAvatarPath } = useAuth()
    const [busy, setBusy] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [pending, setPending] = useState<{ file: File; url: string } | null>(null) // foto sendo ajustada
    const fileInput = useRef<HTMLInputElement>(null)

    // A URL local da foto em ajuste é liberada ao trocar de foto, fechar ou sair da tela.
    useEffect(() => {
        if (!pending) return
        return () => URL.revokeObjectURL(pending.url)
    }, [pending])

    async function run(action: () => Promise<string | null>): Promise<boolean> {
        setBusy(true)
        setError(null)
        try {
            setAvatarPath(await action())
            return true
        } catch (err) {
            setError(toDataError(err).message)
            return false
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
        setError(null)
        setPending({ file, url: URL.createObjectURL(file) })
    }

    async function save(area: CropArea) {
        if (!pending) return
        const { file } = pending
        const saved = await run(async () => {
            const image = await toAvatarBlob(file, area).catch(() => {
                throw new DataError(0, 'Não foi possível ler esta foto.')
            })
            return dataClient.uploadMyAvatar(image)
        })
        if (saved) setPending(null)
    }

    const choose = () => fileInput.current?.click() // abre o seletor de arquivo

    return {
        busy,
        error: pending ? null : error, // com o modal aberto, o erro aparece nele
        clearError: () => setError(null),
        choose,
        remove: () =>
            void run(async () => {
                await dataClient.removeMyAvatar()
                return null
            }),
        input: { ref: fileInput, type: 'file', accept: AVATAR_ACCEPT, hidden: true, onChange } as const,
        // Props do <AvatarCropDialog> (null = fechado).
        crop: pending
            ? {
                  src: pending.url,
                  busy,
                  error,
                  onCancel: () => {
                      setError(null)
                      setPending(null)
                  },
                  onChange: choose,
                  onSave: (area: CropArea) => void save(area),
              }
            : null,
    }
}
