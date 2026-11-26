import { DataError } from '../errors.ts'
import type {
    ApiKeyEligibility,
    ApiKeyExtraRequest,
    ApiKeyInfo,
    ApiKeyTokens,
} from '../../types/index.ts'

// Setores do mock (os mesmos nomes da LexGroup) e os setores de quem está logado no mock.
const SECTORS = ['Comercial', 'Protocolo', 'Peticionamento', 'Execução', 'Financeiro']
const BASE = ['Comercial']
const DAY = 86_400_000

type Who = { name: string; email: string }

const isoDay = (d: Date) => d.toISOString().slice(0, 10)

// Um pedido de outra pessoa, para a aba do Desenvolvedor não abrir vazia.
const seed = (now: number): ApiKeyInfo[] => [
    {
        id: 'key-exemplo',
        userName: 'Beatriz Lima',
        userEmail: 'beatriz.lima@lexgroup.com.br',
        status: 'pending',
        note: 'Power BI das metas do Comercial',
        decisionNote: null,
        requestedAt: new Date(now - 2 * 3_600_000).toISOString(),
        decidedAt: null,
        revokedAt: null,
        lastUsedAt: null,
        sectors: [
            { setor: 'Comercial', base: true, status: 'approved', justificativa: null, expiresAt: null },
            {
                setor: 'Financeiro',
                base: false,
                status: 'pending',
                justificativa: 'Cruzar vendas com recebimentos no planejamento',
                expiresAt: new Date(now + 90 * DAY).toISOString(),
            },
        ],
    },
]

// Módulo: chaves de API no modo mock. Em memória (F5 volta ao exemplo). Mesmas regras de
// supabase/migrations/20261126200000_api_publica.sql; no mock, quem está logado pode pedir e aprovar.
export function createMockApiKeys(now: () => number = Date.now) {
    let keys = seed(now())
    let seq = 0

    const find = (id: string) => {
        const key = keys.find((k) => k.id === id)
        if (!key) throw new DataError(409, 'Chave não encontrada.')
        return key
    }
    const mine = (who: Who) => keys.filter((k) => k.userEmail === who.email)

    function validate(extras: ApiKeyExtraRequest[]) {
        const today = isoDay(new Date(now()))
        const max = isoDay(new Date(now() + 365 * DAY))
        if (BASE.length === 0 && extras.length === 0) {
            throw new DataError(409, 'Você não tem setor cadastrado: peça ao menos um setor extra.')
        }
        for (const e of extras) {
            if (!SECTORS.includes(e.setor)) throw new DataError(409, `Setor "${e.setor}" não disponível.`)
            if (BASE.includes(e.setor)) throw new DataError(409, `"${e.setor}" já é um setor seu.`)
            if (e.justificativa.trim().length < 10) {
                throw new DataError(409, 'A justificativa do setor extra precisa de pelo menos 10 caracteres.')
            }
            if (!(e.validade > today && e.validade <= max)) {
                throw new DataError(409, 'A validade do setor extra deve ser entre amanhã e 365 dias.')
            }
        }
    }

    return {
        eligibility(): ApiKeyEligibility {
            return { eligible: true, baseSectors: [...BASE], sectors: [...SECTORS] }
        },
        request(who: Who, note: string | null, extras: ApiKeyExtraRequest[]): string {
            if (mine(who).some((k) => k.status === 'pending' || k.status === 'active')) {
                throw new DataError(409, 'Você já tem uma chave pedida ou ativa nesta organização.')
            }
            validate(extras)
            const id = `key-mock-${++seq}`
            keys = [
                {
                    id,
                    userName: who.name,
                    userEmail: who.email,
                    status: 'pending',
                    note: note?.trim() || null,
                    decisionNote: null,
                    requestedAt: new Date(now()).toISOString(),
                    decidedAt: null,
                    revokedAt: null,
                    lastUsedAt: null,
                    sectors: [
                        ...BASE.map((setor) => ({
                            setor,
                            base: true,
                            status: 'approved' as const,
                            justificativa: null,
                            expiresAt: null,
                        })),
                        ...extras.map((e) => ({
                            setor: e.setor,
                            base: false,
                            status: 'pending' as const,
                            justificativa: e.justificativa.trim(),
                            expiresAt: new Date(`${e.validade}T23:59:59-03:00`).toISOString(),
                        })),
                    ],
                },
                ...keys,
            ]
            return id
        },
        mine(who: Who): ApiKeyInfo | null {
            return mine(who)[0] ?? null
        },
        tokens(who: Who): ApiKeyTokens {
            if (!mine(who).some((k) => k.status === 'active')) {
                throw new DataError(404, 'Você não tem chave de API ativa nesta organização.')
            }
            const rand = () => Math.random().toString(36).slice(2)
            return {
                accessToken: `eyJ.mock.${rand()}${rand()}`,
                accessExpiresAt: new Date(now() + 7 * DAY).toISOString(),
                refreshToken: `lxr_mock_${rand()}${rand()}`,
                refreshExpiresAt: new Date(now() + 30 * DAY).toISOString(),
            }
        },
        list(status: 'pending' | 'active' | 'closed' | 'all'): ApiKeyInfo[] {
            return keys.filter(
                (k) =>
                    status === 'all' ||
                    k.status === status ||
                    (status === 'closed' && (k.status === 'rejected' || k.status === 'revoked')),
            )
        },
        count(): number {
            return keys.filter((k) => k.status === 'pending').length
        },
        decide(id: string, approve: boolean, sectors: string[], note: string | null): ApiKeyInfo {
            const key = find(id)
            if (key.status !== 'pending') throw new DataError(409, 'Este pedido já foi decidido.')
            const at = new Date(now()).toISOString()
            const decided: ApiKeyInfo = {
                ...key,
                status: approve ? 'active' : 'rejected',
                decisionNote: note?.trim() || null,
                decidedAt: at,
                sectors: key.sectors.map((s) =>
                    s.base ? s : { ...s, status: approve && sectors.includes(s.setor) ? 'approved' : 'rejected' },
                ),
            }
            keys = keys.map((k) => (k.id === id ? decided : k))
            return decided
        },
        revoke(id: string) {
            const key = find(id)
            if (key.status !== 'pending' && key.status !== 'active') {
                throw new DataError(409, 'Esta chave já está encerrada.')
            }
            keys = keys.map((k) =>
                k.id === id ? { ...k, status: 'revoked', revokedAt: new Date(now()).toISOString() } : k,
            )
        },
        revokeSector(id: string, sector: string) {
            const key = find(id)
            if (!key.sectors.some((s) => !s.base && s.setor === sector && s.status === 'approved')) {
                throw new DataError(409, 'Setor extra não encontrado nesta chave.')
            }
            keys = keys.map((k) =>
                k.id === id
                    ? {
                          ...k,
                          sectors: k.sectors.map((s) =>
                              !s.base && s.setor === sector ? { ...s, status: 'revoked' } : s,
                          ),
                      }
                    : k,
            )
        },
    }
}
