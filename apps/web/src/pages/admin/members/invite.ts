import type { RoleKey, Team, Unit } from '../../../types/index.ts'
import { ROLE_LABEL } from './memberView.ts'

// Regras do convite (sem React): quem usa é o InvitePanel; os testes ficam em invite.test.ts.

// Papéis que dá para convidar (owner fica de fora), na ordem do protótipo.
export const INVITE_ROLES: Exclude<RoleKey, 'owner'>[] = ['colaborador', 'gestor', 'leitor', 'admin']

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
export function validateInvite(emailsText: string, unitCodes: string[]): { emails: string[] } | { error: string } {
    const { valid, invalid } = parseEmails(emailsText)
    if (invalid.length) return { error: `E-mail inválido: ${invalid.join(', ')}` }
    if (valid.length === 0) return { error: 'Digite ao menos um e-mail.' }
    if (unitCodes.length === 0) return { error: 'Escolha ao menos uma unidade.' }
    return { emails: valid }
}

// A frase do quadro cinza: o que a pessoa vai ver ao entrar.
export function invitePreview(role: RoleKey, unitCodes: string[], team: Team | undefined, units: Unit[]): string {
    if (unitCodes.length === 0) return 'Escolha ao menos uma unidade. Sem unidade, a pessoa não vê nenhum dashboard.'
    const names = units
        .filter((u) => unitCodes.includes(u.code))
        .map((u) => u.name)
        .join(', ')
    return `Vão ver ${team?.dashboards ?? 0} dashboards da equipe ${team?.name ?? ''} em ${names}, com o papel ${ROLE_LABEL[role]}.`
}
