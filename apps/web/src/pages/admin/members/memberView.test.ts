import { describe, expect, it } from 'vitest'
import { members } from '../../../services/mock/members.ts'
import type { Invitation } from '../../../types/index.ts'
import {
    activeCount,
    filterFromParams,
    filterRows,
    noteOf,
    paramsFromFilter,
    roleOf,
    rowsOf,
    scopeOf,
    statusOf,
    sectorsText,
    storedMembersLayout,
    storeMembersLayout,
    MEMBERS_LAYOUT_KEY,
    lastSeenText,
    isOnline,
    unitsText,
    unitViewOf,
    firstUnitOf,
    hasUnitAccess,
    type MemberRow,
} from './memberView.ts'

const rows = rowsOf(members)
const emailOf = (row: MemberRow) => (row.kind === 'member' ? row.member.email : row.invitation.email)
const names = (list: MemberRow[]) => list.map((r) => emailOf(r).split('@')[0])
const row = (name: string) => rows.find((r) => emailOf(r).startsWith(name))!
const none = { q: '', unit: '', role: '' as const, status: '' as const }

describe('rowsOf', () => {
    it('membros na ordem do servidor e depois os convites pendentes', () => {
        expect(names(rows)).toEqual(['ana', 'bruno', 'carla', 'diego', 'fernanda', 'gabriel'])
        expect(rows.at(-1)?.kind).toBe('invitation')
    })
})

describe('roleOf', () => {
    it('Desenvolvedor pelo papel na organização, em qualquer unidade', () => {
        expect(roleOf(row('ana'), 'NG')).toEqual({ label: 'Desenvolvedor', badge: 'badge pro' })
    })
    it('com unidade escolhida: o cargo nela', () => {
        expect(roleOf(row('bruno'), 'LA_AM').label).toBe('Controller')
        expect(roleOf(row('carla'), 'NG').label).toBe('Sem cargo aqui')
    })
    it('todas as unidades: o maior cargo e +N', () => {
        expect(roleOf(row('bruno'), null).label).toBe('Gestor +1')
        expect(roleOf(row('carla'), null).label).toBe('Colaborador')
    })
    it('convite: o papel do convite', () => {
        expect(roleOf(row('gabriel'), null).label).toBe('Colaborador')
    })
})

describe('scopeOf e statusOf', () => {
    it('unidades e equipes', () => {
        expect(scopeOf(row('bruno'))).toBe('LA AM, NG · Comercial')
        expect(scopeOf(row('ana'))).toBe('Todas as unidades · Diretoria')
        expect(scopeOf(row('gabriel'))).toBe('NG · Pendências')
    })
    it('situação', () => {
        expect(statusOf(row('fernanda'))).toEqual({ label: 'Desativado', badge: 'badge neutral' })
        expect(statusOf(row('gabriel'))).toEqual({ label: 'Convite pendente', badge: 'badge warn' })
        expect(statusOf(row('ana'))).toEqual({ label: 'Ativo', badge: 'badge ok' })
    })
})

describe('noteOf', () => {
    const now = new Date('2026-11-12T12:00:00Z')
    const inv = (expires_at: string): MemberRow => ({
        kind: 'invitation',
        invitation: {
            ...(row('gabriel') as { invitation: Invitation }).invitation,
            invited_by: 'Ana Ribeiro',
            expires_at,
        },
    })
    it('convite: quem convidou e quando vence', () => {
        expect(noteOf(inv('2026-11-17T12:00:00Z'), now)).toBe('Convidado por Ana Ribeiro · vence em 5 dias')
        expect(noteOf(inv('2026-11-12T15:00:00Z'), now)).toBe('Convidado por Ana Ribeiro · vence hoje')
    })
    it('convite recém-criado (vence em 7 dias menos alguns minutos) mostra 7 dias, não 6', () => {
        expect(noteOf(inv('2026-11-19T11:58:00Z'), now)).toBe('Convidado por Ana Ribeiro · vence em 7 dias')
    })
    it('membro: o e-mail', () => {
        expect(noteOf(row('carla'), now)).toBe('carla@lexgroup.com.br')
    })
})

describe('filterRows', () => {
    it('sem filtro mostra todos', () => {
        expect(filterRows(rows, none)).toHaveLength(6)
    })
    it('busca por nome ou e-mail, inclusive nos convites', () => {
        expect(names(filterRows(rows, { ...none, q: 'ANA' }))).toEqual(['ana'])
        expect(names(filterRows(rows, { ...none, q: 'gabriel@' }))).toEqual(['gabriel'])
        expect(names(filterRows(rows, { ...none, q: 'fernánda' }))).toEqual(['fernanda'])
    })
    it('unidade: Owner/Desenvolvedor aparecem em todas', () => {
        expect(names(filterRows(rows, { ...none, unit: 'LA_RJ' }))).toEqual(['ana', 'carla'])
    })
    it('papel casa com o cargo em qualquer unidade, ou na unidade filtrada', () => {
        expect(names(filterRows(rows, { ...none, role: 'controller' }))).toEqual(['bruno'])
        expect(names(filterRows(rows, { ...none, unit: 'NG', role: 'controller' }))).toEqual([])
        expect(names(filterRows(rows, { ...none, unit: 'NG', role: 'colaborador' }))).toEqual(['diego', 'gabriel'])
        expect(names(filterRows(rows, { ...none, role: 'admin' }))).toEqual(['ana'])
    })
})

describe('activeCount', () => {
    it('conta só os membros ativos', () => {
        expect(activeCount(members)).toBe(4)
    })
})

describe('filtro na URL', () => {
    it('vai e volta', () => {
        const f = { q: 'ana', unit: 'NG', role: 'controller' as const, status: 'disabled' as const }
        expect(filterFromParams(paramsFromFilter(f))).toEqual(f)
        expect(paramsFromFilter(f).toString()).toBe('busca=ana&unidade=NG&papel=controller&situacao=disabled')
    })
    it('campos vazios não vão para a URL', () => {
        expect(paramsFromFilter(none).toString()).toBe('')
    })
    it('papel inválido na URL vira "todos"', () => {
        expect(filterFromParams(new URLSearchParams('papel=chefe')).role).toBe('')
        expect(filterFromParams(new URLSearchParams('situacao=sumido')).status).toBe('')
    })
})

describe('situação e busca por setor', () => {
    it('situação filtra membros ativos, desativados e convites', () => {
        expect(names(filterRows(rows, { ...none, status: 'invited' }))).toEqual(['gabriel'])
        expect(names(filterRows(rows, { ...none, status: 'disabled' }))).toEqual(['fernanda'])
    })
    it('a busca acha pelo setor', () => {
        expect(names(filterRows(rows, { ...none, q: 'protocolo' }))).toEqual(['carla'])
    })
})

describe('colunas da lista', () => {
    it('unidades pelo nome, em maiúsculas; Owner/Dev = TODAS', () => {
        expect(unitsText(row('bruno'), members.units)).toBe('LUIS ALBERT AM, NICOLAS GOMES')
        expect(unitsText(row('ana'), members.units)).toBe('TODAS')
        expect(unitsText(row('gabriel'), members.units)).toBe('NICOLAS GOMES')
    })
    it('setores e último acesso', () => {
        expect(sectorsText(row('bruno'))).toBe('Comercial')
        const now = new Date()
        expect(lastSeenText(row('gabriel'), now)).toBe('Nunca acessou')
        const never = { kind: 'member' as const, member: { ...members.members[0], last_seen_at: null } }
        expect(lastSeenText(never, now)).toBe('Nunca acessou')
    })

    describe('presença', () => {
        const now = new Date('2026-11-24T15:00:00Z')
        const seen = (msAgo: number, status: 'active' | 'disabled' = 'active') => ({
            kind: 'member' as const,
            member: { ...members.members[0], status, last_seen_at: new Date(now.getTime() - msAgo).toISOString() },
        })
        const MIN = 60_000
        it('online até 3 min sem aviso', () => {
            expect(isOnline(seen(2 * MIN), now)).toBe(true)
            expect(lastSeenText(seen(2 * MIN), now)).toBe('Online agora')
            expect(isOnline(seen(3 * MIN), now)).toBe(false)
            expect(isOnline(seen(MIN, 'disabled'), now)).toBe(false)
            expect(isOnline(row('gabriel'), now)).toBe(false)
        })
        it('há quanto tempo', () => {
            expect(lastSeenText(seen(12 * MIN), now)).toBe('Visto há 12 min')
            expect(lastSeenText(seen(3 * 60 * MIN), now)).toBe('Visto há 3 h')
            expect(lastSeenText(seen(26 * 60 * MIN), now)).toBe('Visto há 1 dia')
            expect(lastSeenText(seen(5 * 24 * 60 * MIN), now)).toBe('Visto há 5 dias')
            expect(lastSeenText(seen(40 * 24 * 60 * MIN), now)).toMatch(/^Visto em \d{2}\/\d{2}\/\d{4}$/)
        })
    })
})

describe('unitViewOf', () => {
    const teams = members.teams
    it('cargo e setores só da unidade pedida', () => {
        expect(unitViewOf(row('bruno'), 'LA_AM', teams)).toEqual({
            role: 'Controller',
            sectors: ['Comercial'],
            extraGroups: 0,
            extraDashboards: 0,
        })
        const ng = unitViewOf(row('bruno'), 'LA_RJ', teams)
        expect(ng.role).toBeNull()
        expect(hasUnitAccess(ng)).toBe(false)
    })
    it('convite: cargo e setores pelo nome, nas unidades do convite', () => {
        expect(unitViewOf(row('gabriel'), 'NG', teams)).toMatchObject({ role: 'Colaborador', sectors: ['Pendências'] })
        expect(unitViewOf(row('gabriel'), 'LA_AM', teams).role).toBeNull()
    })
    it('primeira unidade com algo; senão a primeira', () => {
        const codes = members.units.map((u) => u.code)
        expect(firstUnitOf(row('carla'), codes, teams)).toBe('LA_RJ')
        expect(firstUnitOf(row('gabriel'), codes, teams)).toBe('NG')
        expect(firstUnitOf(row('gabriel'), [], teams)).toBe('')
    })
})

describe('pílulas ou cards', () => {
    it('lembra a escolha; sem escolha, valor estranho ou storage quebrado: cards', () => {
        const box = new Map<string, string>()
        const storage = {
            getItem: (k: string) => box.get(k) ?? null,
            setItem: (k: string, v: string) => void box.set(k, v),
        }
        expect(storedMembersLayout(storage)).toBe('cards')
        storeMembersLayout('pilulas', storage)
        expect(box.get(MEMBERS_LAYOUT_KEY)).toBe('pilulas')
        expect(storedMembersLayout(storage)).toBe('pilulas')
        box.set(MEMBERS_LAYOUT_KEY, 'tabela')
        expect(storedMembersLayout(storage)).toBe('cards')
        const broken = {
            getItem: (): string | null => {
                throw new Error('bloqueado')
            },
        }
        expect(storedMembersLayout(broken)).toBe('cards')
    })
})
