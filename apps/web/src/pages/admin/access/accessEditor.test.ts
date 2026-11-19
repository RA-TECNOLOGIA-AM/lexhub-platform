import { describe, expect, it } from 'vitest'
import { createAccessStore } from '../../../services/mock/access.ts'
import { createMembersStore } from '../../../services/mock/members.ts'
import type { Member } from '../../../types/index.ts'
import {
    draftFromMember,
    firstUnit,
    gridCell,
    isDirty,
    previewDashboards,
    avulsoOptions,
    personalText,
    previewText,
    readOnlyReason,
    sectorCoverage,
    setAllTeams,
    setUnitRole,
    toggleExtraDashboard,
    toggleExtraGroup,
    toggleTeam,
    toUpdate,
    unitHasAccess,
    type AccessDraft,
} from './accessEditor.ts'

const members = createMembersStore({ name: 'Ana Ribeiro', email: 'ana@lexgroup.com.br' })
const overview = createAccessStore(members).overview('NG')
const person = (name: string): Member => members.list().members.find((m) => m.email.startsWith(name))!
const none = { LA_AM: [], LA_RJ: [], NG: [] }
const blank: AccessDraft = {
    orgRole: 'member',
    units: { LA_AM: '', LA_RJ: '', NG: '' },
    teams: [],
    extraGroups: none,
    extraDashboards: none,
}

describe('draftFromMember', () => {
    it('um cargo por unidade gerida ("" = sem cargo) e as equipes por id', () => {
        expect(draftFromMember(person('bruno'), overview)).toEqual({
            orgRole: 'member',
            units: { LA_AM: 'controller', LA_RJ: '', NG: 'gestor' },
            teams: ['t-comercial'],
            extraGroups: none,
            extraDashboards: none,
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
            extra_groups: [],
            extra_dashboards: [],
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
        expect(previewText({ unit: 'MT', all: true, titles: [], personal: [], total: 0 })).toBe(
            'nenhum dashboard ligado nesta unidade',
        )
        expect(previewText({ unit: 'MT', all: false, titles: [], personal: [], total: 0 })).toBe(
            'nenhum dashboard ligado nesta unidade',
        )
    })
    it('vê tudo, uma parte ou nada', () => {
        expect(previewText({ unit: 'NG', all: true, titles: ['A', 'B'], personal: [], total: 2 })).toBe(
            'todos os 2 dashboards',
        )
        expect(previewText({ unit: 'NG', all: false, titles: ['A'], personal: [], total: 2 })).toBe('1 de 2: A')
        expect(previewText({ unit: 'NG', all: false, titles: [], personal: [], total: 2 })).toBe(
            'nenhum — marque um setor, um grupo extra ou um dashboard avulso',
        )
    })
    it('exceções entram na conta e têm a linha delas', () => {
        const p = { unit: 'NG', all: false, titles: ['A'], personal: ['B'], total: 3 }
        expect(previewText(p)).toBe('2 de 3: A')
        expect(personalText(p)).toBe('só visualiza (exceção): B')
        expect(previewText({ ...p, titles: [] })).toBe('1 de 3')
        expect(personalText({ ...p, personal: [] })).toBe('')
    })
})

describe('4 camadas (mesma regra de app_private.dashboard_access)', () => {
    const store = createAccessStore(members)
    store.setTeamGroups('t-pendencias', ['juridico'], null)
    const ov = store.overview('NG')
    const juridicoNg = ov.dashboards_by_unit.NG.filter((k) => ov.group_of[k] === 'juridico')
    const colab = setUnitRole(blank, 'NG', 'colaborador', ov.teams)

    it('grupo do setor libera a coluna inteira, somada à regra card a card', () => {
        const [ng] = previewDashboards(ov, toggleTeam(colab, 't-pendencias'))
        expect(juridicoNg.length).toBeGreaterThan(0)
        expect(ng.titles).toEqual(
            expect.arrayContaining([...juridicoNg.map((k) => ov.titles[k]), 'Pendências (LexPre)']),
        )
        expect(ng.personal).toEqual([])
    })
    it('setor que vê tudo (Diretoria) vê todos', () => {
        const [ng] = previewDashboards(ov, toggleTeam(colab, 't-diretoria'))
        expect(ng.all).toBe(true)
    })
    it('grupo extra e avulso da pessoa: só visualiza, fora do que o setor já dá', () => {
        const draft = toggleExtraDashboard(toggleExtraGroup(colab, 'NG', 'juridico'), 'NG', 'nps')
        const [ng] = previewDashboards(ov, draft)
        expect(ng.titles).toEqual([])
        expect(ng.personal).toEqual(expect.arrayContaining([...juridicoNg.map((k) => ov.titles[k]), 'NPS']))
        const withSector = previewDashboards(ov, toggleTeam(draft, 't-pendencias'))[0]
        expect(withSector.personal).toEqual(['NPS']) // o Jurídico agora vem do setor
    })
    it('sectorCoverage diz qual setor dá cada grupo', () => {
        const cov = sectorCoverage(ov, toggleTeam(colab, 't-pendencias'), 'NG')
        expect(cov.groups.get('juridico')).toEqual(['Pendências'])
        expect(cov.all).toBe(false)
    })
    it('avulsoOptions esconde o que já está coberto', () => {
        const draft = toggleExtraGroup(toggleTeam(colab, 't-pendencias'), 'NG', 'comercial')
        const { options, covered } = avulsoOptions(ov, draft, 'NG')
        expect(options.some((o) => o.group === 'juridico' || o.group === 'comercial')).toBe(false)
        expect(options.length + covered).toBe(ov.dashboards_by_unit.NG.length)
    })
    it('tirar o cargo limpa as exceções; toUpdate só manda unidade com cargo', () => {
        const draft = toggleExtraDashboard(toggleExtraGroup(colab, 'NG', 'juridico'), 'NG', 'nps')
        expect(toUpdate(draft, blank, false)).toMatchObject({
            extra_groups: [{ unit: 'NG', slug: 'juridico' }],
            extra_dashboards: [{ unit: 'NG', key: 'nps' }],
        })
        const cleared = setUnitRole(draft, 'NG', '', ov.teams)
        expect(cleared.extraGroups.NG).toEqual([])
        expect(cleared.extraDashboards.NG).toEqual([])
        expect(isDirty(draft, cleared)).toBe(true)
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

describe('setAllTeams, firstUnit e unitHasAccess', () => {
    it('marca e limpa só os setores da unidade', () => {
        const draft = toggleTeam(setUnitRole(blank, 'NG', 'colaborador', overview.teams), 't-protocolo')
        const all = setAllTeams(draft, 'NG', overview.teams, true)
        expect(all.teams).toEqual(['t-protocolo', 't-diretoria', 't-pendencias'])
        expect(setAllTeams(all, 'NG', overview.teams, false).teams).toEqual(['t-protocolo'])
    })
    it('abre na primeira unidade com cargo; sem cargo, na primeira', () => {
        expect(firstUnit(setUnitRole(blank, 'NG', 'leitor', overview.teams), ['LA_AM', 'LA_RJ', 'NG'])).toBe('NG')
        expect(firstUnit(blank, ['LA_AM', 'NG'])).toBe('LA_AM')
    })
    it('unidade acesa com cargo ou exceção', () => {
        expect(unitHasAccess(blank, 'NG')).toBe(false)
        expect(unitHasAccess(setUnitRole(blank, 'NG', 'leitor', overview.teams), 'NG')).toBe(true)
        expect(unitHasAccess({ ...blank, extraDashboards: { ...none, NG: ['nps'] } }, 'NG')).toBe(true)
    })
})
