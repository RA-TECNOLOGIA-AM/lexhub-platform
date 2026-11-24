import { renderToStaticMarkup } from 'react-dom/server'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ExportButton } from '../components/dashboard/ExportButton.tsx'
import { logViewOnce } from '../hooks/useLogDashboardView.ts'
import { getSupport, onSupportExpired, setSupport, supportValidFor } from '../lib/supportSession.ts'
import { DataError } from '../services/errors.ts'
import { withSupportExpiry } from '../services/supportExpiry.ts'
import type { SupportSession } from '../types/index.ts'

const session: SupportSession = {
    sessionId: 's1',
    org: 'lexgroup',
    expiresAt: '2026-11-24T15:00:00Z',
    reason: 'Chamado 42',
    member: {
        membershipId: 'm1',
        name: 'Ana Souza',
        avatarPath: null,
        roleLabel: 'Colaborador',
        units: [{ code: 'NG', name: 'Nova Gestão' }],
    },
}
const BEFORE = Date.parse('2026-11-24T14:30:00Z')
const AFTER = Date.parse('2026-11-24T15:00:01Z')

describe('modo suporte', () => {
    beforeEach(() => setSupport(null))
    afterEach(() => setSupport(null))

    describe('409 support_expired (withSupportExpiry)', () => {
        const failing = (err: unknown) => withSupportExpiry({ load: () => Promise.reject(err) })

        it('limpa a sessão e avisa que venceu; o erro continua subindo', async () => {
            setSupport(session)
            const expired = vi.fn()
            const off = onSupportExpired(expired)
            await expect(failing(new DataError(409, 'support_expired')).load()).rejects.toThrow('support_expired')
            off()
            expect(getSupport()).toBeNull()
            expect(expired).toHaveBeenCalledTimes(1)
        })

        it('outro erro (ex.: 403 support_read_only, 409 de regra) não mexe na sessão', async () => {
            setSupport(session)
            await expect(failing(new DataError(403, 'support_read_only')).load()).rejects.toThrow()
            await expect(failing(new DataError(409, 'Unidade travada')).load()).rejects.toThrow()
            expect(getSupport()).toEqual(session)
        })

        it('sem sessão (ex.: resposta atrasada depois de Sair), não avisa nada', async () => {
            const expired = vi.fn()
            const off = onSupportExpired(expired)
            await expect(failing(new DataError(409, 'support_expired')).load()).rejects.toThrow()
            off()
            expect(expired).not.toHaveBeenCalled()
        })

        it('chamada que dá certo passa igual', async () => {
            const client = withSupportExpiry({ sum: async (a: number, b: number) => a + b, name: 'x' })
            expect(await client.sum(1, 2)).toBe(3)
            expect(client.name).toBe('x')
        })
    })

    describe('supportValidFor (sessão restaurada)', () => {
        it('vale na organização dela, dentro do prazo', () => {
            expect(supportValidFor(session, '/lexgroup/dashboards', BEFORE)).toBe(true)
            expect(supportValidFor(session, '/lexgroup/NG/dashboards/protocolo', BEFORE)).toBe(true)
        })
        it('outra organização na URL: não vale (o cabeçalho nunca vai para outra org)', () => {
            expect(supportValidFor(session, '/outra-org/dashboards', BEFORE)).toBe(false)
        })
        it('prazo vencido: não vale', () => {
            expect(supportValidFor(session, '/lexgroup/dashboards', AFTER)).toBe(false)
        })
        it('rota fora de organização (plataforma, ativar): vale (a rota redireciona ao hub da sessão)', () => {
            expect(supportValidFor(session, '/plataforma/clientes', BEFORE)).toBe(true)
        })
    })

    describe('useLogDashboardView (logViewOnce)', () => {
        it('com sessão de suporte ativa, não registra a abertura', () => {
            setSupport(session)
            const log = vi.fn(() => Promise.resolve())
            logViewOnce('lexgroup', 'NG', 'suporte-teste', log)
            expect(log).not.toHaveBeenCalled()
        })
        it('fora do suporte, registra uma vez', () => {
            const log = vi.fn(() => Promise.resolve())
            logViewOnce('lexgroup', 'NG', 'fora-teste', log)
            logViewOnce('lexgroup', 'NG', 'fora-teste', log)
            expect(log).toHaveBeenCalledTimes(1)
        })
    })

    describe('ExportButton', () => {
        const render = () =>
            renderToStaticMarkup(<ExportButton canExport title="Protocolo" reports={[]} onExport={async () => {}} />)
        it('em suporte, no lugar do botão aparece "Somente leitura no modo suporte"', () => {
            setSupport(session)
            const html = render()
            expect(html).toContain('Somente leitura no modo suporte')
            expect(html).not.toContain('Exportar')
        })
        it('fora do suporte, o botão Exportar', () => {
            expect(render()).toContain('Exportar')
        })
    })

    describe('SupportProvider', () => {
        it('com o sessionStorage já preenchido ao montar, abre em modo suporte', async () => {
            vi.resetModules()
            sessionStorage.setItem('lexhub.support', JSON.stringify(session))
            vi.useFakeTimers({ now: BEFORE, toFake: ['Date'] })
            try {
                const { renderToStaticMarkup: render } = await import('react-dom/server')
                const { MemoryRouter } = await import('react-router')
                const { SupportProvider } = await import('./SupportProvider.tsx')
                const { useSupport } = await import('./support-context.ts')
                function Probe() {
                    const { session: s } = useSupport()
                    return <span>{s ? `suporte:${s.member.name}` : 'normal'}</span>
                }
                const html = render(
                    <MemoryRouter initialEntries={['/lexgroup/dashboards']}>
                        <SupportProvider>
                            <Probe />
                        </SupportProvider>
                    </MemoryRouter>,
                )
                expect(html).toContain('suporte:Ana Souza')
            } finally {
                vi.useRealTimers()
                sessionStorage.removeItem('lexhub.support')
            }
        })
    })
})
