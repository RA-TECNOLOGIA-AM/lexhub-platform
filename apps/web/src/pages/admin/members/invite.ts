import type { Invitation, MemberTeam } from '../../../types/index.ts'

// Regras do convite (sem React): quem usa é o InvitePanel; os testes ficam em invite.test.ts.

type InviteRole = Invitation['role']

// Cargos que dá para convidar. Desenvolvedor só para quem tem members.manage (can_invite_admin).
export function inviteRolesFor(canInviteAdmin: boolean): InviteRole[] {
    const roles: InviteRole[] = ['colaborador', 'leitor', 'gestor', 'controller']
    return canInviteAdmin ? [...roles, 'admin'] : roles
}

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

// "a@x.com, b@x.com" ou um por linha -> válidos (sem repetir, minúsculos) e inválidos.
export function parseEmails(text: string): { valid: string[]; invalid: string[] } {
    const items = text
        .split(/[\s,;]+/)
        .map((e) => e.trim().toLowerCase())
        .filter(Boolean)
    const unique = [...new Set(items)]
    return { valid: unique.filter((e) => EMAIL.test(e)), invalid: unique.filter((e) => !EMAIL.test(e)) }
}

// O que falta para o convite poder ser enviado: { emails } se está tudo certo, ou { error }.
// Desenvolvedor vale na organização inteira; os outros cargos precisam de ao menos uma unidade.
export function validateInvite(
    emailsText: string,
    role: InviteRole,
    unitCodes: string[],
): { emails: string[] } | { error: string } {
    const { valid, invalid } = parseEmails(emailsText)
    if (invalid.length) return { error: `E-mail inválido: ${invalid.join(', ')}` }
    if (valid.length === 0) return { error: 'Digite ao menos um e-mail.' }
    if (role !== 'admin' && unitCodes.length === 0) return { error: 'Escolha ao menos uma unidade.' }
    return { emails: valid }
}

// Só as equipes das unidades escolhidas (cada equipe é de uma unidade).
export const teamsFor = (teams: MemberTeam[], unitCodes: string[]) => teams.filter((t) => unitCodes.includes(t.unit))

// O link que quem convida manda para a pessoa: a tela de login do app.
export const inviteLink = (origin: string) => `${origin.replace(/\/+$/, '')}/login`
