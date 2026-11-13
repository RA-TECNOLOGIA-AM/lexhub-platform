import type { AppNotification, NotificationsResponse } from '../../types/index.ts'

// Módulo: as notificações do mock, em memória por e-mail (somem no F5), com as mesmas regras do banco:
// cada pessoa vê e marca só as próprias. Parâmetro: o relógio (trocável nos testes).
export function createNotificationsStore(now: () => Date = () => new Date()) {
    const byEmail = new Map<string, AppNotification[]>()
    let nextId = 1

    const own = (email: string) => byEmail.get(email) ?? []

    return {
        add(email: string, notification: Omit<AppNotification, 'id' | 'created_at' | 'read_at'>) {
            const created: AppNotification = {
                ...notification,
                id: `notif-${nextId++}`,
                created_at: now().toISOString(),
                read_at: null,
            }
            byEmail.set(email, [created, ...own(email)])
        },

        list(email: string): NotificationsResponse {
            const items = own(email)
            return { items: structuredClone(items.slice(0, 20)), unread: items.filter((n) => !n.read_at).length }
        },

        markRead(email: string, ids: string[] | null) {
            const at = now().toISOString()
            byEmail.set(
                email,
                own(email).map((n) => (!n.read_at && (ids === null || ids.includes(n.id)) ? { ...n, read_at: at } : n)),
            )
        },
    }
}
