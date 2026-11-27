import { describe, expect, it } from 'vitest'
import { createMockMetaIntegration } from './metaIntegration.ts'

const SECRET = 'a'.repeat(32)

describe('Integração Meta no mock (mesmas regras da API)', () => {
    it('começa sem app; salvar chave testa, guarda e nunca devolve a chave', () => {
        const m = createMockMetaIntegration()
        expect(m.get()).toMatchObject({ appId: null, hasAppSecret: false, graphVersion: 'v26.0' })
        expect(m.get().origin).toEqual({
            appId: 'nenhum',
            appSecret: 'nenhum',
            graphVersion: 'padrão',
            syncInterval: 'padrão',
        })
        const out = m.save(
            { appId: '1234567', appSecret: SECRET, graphVersion: 'v26.0', syncPaused: false, syncIntervalMin: 10 },
            'Ana',
        )
        expect(out.saved).toBe(true)
        expect(out.checks.every((c) => c.ok)).toBe(true)
        expect(JSON.stringify(out)).not.toContain(SECRET)
        expect(out.integration).toMatchObject({ appId: '1234567', hasAppSecret: true, updatedBy: 'Ana' })
    })

    it('chave que a Meta recusa não grava', () => {
        const m = createMockMetaIntegration()
        const out = m.save(
            { appId: '1234567', appSecret: 'errado', graphVersion: 'v26.0', syncPaused: false, syncIntervalMin: 10 },
            'Ana',
        )
        expect(out.saved).toBe(false)
        expect(m.get().appId).toBeNull()
    })

    it('manter, pausar, trocar o ID (testa com a salva) e sem ID apaga a chave', () => {
        const m = createMockMetaIntegration()
        m.save(
            { appId: '1234567', appSecret: SECRET, graphVersion: 'v26.0', syncPaused: false, syncIntervalMin: 10 },
            'Ana',
        )
        const paused = m.save(
            { appId: '1234567', appSecret: null, graphVersion: 'v26.0', syncPaused: true, syncIntervalMin: 10 },
            'Ana',
        )
        expect(paused.checks).toEqual([])
        expect(paused.integration).toMatchObject({ hasAppSecret: true, syncPaused: true })
        const moved = m.save(
            { appId: '7654321', appSecret: null, graphVersion: 'v25.0', syncPaused: true, syncIntervalMin: 10 },
            'Ana',
        )
        expect(moved.checks.length).toBeGreaterThan(0)
        expect(moved.integration).toMatchObject({ appId: '7654321', graphVersion: 'v25.0' })
        const cleared = m.save(
            { appId: '', appSecret: null, graphVersion: 'v26.0', syncPaused: true, syncIntervalMin: 10 },
            'Ana',
        )
        expect(cleared.integration).toMatchObject({ appId: null, hasAppSecret: false })
        expect(() =>
            m.save(
                { appId: '', appSecret: SECRET, graphVersion: 'v26.0', syncPaused: false, syncIntervalMin: 10 },
                'Ana',
            ),
        ).toThrow(/ID do app/)
    })

    it('intervalo da atualização: padrão 10 min, grava o escolhido e recusa fora da lista', () => {
        const m = createMockMetaIntegration()
        expect(m.get()).toMatchObject({ syncIntervalMin: 10, intervals: [5, 10, 15, 30, 60] })
        expect(m.get().origin.syncInterval).toBe('padrão')
        const out = m.save(
            { appId: '', appSecret: null, graphVersion: 'v26.0', syncPaused: false, syncIntervalMin: 30 },
            'Ana',
        )
        expect(out.integration).toMatchObject({ syncIntervalMin: 30 })
        expect(out.integration.origin.syncInterval).toBe('tela')
        expect(() =>
            m.save({ appId: '', appSecret: null, graphVersion: 'v26.0', syncPaused: false, syncIntervalMin: 7 }, 'Ana'),
        ).toThrow(/Intervalo/)
    })

    it('testar sem chave nenhuma pede a chave; com a salva, passa', () => {
        const m = createMockMetaIntegration()
        expect(m.test({ appId: '1234567', appSecret: null, graphVersion: 'v26.0' }).ok).toBe(false)
        m.save(
            { appId: '1234567', appSecret: SECRET, graphVersion: 'v26.0', syncPaused: false, syncIntervalMin: 10 },
            'Ana',
        )
        expect(m.test({ appId: '1234567', appSecret: null, graphVersion: 'v26.0' })).toMatchObject({
            ok: true,
            app: 'LexHub Ads',
        })
    })
})
