import { isValidElement, type ReactElement, type ReactNode } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it, vi } from 'vitest'
import type { SupportSession } from '../../types/index.ts'
import { SupportBannerView } from './SupportBanner.tsx'

const session: SupportSession = {
    sessionId: 's1',
    org: 'lexgroup',
    expiresAt: '2026-11-24T15:00:00Z',
    reason: 'Chamado 42',
    member: {
        membershipId: 'm1',
        name: 'Ana Maria Souza',
        avatarPath: null,
        roleLabel: 'Colaborador',
        units: [],
    },
}
const now = Date.parse('2026-11-24T14:35:30Z') // faltam 24,5 min

// Procura, na árvore de elementos, o botão cujo texto contém `text` (sem DOM: os testes rodam em Node).
function findButton(node: ReactNode, text: string): ReactElement<{ onClick?: () => void }> | null {
    if (Array.isArray(node)) {
        for (const child of node) {
            const hit = findButton(child, text)
            if (hit) return hit
        }
        return null
    }
    if (!isValidElement<{ children?: ReactNode; onClick?: () => void }>(node)) return null
    if (node.type === 'button' && renderToStaticMarkup(node).includes(text)) return node
    return findButton(node.props.children, text)
}

describe('SupportBanner', () => {
    it('mostra o nome, o motivo e o tempo que falta, como status (aviso)', () => {
        const html = renderToStaticMarkup(<SupportBannerView session={session} now={now} onExit={() => {}} />)
        expect(html).toContain('role="status"')
        expect(html).toContain('Vendo como')
        expect(html).toContain('Ana Maria Souza')
        expect(html).toContain('Chamado 42')
        expect(html).toContain('termina em 25 min')
        // No celular só cabe o primeiro nome (o CSS escolhe qual mostrar).
        expect(html).toContain('>Ana<')
    })

    it('Sair chama exit', () => {
        const onExit = vi.fn()
        const button = findButton(SupportBannerView({ session, now, onExit }), 'Sair')
        expect(button).not.toBeNull()
        button?.props.onClick?.()
        expect(onExit).toHaveBeenCalledTimes(1)
    })
})
