import { describe, expect, it } from 'vitest'
import { createAccessStore } from '../../../services/mock/access.ts'
import { createMembersStore } from '../../../services/mock/members.ts'
import type { Member } from '../../../types/index.ts'
import {
    draftFromMember,
    gridCell,
    isDirty,
    previewDashboards,
    previewText,
    readOnlyReason,
    setUnitRole,
    toggleTeam,
    toUpdate,
    type AccessDraft,
} from './accessEditor.ts'

const members = createMembersStore({ name: 'Ana Ribeiro', email: 'ana@lexgroup.com.br' })
const overview = createAccessStore(members).overview('NG')
const person = (name: string): Member => members.list().members.find((m) => m.email.startsWith(name))!
const blank: AccessDraft = { orgRole: 'member', units: { LA_AM: '', LA_RJ: '', NG: '' }, teams: [] }

describe('draftFromMember', () => {
    it('um cargo por unidade gerida ("" = sem cargo) e as equipes por id', () => {
        expect(draftFromMember(person('bruno'), overview)).toEqual({
            orgRole: 'member',
            units: { LA_AM: 'controller', LA_RJ: '', NG: 'gestor' },
            teams: ['t-comercial'],
        })
    })
})

describe('setUnitRole e toggleTeam', () => {
    it('tirar o cargo de uma unidade tira as equipes dela junto', () => {
        const withTeam = toggleTeam(setUnitRole(blank, 'NG', 'colaborador', overview.teams), 't-pendencias')
        expect(withTeam.teams).toEqual(['t-pendencias'])
        expect(setUnitRole(withTeam, 'NG', '', overview.teams).teams).toEqual([])
    })
    it('trocar o cargo mantém as equipes', () => {
        const withTeam = toggleTeam(setUnitRole(blank, 'NG', 'colaborador', overview.teams), 't-pendencias')
        expect(setUnitRole(withTeam, 'NG', 'leitor', overview.teams).teams).toEqual(['t-pendencias'])
    })
})

describe('previewDashboards (mesma regra de app_private.dashboard_scope)', () => {
    it('Gestor e Controller veem todos os dashboards da unidade', () => {
        const draft = setUnitRole(blank, 'NG', 'controller', overview.teams)
        const [ng] = previewDashboards(overview, draft)
        expect(ng).toMatchObject({ unit: 'NG', all: true })
        expect(ng.titles).toHaveLength(overview.dashboards_by_unit.NG.length)
    })
    it('Colaborador vê só o que as equipes dele naquela unidade liberam', () => {
        const draft = toggleTeam(setUnitRole(blank, 'NG', 'colaborador', overview.teams), 't-pendencias')
        expect(previewDashboards(overview, draft)).toMatchObject([
            { unit: 'NG', all: false, titles: ['Pendências', 'Pendências (LexPre)'] },
        ])
    })
    it('equipe de outra unidade não libera nada aqui', () => {
        const draft = toggleTeam(
            setUnitRole(setUnitRole(blank, 'NG', 'leitor', overview.teams), 'LA_RJ', 'leitor', overview.teams),
            't-protocolo',
        )
        const ng = previewDashboards(overview, draft).find((p) => p.unit === 'NG')
        expect(ng).toMatchObject({ unit: 'NG', all: false, titles: [] })
    })
    it('Desenvolvedor vê tudo em todas as unidades', () => {
        const preview = previewDashboards(overview, { ...blank, orgRole: 'admin' })
        expect(preview.map((p) => p.unit)).toEqual(['LA_AM', 'LA_RJ', 'NG'])
        expect(preview.every((p) => p.all)).toBe(true)
    })
    it('unidade sem cargo não aparece', () => {
        expect(previewDashboards(overview, blank)).toEqual([])
    })
})

describe('toUpdate e isDirty', () => {
    it('só manda unidades com cargo; papel na org só se mudou', () => {
        const original = draftFromMember(person('bruno'), overview)
        const draft = setUnitRole(original, 'LA_AM', '', overview.teams)
        expect(isDirty(original, draft)).toBe(true)
        expect(toUpdate(draft, original, true)).toEqual({
            units: [{ code: 'NG', role: 'gestor' }],
            teams: [],
            org_role: null,
        })
    })
    it('virar Desenvolvedor manda org_role; sem permissão, nunca manda', () => {
        const original = draftFromMember(person('carla'), overview)
        const draft = { ...original, orgRole: 'admin' as const }
        expect(toUpdate(draft, original, true).org_role).toBe('admin')
        expect(toUpdate(draft, original, false).org_role).toBeNull()
    })
    it('sem mudança não está sujo', () => {
        const original = draftFromMember(person('carla'), overview)
        expect(isDirty(original, { ...original, teams: [...original.teams] })).toBe(false)
    })
})

describe('gridCell', () => {
    it('Gestor/Controller: vê; Colaborador/Leitor: as equipes que liberam, ou nenhuma', () => {
        expect(gridCell(overview, 'pendencias', 'gestor')).toEqual({ kind: 'all' })
        expect(gridCell(overview, 'pendencias', 'leitor')).toEqual({
            kind: 'teams',
            teams: ['Diretoria', 'Pendências'],
        })
        const laAm = createAccessStore(members).overview('LA_AM')
        expect(gridCell(laAm, 'execucao', 'colaborador')).toEqual({ kind: 'none' })
    })
})

describe('previewText', () => {
    it('unidade sem dashboard ligado não diz "todos os 0"', () => {
        expect(previewText({ unit: 'MT', all: true, titles: [], total: 0 })).toBe(
            'nenhum dashboard ligado nesta unidade',
        )
        expect(previewText({ unit: 'MT', all: false, titles: [], total: 0 })).toBe(
            'nenhum dashboard ligado nesta unidade',
        )
    })
    it('vê tudo, uma parte ou nada', () => {
        expect(previewText({ unit: 'NG', all: true, titles: ['A', 'B'], total: 2 })).toBe('todos os 2 dashboards')
        expect(previewText({ unit: 'NG', all: false, titles: ['A'], total: 2 })).toBe('1 de 2: A')
        expect(previewText({ unit: 'NG', all: false, titles: [], total: 2 })).toBe(
            'nenhum — marque uma equipe que libere dashboards',
        )
    })
})

describe('readOnlyReason', () => {
    const all = members.list().members
    const admin = all.find((m) => m.org_role === 'admin' || m.org_role === 'owner')!
    const plain = all.find((m) => m.org_role === 'member')!
    const asGestor = { ...overview, can_set_org_role: false }
    const asDev = { ...overview, can_set_org_role: true }

    it('Gestor edita outra pessoa comum', () => {
        expect(readOnlyReason(plain, asGestor, false)).toBeNull()
    })
    it('Gestor não edita o próprio acesso', () => {
        expect(readOnlyReason(plain, asGestor, true)).toMatch(/próprio acesso/)
    })
    it('Gestor não edita Owner/Desenvolvedor', () => {
        expect(readOnlyReason(admin, asGestor, false)).toMatch(/Owner e Desenvolvedor/)
    })
    it('Owner/Desenvolvedor editam todos, inclusive a si', () => {
        expect(readOnlyReason(admin, asDev, true)).toBeNull()
        expect(readOnlyReason(plain, asDev, false)).toBeNull()
    })
})
