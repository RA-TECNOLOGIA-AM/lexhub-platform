import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { ApiKeysView, type ApiKeysViewProps } from './ApiKeysPage.tsx'
import { pendingExtras } from './apiKeysView.ts'
import type { ApiKeyInfo } from '../../../types/index.ts'

const base = { setor: 'Comercial', base: true, status: 'approved' as const, justificativa: null, expiresAt: null }
const KEY: ApiKeyInfo = {
    id: 'k1',
    userName: 'Beatriz Lima',
    userEmail: 'beatriz@x.com',
    status: 'pending',
    note: 'Power BI das metas',
    decisionNote: null,
    requestedAt: '2026-11-26T12:00:00Z',
    decidedAt: null,
    revokedAt: null,
    lastUsedAt: null,
    lastUsedIp: null,
    sectors: [
        base,
        {
            setor: 'Financeiro',
            base: false,
            status: 'pending',
            justificativa: 'Cruzar vendas com recebimentos',
            expiresAt: '2027-02-25T03:00:00Z',
        },
        {
            setor: 'Protocolo',
            base: false,
            status: 'pending',
            justificativa: 'Metas do protocolo',
            expiresAt: '2027-01-01T03:00:00Z',
        },
    ],
}
const ACTIVE: ApiKeyInfo = {
    ...KEY,
    status: 'active',
    decidedAt: '2026-11-26T13:00:00Z',
    lastUsedAt: '2026-11-26T14:00:00Z',
    lastUsedIp: '203.0.113.7',
    sectors: [
        base,
        { ...KEY.sectors[1], status: 'approved' },
        { ...KEY.sectors[2], status: 'rejected' },
    ],
}
const noop = () => {}
const props = (over: Partial<ApiKeysViewProps>): ApiKeysViewProps => ({
    tab: 'pending',
    keys: [KEY],
    selectedId: null,
    busy: false,
    error: '',
    onTab: noop,
    onSelect: noop,
    onDecide: noop,
    onRevoke: noop,
    onRevokeSector: noop,
    ...over,
})
const render = (over: Partial<ApiKeysViewProps>) => renderToStaticMarkup(<ApiKeysView {...props(over)} />)

describe('pendingExtras', () => {
    it('só os extras pendentes, na ordem', () => {
        expect(pendingExtras(KEY)).toEqual(['Financeiro', 'Protocolo'])
        expect(pendingExtras(ACTIVE)).toEqual([])
    })
})

describe('ApiKeysView', () => {
    it('lista vazia: avisa', () => {
        expect(render({ keys: [] })).toContain('Nenhum pedido pendente')
    })

    it('pedido selecionado: setores extras com justificativa, validade e as duas ações', () => {
        const html = render({ selectedId: 'k1' })
        expect(html).toContain('Beatriz Lima')
        expect(html).toContain('Power BI das metas')
        expect(html).toContain('Cruzar vendas com recebimentos')
        expect(html).toContain('24/02/2027')
        expect(html).toContain('Aprovar')
        expect(html).toContain('Recusar')
    })

    it('chave ativa: revogar só os extras aprovados e a chave', () => {
        const html = render({ tab: 'active', keys: [ACTIVE], selectedId: 'k1' })
        expect(html.match(/Revogar setor/g)?.length).toBe(1)
        expect(html).toContain('Revogar chave')
        expect(html).not.toContain('Aprovar')
    })

    it('chave ativa: último uso com o IP, sem nenhum token', () => {
        const html = render({ tab: 'active', keys: [ACTIVE], selectedId: 'k1' })
        expect(html).toContain('IP 203.0.113.7')
        expect(html).not.toMatch(/lxr_|eyJ/)
    })

    it('chave nunca usada: sem IP', () => {
        const html = render({ tab: 'active', keys: [{ ...ACTIVE, lastUsedAt: null, lastUsedIp: null }], selectedId: 'k1' })
        expect(html).toContain('nunca')
        expect(html).not.toContain('IP ')
    })
})
