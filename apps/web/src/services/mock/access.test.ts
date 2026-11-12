import { describe, expect, it } from 'vitest'
import { createAccessStore } from './access.ts'
import { createMembersStore } from './members.ts'
import { DataError } from '../errors.ts'

const self = 'ana@lexgroup.com.br'
const setup = () => {
    const members = createMembersStore({ name: 'Ana Ribeiro', email: self })
    return { members, access: createAccessStore(members) }
}

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
            { units: [{ code: 'NG', role: 'leitor' }], teams: ['t-pendencias'], org_role: null },
            self,
        )
        const after = members.list().members.find((m) => m.id === carla.id)!
        expect(after.units).toEqual([{ code: 'NG', role: 'leitor' }])
        expect(after.teams).toEqual(['Pendências'])
    })

    it('equipe de unidade sem cargo é recusada', () => {
        const { members, access } = setup()
        const carla = members.list().members.find((m) => m.email.startsWith('carla'))!
        expect(() => access.update(carla.id, { units: [], teams: ['t-pendencias'], org_role: null }, self)).toThrow(
            new DataError(409, 'Equipe sem cargo na unidade.'),
        )
    })

    it('ninguém muda o próprio papel', () => {
        const { members, access } = setup()
        const ana = members.list().members.find((m) => m.email === self)!
        expect(() => access.update(ana.id, { units: [], teams: [], org_role: 'member' }, self)).toThrow(
            new DataError(409, 'Você não pode mudar o seu próprio papel.'),
        )
    })
})
