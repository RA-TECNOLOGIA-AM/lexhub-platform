import { describe, expect, it } from 'vitest'
import { invitePreview, parseEmails, validateInvite } from './invite.ts'

const units = [
    { code: 'NG', name: 'Nicolas Gomes' },
    { code: 'LA_AM', name: 'Luis Albert AM' },
]

describe('parseEmails', () => {
    it('aceita vírgula, ponto e vírgula e quebra de linha, sem repetir', () => {
        expect(parseEmails('A@x.com, b@x.com\nb@x.com; c@x.com').valid).toEqual(['a@x.com', 'b@x.com', 'c@x.com'])
    })
    it('separa os inválidos', () => {
        expect(parseEmails('ok@x.com, sem-arroba, x@y').invalid).toEqual(['sem-arroba', 'x@y'])
    })
})

describe('validateInvite', () => {
    it('tudo certo devolve os e-mails', () => {
        expect(validateInvite('a@x.com', ['NG'])).toEqual({ emails: ['a@x.com'] })
    })
    it('e-mail inválido vem antes dos outros avisos', () => {
        expect(validateInvite('a@x.com, ruim', [])).toEqual({ error: 'E-mail inválido: ruim' })
    })
    it('sem e-mail', () => {
        expect(validateInvite('  ', ['NG'])).toEqual({ error: 'Digite ao menos um e-mail.' })
    })
    it('sem unidade', () => {
        expect(validateInvite('a@x.com', [])).toEqual({ error: 'Escolha ao menos uma unidade.' })
    })
})

describe('invitePreview', () => {
    it('frase do protótipo', () => {
        expect(invitePreview('colaborador', ['NG'], { name: 'Protocolo', dashboards: 4 }, units)).toBe(
            'Vão ver 4 dashboards da equipe Protocolo em Nicolas Gomes, com o papel Colaborador.',
        )
    })
    it('sem unidade avisa', () => {
        expect(invitePreview('leitor', [], { name: 'Protocolo', dashboards: 4 }, units)).toMatch(
            /^Escolha ao menos uma unidade/,
        )
    })
})
