import type { SupabaseClient } from '@supabase/supabase-js'
import { describe, expect, it } from 'vitest'
import { createProfileClient } from './profileClient.ts'

// Supabase falso com sessão, storage e rpc: guarda o que foi enviado, apagado e chamado.
function fake({
    previous = null as unknown,
    rpcError = false,
    authError = null as { code?: string; status?: number } | null,
} = {}) {
    const log = { uploads: [] as string[], removed: [] as string[], rpc: [] as unknown[], updates: [] as unknown[] }
    const supabase = {
        auth: {
            getSession: async () => ({ data: { session: { user: { id: 'u1' } } } }),
            updateUser: async (attrs: unknown) => {
                log.updates.push(attrs)
                return { data: { user: null }, error: authError }
            },
        },
        storage: {
            from: () => ({
                upload: async (path: string) => {
                    log.uploads.push(path)
                    return { error: null }
                },
                remove: async (paths: string[]) => {
                    log.removed.push(...paths)
                    return { error: null }
                },
                getPublicUrl: (path: string) => ({ data: { publicUrl: `https://x/avatars/${path}` } }),
            }),
        },
        schema: () => ({
            rpc: async (fn: string, args: unknown) => {
                log.rpc.push({ fn, args })
                return rpcError
                    ? { data: null, error: { code: '42501', message: 'Esta foto não é sua.' } }
                    : { data: previous, error: null }
            },
        }),
    } as unknown as SupabaseClient
    return { client: createProfileClient(supabase), log }
}

describe('createProfileClient', () => {
    it('envia na pasta da pessoa, registra o caminho e apaga a foto anterior', async () => {
        const { client, log } = fake({ previous: 'u1/velha.webp' })
        const path = await client.uploadMyAvatar(new Blob(['x']))
        expect(path).toMatch(/^u1\/\d+\.webp$/)
        expect(log.uploads).toEqual([path])
        expect(log.rpc).toEqual([{ fn: 'set_my_avatar', args: { p_path: path } }])
        expect(log.removed).toEqual(['u1/velha.webp'])
    })

    it('se o banco recusar, apaga o arquivo que acabou de enviar', async () => {
        const { client, log } = fake({ rpcError: true })
        await expect(client.uploadMyAvatar(new Blob(['x']))).rejects.toThrow()
        expect(log.removed).toEqual(log.uploads)
    })

    it('tirar a foto grava null e apaga o arquivo', async () => {
        const { client, log } = fake({ previous: 'u1/atual.webp' })
        await client.removeMyAvatar()
        expect(log.rpc).toEqual([{ fn: 'set_my_avatar', args: { p_path: null } }])
        expect(log.removed).toEqual(['u1/atual.webp'])
    })

    it('salva a aparência numa chamada só, com os 4 campos', async () => {
        const { client, log } = fake()
        await client.setMyAppearance({ mode: 'dark', light: null, dark: 'dark-nord', accent: '#2563eb' })
        expect(log.rpc).toEqual([
            {
                fn: 'set_my_appearance',
                args: { p_mode: 'dark', p_light: null, p_dark: 'dark-nord', p_accent: '#2563eb' },
            },
        ])
    })

    it('monta a URL pública', () => {
        expect(fake().client.avatarUrl('u1/a.webp')).toBe('https://x/avatars/u1/a.webp')
    })
    it('diz se a conta tem senha pela RPC my_password_status', async () => {
        const { client, log } = fake({ previous: true })
        expect(await client.getPasswordStatus()).toBe(true)
        expect(log.rpc).toEqual([{ fn: 'my_password_status', args: undefined }])
    })

    it('grava a senha pelo updateUser do Supabase', async () => {
        const { client, log } = fake()
        await client.setPassword('abc123')
        expect(log.updates).toEqual([{ password: 'abc123' }])
    })

    it.each([
        ['weak_password', 'Senha fraca. Use mais caracteres, com letras e números.'],
        ['same_password', 'A nova senha é igual à atual.'],
        ['reauthentication_needed', 'Entre de novo para trocar a senha.'],
        ['outro_erro', 'Não foi possível salvar a senha. Tente de novo.'],
    ])('erro %s do Supabase vira mensagem em português', async (code, message) => {
        const { client } = fake({ authError: { code, status: 422 } })
        await expect(client.setPassword('abc123')).rejects.toThrow(message)
    })
})
