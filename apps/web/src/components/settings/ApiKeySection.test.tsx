import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { ApiKeyView, type ApiKeyViewProps } from './ApiKeySection.tsx'
import { addDays, validateRequest } from './apiKey.ts'
import type { ApiKeyInfo } from '../../types/index.ts'

const TODAY = '2026-11-26'
const extra = (over = {}) => ({ setor: 'Protocolo', justificativa: 'Automação de metas', validade: '2027-01-31', ...over })

describe('validateRequest', () => {
    it('aceita setor base sem extra e extra válido', () => {
        expect(validateRequest(['Comercial'], [], TODAY)).toBeNull()
        expect(validateRequest(['Comercial'], [extra()], TODAY)).toBeNull()
    })
    it('sem setor base exige ao menos um extra', () => {
        expect(validateRequest([], [], TODAY)).toMatch(/setor extra/)
    })
    it('justificativa curta, setor vazio e validade fora da faixa bloqueiam', () => {
        expect(validateRequest([], [extra({ justificativa: 'curta' })], TODAY)).toMatch(/10 caracteres/)
        expect(validateRequest([], [extra({ setor: '' })], TODAY)).toMatch(/Escolha o setor/)
        expect(validateRequest([], [extra({ validade: TODAY })], TODAY)).toMatch(/365 dias/)
        expect(validateRequest([], [extra({ validade: addDays(TODAY, 366) })], TODAY)).toMatch(/365 dias/)
        expect(validateRequest([], [extra({ validade: addDays(TODAY, 365) })], TODAY)).toBeNull()
    })
    it('setor repetido bloqueia', () => {
        expect(validateRequest([], [extra(), extra()], TODAY)).toMatch(/mais de uma vez/)
    })
})

const KEY: ApiKeyInfo = {
    id: 'k1',
    userName: 'Ana',
    userEmail: 'ana@x.com',
    status: 'active',
    note: null,
    decisionNote: null,
    requestedAt: '2026-11-26T12:00:00Z',
    decidedAt: '2026-11-26T13:00:00Z',
    revokedAt: null,
    lastUsedAt: null,
    sectors: [
        { setor: 'Comercial', base: true, status: 'approved', justificativa: null, expiresAt: null },
        {
            setor: 'Protocolo',
            base: false,
            status: 'approved',
            justificativa: 'Automação',
            expiresAt: '2027-02-01T02:59:59Z',
        },
    ],
}
const noop = () => {}
const props = (over: Partial<ApiKeyViewProps>): ApiKeyViewProps => ({
    eligibility: { eligible: true, baseSectors: ['Comercial'], sectors: ['Comercial', 'Protocolo'] },
    apiKey: null,
    tokens: null,
    busy: false,
    error: '',
    today: TODAY,
    guideHref: '/lexgroup/documentacao/api-publica',
    onRequest: noop,
    onIssueTokens: noop,
    onHideTokens: noop,
    onRevoke: noop,
    ...over,
})
const render = (over: Partial<ApiKeyViewProps>) => renderToStaticMarkup(<ApiKeyView {...props(over)} />)

describe('ApiKeyView', () => {
    it('sem chave: mostra o setor base e o botão de pedir', () => {
        const html = render({})
        expect(html).toContain('Comercial')
        expect(html).toContain('Pedir chave de API')
        expect(html).not.toContain('não tem setor cadastrado')
    })
    it('sem setor: avisa', () => {
        const html = render({ eligibility: { eligible: true, baseSectors: [], sectors: ['Protocolo'] } })
        expect(html).toContain('não tem setor cadastrado')
    })
    it('pendente: aguardando aprovação', () => {
        expect(render({ apiKey: { ...KEY, status: 'pending' } })).toContain('Aguardando aprovação')
    })
    it('ativa: setores com validade e botão de gerar tokens', () => {
        const html = render({ apiKey: KEY })
        expect(html).toContain('Gerar tokens')
        expect(html).toContain('Protocolo')
        expect(html).toContain('31/01/2027')
        expect(html).not.toContain('lxr_')
    })
    it('tokens gerados aparecem uma vez com o aviso', () => {
        const html = render({
            apiKey: KEY,
            tokens: {
                accessToken: 'eyJ.abc',
                accessExpiresAt: '2026-12-03T12:00:00Z',
                refreshToken: 'lxr_xyz',
                refreshExpiresAt: '2026-12-26T12:00:00Z',
            },
        })
        expect(html).toContain('lxr_xyz')
        expect(html).toContain('eyJ.abc')
        expect(html).toContain('Guarde agora')
    })
    it('recusada: mostra o motivo e deixa pedir de novo', () => {
        const html = render({ apiKey: { ...KEY, status: 'rejected', decisionNote: 'Use o Power BI do setor' } })
        expect(html).toContain('Use o Power BI do setor')
        expect(html).toContain('Pedir de novo')
    })
})
