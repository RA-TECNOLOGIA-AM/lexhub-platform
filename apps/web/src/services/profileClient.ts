import type { SupabaseClient } from '@supabase/supabase-js'
import type { DataClient } from './client.ts'
import { DataError } from './errors.ts'
import { createRpc } from './rpc.ts'

type ProfileClient = Pick<
    DataClient,
    'uploadMyAvatar' | 'removeMyAvatar' | 'avatarUrl' | 'setMyAppearance' | 'getPasswordStatus' | 'setPassword'
>

const BUCKET = 'avatars'

// Códigos do Supabase Auth ao trocar a senha → mensagem para a pessoa.
const PASSWORD_ERRORS: Record<string, string> = {
    weak_password: 'Senha fraca. Use mais caracteres, com letras e números.',
    same_password: 'A nova senha é igual à atual.',
    reauthentication_needed: 'Entre de novo para trocar a senha.',
}

// Módulo: a foto de perfil pelo Supabase (bucket público 'avatars' + api.set_my_avatar).
// Cada troca grava um arquivo novo ('<user_id>/<data>.webp'), registra o caminho e apaga o anterior:
// nome novo = sem cache velho no navegador.
export function createProfileClient(supabase: SupabaseClient): ProfileClient {
    const call = createRpc(supabase)
    const bucket = () => supabase.storage.from(BUCKET)

    // O arquivo velho só ocupa espaço: se não der para apagar, a troca segue valendo.
    async function removeOld(path: string | null) {
        if (path)
            await bucket()
                .remove([path])
                .catch(() => undefined)
    }

    return {
        async uploadMyAvatar(image) {
            const { data } = await supabase.auth.getSession()
            const uid = data.session?.user.id
            if (!uid) throw new DataError(401, 'Entre de novo para trocar a foto.')

            const path = `${uid}/${Date.now()}.webp`
            const { error } = await bucket().upload(path, image, { contentType: 'image/webp', upsert: false })
            if (error) throw new DataError(0, 'Não foi possível enviar a foto. Tente de novo.')

            try {
                await removeOld(await call<string | null>('set_my_avatar', { p_path: path }))
            } catch (err) {
                await removeOld(path) // não registrou: não deixa o arquivo solto
                throw err
            }
            return path
        },
        async removeMyAvatar() {
            await removeOld(await call<string | null>('set_my_avatar', { p_path: null }))
        },
        avatarUrl: (path) => bucket().getPublicUrl(path).data.publicUrl,
        // Aparência: api.set_my_appearance grava os 4 campos na linha de quem está logado.
        async setMyAppearance({ mode, light, dark, accent }) {
            await call<null>('set_my_appearance', { p_mode: mode, p_light: light, p_dark: dark, p_accent: accent })
        },
        // Senha: o status vem do banco (só um boolean); a troca é do Supabase Auth, e a auditoria é um trigger.
        getPasswordStatus: () => call<boolean>('my_password_status'),
        async setPassword(password) {
            const { error } = await supabase.auth.updateUser({ password })
            if (error) {
                const message = PASSWORD_ERRORS[error.code ?? ''] ?? 'Não foi possível salvar a senha. Tente de novo.'
                throw new DataError(error.status ?? 0, message, error.code)
            }
        },
    }
}
