import { describe, expect, it } from 'vitest'
import { access } from '../../../services/mock/access.ts'
import { members } from '../../../services/mock/members.ts'
import type { Unit } from '../../../types/index.ts'
import { simulateAccess } from './accessView.ts'

const units: Unit[] = [
    { code: 'NG', name: 'Nicolas Gomes' },
    { code: 'LA_AM', name: 'Luis Albert AM' },
    { code: 'LA_RJ', name: 'Luis Albert RJ' },
]
// Simula pelo primeiro nome do mock de Membros ('carla', 'bruno'...).
const sim = (email: string) => {
    const member = members.members.find((m) => m.email.startsWith(email))!
    return simulateAccess(member, access.rules, access.matrix, units)
}

describe('simulateAccess', () => {
    it('colaborador vê os dashboards da equipe na sua unidade e não exporta', () => {
        expect(sim('carla')).toEqual({
            profile: 'Colaborador · equipe Protocolo · Luis Albert RJ',
            summary: 'Vê 4 dashboards em Luis Albert RJ e não pode exportar.',
            dashboards: ['Protocolo', 'Pendências', 'Peticionamento', 'Pré-protocolo'],
        })
    })
    it('gestor em duas unidades vê os dados da equipe e exporta', () => {
        expect(sim('bruno').summary).toBe(
            'Vê 4 dashboards em 2 unidades, com os dados de toda a equipe, e pode exportar.',
        )
    })
    it('Diretoria vê todos os dashboards das suas unidades', () => {
        const ana = sim('ana')
        expect(ana.summary).toBe(
            'Vê todos os dashboards em todas as unidades, com os dados de toda a equipe, e pode exportar.',
        )
        expect(ana.dashboards).toEqual(['Todos os dashboards das suas unidades'])
    })
    it('sem papel não vê nada', () => {
        expect(sim('eduardo')).toEqual({
            profile: 'Sem papel, equipe ou unidade',
            summary: 'Não vê nenhum dashboard até um admin aprovar o pedido e definir equipe e unidade.',
            dashboards: [],
        })
    })
    it('equipe sem regra não vê nada', () => {
        expect(sim('diego').summary).toBe('Não vê nenhum dashboard: a equipe Pendências ainda não tem regra.')
        expect(sim('diego').dashboards).toEqual([])
    })
})
