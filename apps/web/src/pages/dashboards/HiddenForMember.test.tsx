import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { HiddenForMemberView } from './HiddenForMember.tsx'
import { HIDDEN_REASON } from './hiddenReason.ts'

describe('HiddenForMemberView', () => {
    it('título com o primeiro nome e a contagem; cada dashboard com o motivo', () => {
        const html = renderToStaticMarkup(
            <HiddenForMemberView
                name="Bruna Lima"
                items={[
                    { key: 'comercial', title: 'Comercial', area: 'Comercial', reason: 'no_sector_rule' },
                    { key: 'nps', title: 'NPS', area: 'Marketing', reason: 'dashboard_off' },
                ]}
            />,
        )
        expect(html).toContain('Dashboards ocultos para Bruna (2)')
        expect(html).toContain('Comercial')
        expect(html).toContain(HIDDEN_REASON.no_sector_rule)
        expect(html).toContain(HIDDEN_REASON.dashboard_off)
        expect(html).toContain('<details')
    })

    it('nada oculto: diz isso', () => {
        const html = renderToStaticMarkup(<HiddenForMemberView name="Bruna" items={[]} />)
        expect(html).toContain('Dashboards ocultos para Bruna (0)')
        expect(html).toContain('Nenhum dashboard desta unidade está oculto para Bruna.')
    })

    it('textos de todos os motivos', () => {
        expect(HIDDEN_REASON).toEqual({
            no_unit_role: 'Sem cargo nesta unidade',
            no_sector_rule: 'Os setores dele não têm este dashboard e não há exceção',
            dashboard_off: 'Desligado nesta unidade',
            not_member: 'Não é membro ativo',
            org_inactive: 'Unidade ou organização inativa',
            owner_dev_only: 'Só Owner e Desenvolvedor veem este dashboard',
        })
    })
})
