import { describe, expect, it } from 'vitest'
import { members } from '../../../services/mock/members.ts'
import { inviteLink, inviteRolesFor, parseEmails, teamsFor, validateInvite } from './invite.ts'

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
        expect(validateInvite('a@x.com', 'leitor', ['NG'])).toEqual({ emails: ['a@x.com'] })
    })
    it('e-mail inválido vem antes dos outros avisos', () => {
        expect(validateInvite('a@x.com, ruim', 'leitor', [])).toEqual({ error: 'E-mail inválido: ruim' })
    })
    it('sem e-mail', () => {
        expect(validateInvite('  ', 'leitor', ['NG'])).toEqual({ error: 'Digite ao menos um e-mail.' })
    })
    it('cargo de unidade precisa de unidade', () => {
        expect(validateInvite('a@x.com', 'leitor', [])).toEqual({ error: 'Escolha ao menos uma unidade.' })
    })
    it('Desenvolvedor vale na organização inteira: não precisa de unidade', () => {
        expect(validateInvite('a@x.com', 'admin', [])).toEqual({ emails: ['a@x.com'] })
    })
})

describe('inviteRolesFor', () => {
    it('Desenvolvedor só para quem pode convidar Desenvolvedor', () => {
        expect(inviteRolesFor(false)).toEqual(['colaborador', 'leitor', 'gestor', 'controller'])
        expect(inviteRolesFor(true)).toEqual(['colaborador', 'leitor', 'gestor', 'controller', 'admin'])
    })
})

describe('teamsFor', () => {
    it('só as equipes das unidades escolhidas', () => {
        expect(teamsFor(members.teams, ['NG']).map((t) => t.name)).toEqual(['Diretoria', 'Pendências'])
        expect(teamsFor(members.teams, [])).toEqual([])
    })
})

describe('inviteLink', () => {
    it('a tela de login do app (sem barra repetida)', () => {
        expect(inviteLink('https://lexhub.app')).toBe('https://lexhub.app/login')
        expect(inviteLink('https://lexhub.app/')).toBe('https://lexhub.app/login')
    })
})
