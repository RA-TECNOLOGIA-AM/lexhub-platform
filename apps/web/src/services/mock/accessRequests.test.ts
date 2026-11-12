import { describe, expect, it } from 'vitest'
import { createAccessRequestsStore } from './accessRequests.ts'

const novato = { email: 'novo@gmail.com', name: 'Novo', staff: false, hasAccess: false }
const equipe = { email: 'ra@lexgroup.com.br', name: 'RA', staff: true, hasAccess: true }
const clock = () => new Date('2026-11-12T15:00:00Z')

describe('createAccessRequestsStore (mock dos pedidos de acesso)', () => {
    it('pede, não repete enquanto pendente, e aparece para a equipe RA', () => {
        const store = createAccessRequestsStore(clock)
        const req = store.request(novato, '  Escritório Novo ', null)
        expect(req).toMatchObject({ status: 'pending', office: 'Escritório Novo', email: 'novo@gmail.com' })
        expect(() => store.request(novato, 'Outro', null)).toThrow('aguardando aprovação')
        expect(store.mine(novato)?.id).toBe(req.id)
        expect(store.count(equipe)).toBe(2) // o novo + o exemplo
    })

    it('escritório curto e quem já tem acesso são recusados', () => {
        const store = createAccessRequestsStore(clock)
        expect(() => store.request(novato, 'x', null)).toThrow('2 a 120')
        expect(() => store.request(equipe, 'RA', null)).toThrow('já tem acesso')
    })

    it('só a equipe RA lista, aprova e recusa', () => {
        const store = createAccessRequestsStore(clock)
        expect(() => store.count(novato)).toThrow('equipe RA')
        expect(() => store.list(novato, 'pending')).toThrow('equipe RA')
        expect(() => store.reject(novato, 'req-exemplo', null)).toThrow('equipe RA')
    })

    it('aprovar libera o acesso; decidido não se decide de novo', () => {
        const store = createAccessRequestsStore(clock)
        const req = store.request(novato, 'Escritório Novo', 'oi')
        expect(() =>
            store.approve(equipe, req.id, { kind: 'existing', org_id: 'org-lexgroup', org_role: 'member', units: [] }),
        ).toThrow('pelo menos uma unidade')
        const ok = store.approve(equipe, req.id, {
            kind: 'existing',
            org_id: 'org-lexgroup',
            org_role: 'member',
            units: [{ unit_id: 'unit-ng', role_key: 'leitor' }],
        })
        expect(ok).toMatchObject({ status: 'approved', result_org_id: 'org-lexgroup' })
        expect(store.approved('novo@gmail.com')).toBe(true)
        expect(() => store.reject(equipe, req.id, null)).toThrow('já foi decidido')
        expect(store.list(equipe, 'decided').map((r) => r.id)).toEqual([req.id])
    })

    it('recusar guarda a nota e deixa pedir de novo', () => {
        const store = createAccessRequestsStore(clock)
        const req = store.request(novato, 'Escritório Novo', null)
        expect(store.reject(equipe, req.id, ' não identificado ')).toMatchObject({
            status: 'rejected',
            decision_note: 'não identificado',
        })
        expect(store.request(novato, 'Escritório Novo', 'de novo').status).toBe('pending')
    })
})
