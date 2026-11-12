import { DataError } from '../errors.ts'
import type { AccessRequest, ApprovalOrg, ApprovalTarget } from '../../types/index.ts'

// Organizações que a equipe RA vê ao aprovar (as mesmas do mock de users.ts, com ids fictícios).
export const approvalOrgs: ApprovalOrg[] = [
    {
        id: 'org-lexgroup',
        slug: 'lexgroup',
        name: 'LexGroup',
        units: [
            { id: 'unit-ng', code: 'NG', name: 'Nicolas Gomes' },
            { id: 'unit-la', code: 'LA', name: 'LAAM' },
            { id: 'unit-rj', code: 'RJ', name: 'LARJ' },
        ],
    },
    {
        id: 'org-parceiro',
        slug: 'cliente-parceiro',
        name: 'Cliente parceiro',
        units: [{ id: 'unit-cp', code: 'CP', name: 'Parceiro · sede' }],
    },
]

// Um pedido pendente de exemplo, para a página da equipe RA não abrir vazia.
const seed = (): AccessRequest[] => [
    {
        id: 'req-exemplo',
        email: 'fulano@escritorioexemplo.com.br',
        full_name: 'Fulano de Tal',
        office: 'Escritório Exemplo Advocacia',
        message: 'Sou do financeiro e preciso ver os dashboards da sede.',
        status: 'pending',
        created_at: '2026-11-12T13:20:00Z',
        decided_at: null,
        decision_note: null,
        result_org_id: null,
    },
]

type Who = { email: string; name: string; staff: boolean; hasAccess: boolean }

// Módulo: os pedidos de acesso do mock, em memória (voltam ao exemplo no F5), com as mesmas regras do banco.
// Parâmetros: o relógio (trocável nos testes). Cada chamada recebe quem está logado (Who).
// Devolve também `approved(email)`: o mock do /me usa para liberar quem foi aprovado.
export function createAccessRequestsStore(now: () => Date = () => new Date()) {
    let requests = seed()
    const approvedEmails = new Set<string>()
    let nextId = 1

    const requireStaff = (who: Who) => {
        if (!who.staff) throw new DataError(403, 'Só a equipe RA Tecnologia pode fazer isso.')
    }
    const pendingOf = (id: string) => {
        const found = requests.find((r) => r.id === id)
        if (!found) throw new DataError(409, 'Pedido não encontrado.')
        if (found.status !== 'pending') throw new DataError(409, 'Este pedido já foi decidido.')
        return found
    }
    const decide = (id: string, patch: Partial<AccessRequest>) => {
        requests = requests.map((r) => (r.id === id ? { ...r, ...patch, decided_at: now().toISOString() } : r))
        return structuredClone(requests.find((r) => r.id === id)!)
    }

    return {
        approved: (email: string) => approvedEmails.has(email),

        request(who: Who, office: string, message: string | null): AccessRequest {
            if (who.hasAccess || approvedEmails.has(who.email))
                throw new DataError(409, 'Você já tem acesso ao LexHub.')
            if (requests.some((r) => r.email === who.email && r.status === 'pending')) {
                throw new DataError(409, 'Você já tem um pedido aguardando aprovação.')
            }
            const trimmed = office.trim()
            if (trimmed.length < 2 || trimmed.length > 120) {
                throw new DataError(409, 'Informe o escritório ou a empresa (2 a 120 caracteres).')
            }
            const created: AccessRequest = {
                id: `req-${nextId++}`,
                email: who.email,
                full_name: who.name,
                office: trimmed,
                message: message?.trim() || null,
                status: 'pending',
                created_at: now().toISOString(),
                decided_at: null,
                decision_note: null,
                result_org_id: null,
            }
            requests = [created, ...requests]
            return structuredClone(created)
        },

        mine(who: Who): AccessRequest | null {
            const own = requests.filter((r) => r.email === who.email)
            own.sort((a, b) => b.created_at.localeCompare(a.created_at))
            return own[0] ? structuredClone(own[0]) : null
        },

        count(who: Who): number {
            requireStaff(who)
            return requests.filter((r) => r.status === 'pending').length
        },

        list(who: Who, status: 'pending' | 'decided'): AccessRequest[] {
            requireStaff(who)
            return structuredClone(
                requests
                    .filter((r) => (status === 'pending' ? r.status === 'pending' : r.status !== 'pending'))
                    .sort((a, b) => b.created_at.localeCompare(a.created_at)),
            )
        },

        options(who: Who): ApprovalOrg[] {
            requireStaff(who)
            return structuredClone(approvalOrgs)
        },

        approve(who: Who, id: string, target: ApprovalTarget): AccessRequest {
            requireStaff(who)
            const req = pendingOf(id)
            if (target.kind === 'existing' && target.org_role === 'member' && target.units.length === 0) {
                throw new DataError(409, 'Escolha pelo menos uma unidade.')
            }
            approvedEmails.add(req.email)
            const orgId = target.kind === 'existing' ? target.org_id : `org-${target.slug}`
            return decide(id, { status: 'approved', result_org_id: orgId })
        },

        reject(who: Who, id: string, note: string | null): AccessRequest {
            requireStaff(who)
            pendingOf(id)
            return decide(id, { status: 'rejected', decision_note: note?.trim() || null })
        },
    }
}
