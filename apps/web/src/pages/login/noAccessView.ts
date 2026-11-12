import type { AccessRequest } from '../../types/index.ts'

// Módulo: as regras do card "sem acesso", sem React (testadas em noAccessView.test.ts).

export type NoAccessStep = 'form' | 'pending' | 'rejected'

// O que o card mostra a partir do último pedido. Aprovado e ainda "sem acesso" (o /me não atualizou): pendente,
// para o "Verificar de novo" resolver.
export function stepOf(request: AccessRequest | null): NoAccessStep {
    if (!request) return 'form'
    if (request.status === 'rejected') return 'rejected'
    return 'pending'
}

export const OFFICE_MAX = 120
export const MESSAGE_MAX = 500

// Mesmos limites do banco. Devolve a mensagem de erro, ou null quando está tudo certo.
export function validateRequest(office: string, message: string): string | null {
    const trimmed = office.trim()
    if (trimmed.length < 2) return 'Informe o escritório ou a empresa.'
    if (trimmed.length > OFFICE_MAX) return `O escritório pode ter até ${OFFICE_MAX} caracteres.`
    if (message.length > MESSAGE_MAX) return `A mensagem pode ter até ${MESSAGE_MAX} caracteres.`
    return null
}

// "12/11/2026" no horário de Manaus (o fuso padrão das unidades).
export function requestDate(iso: string): string {
    return new Date(iso).toLocaleDateString('pt-BR', { timeZone: 'America/Manaus' })
}
