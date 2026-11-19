import { describe, expect, it } from 'vitest'
import { createAccessStore } from './access.ts'
import { createMembersStore } from './members.ts'
import { DataError } from '../errors.ts'

const self = 'ana@lexgroup.com.br'
const setup = () => {
    const members = createMembersStore({ name: 'Ana Ribeiro', email: self })
    return { members, access: createAccessStore(members) }
}

const noExtras = { extra_groups: [], extra_dashboards: [] }

describe('createAccessStore', () => {
    it('a grade da unidade traz os dashboards ligados nela e as equipes que liberam cada um', () => {
        const { access } = setup()
        const ng = access.overview('NG')
        expect(ng.unit).toBe('NG')
        expect(ng.dashboards.find((d) => d.key === 'pendencias')?.teams).toEqual(['Diretoria', 'Pendências'])
        expect(ng.dashboards_by_unit.LA_RJ).toContain('protocolo-lexpre')
        expect(ng.can_set_org_role).toBe(true)
    })

    it('sem unidade escolhida: a primeira por código', () => {
        expect(setup().access.overview(null).unit).toBe('LA_AM')
    })

    it('salvar muda cargo e equipes, e a lista de Membros enxerga a mudança', () => {
        const { members, access } = setup()
        const carla = members.list().members.find((m) => m.email.startsWith('carla'))!
        access.update(
            carla.id,
            { units: [{ code: 'NG', role: 'leitor' }], teams: ['t-pendencias'], org_role: null, ...noExtras },
            self,
        )
        const after = members.list().members.find((m) => m.id === carla.id)!
        expect(after.units).toEqual([{ code: 'NG', role: 'leitor' }])
        expect(after.teams).toEqual(['Pendências'])
    })

    it('equipe de unidade sem cargo é recusada', () => {
        const { members, access } = setup()
        const carla = members.list().members.find((m) => m.email.startsWith('carla'))!
        expect(() =>
            access.update(carla.id, { units: [], teams: ['t-pendencias'], org_role: null, ...noExtras }, self),
        ).toThrow(new DataError(409, 'Equipe sem cargo na unidade.'))
    })

    it('ninguém muda o próprio papel', () => {
        const { members, access } = setup()
        const ana = members.list().members.find((m) => m.email === self)!
        expect(() => access.update(ana.id, { units: [], teams: [], org_role: 'member', ...noExtras }, self)).toThrow(
            new DataError(409, 'Você não pode mudar o seu próprio papel.'),
        )
    })

    it('exceções: só em unidade com cargo e de grupo/dashboard que existe; salva na pessoa', () => {
        const { members, access } = setup()
        const carla = members.list().members.find((m) => m.email.startsWith('carla'))!
        const ng = [{ code: 'NG', role: 'colaborador' as const }]
        expect(() =>
            access.update(
                carla.id,
                { units: [], teams: [], org_role: null, ...noExtras, extra_groups: [{ unit: 'NG', slug: 'juridico' }] },
                self,
            ),
        ).toThrow(new DataError(409, 'Grupo extra sem cargo na unidade.'))
        expect(() =>
            access.update(
                carla.id,
                { units: ng, teams: [], org_role: null, ...noExtras, extra_groups: [{ unit: 'NG', slug: 'nada' }] },
                self,
            ),
        ).toThrow(new DataError(409, 'Grupo inválido.'))
        expect(() =>
            access.update(
                carla.id,
                {
                    units: ng,
                    teams: [],
                    org_role: null,
                    ...noExtras,
                    extra_dashboards: [{ unit: 'NG', key: 'nao-existe' }],
                },
                self,
            ),
        ).toThrow(new DataError(409, 'Dashboard avulso não existe nesta unidade.'))
        const after = access.update(
            carla.id,
            {
                units: ng,
                teams: [],
                org_role: null,
                extra_groups: [{ unit: 'NG', slug: 'juridico' }],
                extra_dashboards: [{ unit: 'NG', key: 'nps' }],
            },
            self,
        )
        expect(after.extra_groups).toEqual([{ unit: 'NG', slug: 'juridico' }])
        expect(after.extra_dashboards).toEqual([{ unit: 'NG', key: 'nps' }])
    })

    it('grupos do setor aparecem na grade; Diretoria vê tudo', () => {
        const { access } = setup()
        access.setTeamGroups('t-pendencias', ['juridico'], null)
        const ov = access.overview('NG')
        expect(ov.teams.find((t) => t.id === 't-pendencias')).toMatchObject({ groups: ['juridico'], sees_all: false })
        expect(ov.teams.find((t) => t.id === 't-diretoria')).toMatchObject({ sees_all: true })
        const jur = ov.dashboards.find((d) => d.group === 'juridico')!
        expect(jur.teams).toEqual(['Diretoria', 'Pendências'])
        expect(() => access.setTeamGroups('t-pendencias', ['nada'], null)).toThrow(
            new DataError(409, 'Grupo inválido.'),
        )
    })
})
