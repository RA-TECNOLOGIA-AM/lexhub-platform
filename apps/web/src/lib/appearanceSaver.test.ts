import { describe, expect, it } from 'vitest'
import type { Appearance } from '../types/index.ts'
import { createAppearanceSaver, SAVE_ERROR } from './appearanceSaver.ts'

const theme = (dark: string): Appearance => ({ mode: 'dark', light: null, dark, accent: null })

// Envio falso: cada chamada fica pendente até o teste resolver (ou rejeitar) na ordem que quiser.
function controlledSend() {
    const calls: { appearance: Appearance; resolve: () => void; reject: () => void }[] = []
    let inFlight = 0
    let maxInFlight = 0
    const send = (appearance: Appearance) =>
        new Promise<void>((resolve, reject) => {
            inFlight++
            maxInFlight = Math.max(maxInFlight, inFlight)
            const done = (fn: () => void) => () => {
                inFlight--
                fn()
            }
            calls.push({ appearance, resolve: done(resolve), reject: done(() => reject(new Error('falhou'))) })
        })
    return { send, calls, maxInFlight: () => maxInFlight }
}

const tick = () => new Promise((r) => setTimeout(r, 0))

describe('createAppearanceSaver', () => {
    it('cliques rápidos: envia o primeiro e, quando ele termina, só o mais novo (nunca dois ao mesmo tempo)', async () => {
        const { send, calls, maxInFlight } = controlledSend()
        const save = createAppearanceSaver(send, () => {})

        const done = Promise.all([save(theme('dark-nord')), save(theme('dark-dracula')), save(theme('dark-omni'))])
        await tick()
        expect(calls.map((c) => c.appearance.dark)).toEqual(['dark-nord'])

        calls[0].resolve()
        await tick()
        expect(calls.map((c) => c.appearance.dark)).toEqual(['dark-nord', 'dark-omni'])

        calls[1].resolve()
        await done
        expect(maxInFlight()).toBe(1)
    })

    it('falha avisa; o próximo envio que dá certo limpa o aviso', async () => {
        const { send, calls } = controlledSend()
        const errors: (string | null)[] = []
        const save = createAppearanceSaver(send, (message) => errors.push(message))

        const first = save(theme('dark-nord'))
        await tick()
        calls[0].reject()
        await first
        expect(errors.at(-1)).toBe(SAVE_ERROR)
        expect(SAVE_ERROR).toBe('Não foi possível salvar na sua conta.')

        const second = save(theme('dark-dracula'))
        await tick()
        calls[1].resolve()
        await second
        expect(errors.at(-1)).toBeNull()
    })

    it('depois de esvaziar a fila, um novo clique envia na hora', async () => {
        const { send, calls } = controlledSend()
        const save = createAppearanceSaver(send, () => {})
        const first = save(theme('dark-nord'))
        await tick()
        calls[0].resolve()
        await first

        void save(theme('dark-dracula'))
        await tick()
        expect(calls).toHaveLength(2)
    })
})
