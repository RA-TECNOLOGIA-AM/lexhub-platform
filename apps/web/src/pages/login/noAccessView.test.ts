import { describe, expect, it } from 'vitest'
import { requestDate, stepOf, validateRequest } from './noAccessView.ts'
import type { AccessRequest } from '../../types/index.ts'

const req = (status: AccessRequest['status']): AccessRequest => ({
    id: 'r1',
    email: 'a@b.com',
    full_name: 'A',
    office: 'Escritório',
    message: null,
    status,
    created_at: '2026-11-12T03:30:00Z',
    decided_at: null,
    decision_note: null,
    result_org_id: null,
})

describe('stepOf', () => {
    it('sem pedido = formulário; pendente ou aprovado = pendente; recusado = recusado', () => {
        expect(stepOf(null)).toBe('form')
        expect(stepOf(req('pending'))).toBe('pending')
        expect(stepOf(req('approved'))).toBe('pending')
        expect(stepOf(req('rejected'))).toBe('rejected')
    })
})

describe('validateRequest', () => {
    it('escritório obrigatório e limites do banco', () => {
        expect(validateRequest(' x ', '')).toBe('Informe o escritório ou a empresa.')
        expect(validateRequest('a'.repeat(121), '')).toContain('120')
        expect(validateRequest('Escritório', 'm'.repeat(501))).toContain('500')
        expect(validateRequest('Escritório', '')).toBeNull()
    })
})

describe('requestDate', () => {
    it('data no horário de Manaus', () => {
        expect(requestDate('2026-11-12T03:30:00Z')).toBe('11/11/2026') // 23:30 do dia 11 em Manaus
    })
})
