import type { AccountSession } from '../types/index.ts'

const minutesAgo = (min: number, now: number) => new Date(now - min * 60_000).toISOString()

// Módulo: as sessões da conta no modo mock (Configurações → Dispositivos). Em memória: F5 volta ao início.
// A atual é este navegador; as outras são um celular com dois logins (mesmo IP) e a TV do QR.
export function createMockDevices(now: () => number = Date.now) {
    const t = now()
    let sessions: AccountSession[] = [
        {
            id: 'mock-atual',
            createdAt: minutesAgo(60 * 26, t),
            lastActiveAt: minutesAgo(0, t),
            userAgent: typeof navigator === 'undefined' ? null : navigator.userAgent,
            ip: '187.10.20.30',
            current: true,
        },
        {
            id: 'mock-celular-1',
            createdAt: minutesAgo(60 * 50, t),
            lastActiveAt: minutesAgo(5, t),
            userAgent: 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/131.0 Mobile Safari/537.36',
            ip: '177.55.1.2',
            current: false,
        },
        {
            id: 'mock-celular-2',
            createdAt: minutesAgo(60 * 120, t),
            lastActiveAt: minutesAgo(60 * 30, t),
            userAgent: 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/130.0 Mobile Safari/537.36',
            ip: '177.55.1.2',
            current: false,
        },
        {
            id: 'mock-tv',
            createdAt: minutesAgo(60 * 4, t),
            lastActiveAt: minutesAgo(12, t),
            userAgent: 'python-httpx/0.27.0',
            ip: '187.10.20.31',
            current: false,
        },
    ]
    return {
        list: (): AccountSession[] => sessions.map((s) => ({ ...s })),
        revoke(id: string) {
            sessions = sessions.filter((s) => s.current || s.id !== id)
        },
        revokeOthers() {
            sessions = sessions.filter((s) => s.current)
        },
    }
}
