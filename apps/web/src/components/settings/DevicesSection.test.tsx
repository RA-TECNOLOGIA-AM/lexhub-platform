import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { DevicesList } from './DevicesSection.tsx'
import type { DeviceGroup } from './devices.ts'

const NOW = Date.parse('2026-11-24T12:00:00Z')
const group = (over: Partial<DeviceGroup>): DeviceGroup => ({
    key: 'k',
    ids: ['a'],
    label: 'Chrome · Windows',
    ip: '10.0.0.1',
    kind: 'computer',
    lastActiveAt: '2026-11-24T12:00:00Z',
    current: false,
    ...over,
})
const noop = () => {}
const render = (groups: DeviceGroup[]) =>
    renderToStaticMarkup(
        <DevicesList groups={groups} now={NOW} busy={false} onRevoke={noop} onRevokeOthers={noop} onSignOut={noop} />,
    )

describe('DevicesList', () => {
    it('este dispositivo + um grupo de outro aparelho', () => {
        const html = render([
            group({ key: 'cur', current: true }),
            group({
                key: 'cel',
                ids: ['p1', 'p2'],
                label: 'Chrome · Android',
                kind: 'phone',
                ip: '177.1.1.1',
                lastActiveAt: '2026-11-24T11:55:00Z',
            }),
        ])
        expect(html).toContain('Este dispositivo')
        expect(html).toContain('Sair deste dispositivo')
        expect(html).toContain('Chrome · Android')
        expect(html).toContain('177.1.1.1 · ativo há 5 min · 2 sessões')
        expect(html).toContain('Desconectar todos os outros')
    })

    it('só este aparelho: avisa que não há outros', () => {
        const html = render([group({ current: true })])
        expect(html).not.toContain('Desconectar todos os outros')
        expect(html).toContain('não está aberta em nenhum outro aparelho')
    })
})
