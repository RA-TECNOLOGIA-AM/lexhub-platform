import { describe, expect, it } from 'vitest'
import { buildTarget, emptyForm, slugify } from './approveView.ts'

describe('slugify', () => {
    it('tira acento e símbolo, junta com hífen', () => {
        expect(slugify('Escritório São João & Filhos')).toBe('escritorio-sao-joao-filhos')
        expect(slugify('  --LexGroup--  ')).toBe('lexgroup')
    })
})

describe('buildTarget — organização existente', () => {
    it('membro precisa de pelo menos uma unidade com cargo', () => {
        expect(buildTarget({ ...emptyForm('o1'), unitRoles: { u1: '' } })).toEqual({
            error: 'Escolha pelo menos uma unidade e o cargo nela.',
        })
    })

    it('membro com unidades: só as que têm cargo', () => {
        const r = buildTarget({ ...emptyForm('o1'), unitRoles: { u1: 'leitor', u2: '' } })
        expect(r).toEqual({
            target: {
                kind: 'existing',
                org_id: 'o1',
                org_role: 'member',
                units: [{ unit_id: 'u1', role_key: 'leitor' }],
            },
        })
    })

    it('desenvolvedor (admin) vê todas: unidades não vão', () => {
        const r = buildTarget({ ...emptyForm('o1'), orgRole: 'admin', unitRoles: { u1: 'gestor' } })
        expect(r).toEqual({ target: { kind: 'existing', org_id: 'o1', org_role: 'admin', units: [] } })
    })

    it('sem organização escolhida', () => {
        expect(buildTarget(emptyForm(''))).toEqual({ error: 'Escolha a organização.' })
    })
})

describe('buildTarget — organização nova', () => {
    const base = {
        ...emptyForm(),
        mode: 'new' as const,
        newName: 'Escritório Novo',
        newSlug: 'escritorio-novo',
        unitCode: 'sede',
        unitName: 'Sede',
    }

    it('monta org + 1ª unidade (código em maiúsculas)', () => {
        expect(buildTarget(base)).toEqual({
            target: {
                kind: 'new',
                name: 'Escritório Novo',
                slug: 'escritorio-novo',
                org_role: 'owner',
                unit: { code: 'SEDE', name: 'Sede', timezone: 'America/Manaus' },
            },
        })
    })

    it('slug e código inválidos', () => {
        expect(buildTarget({ ...base, newSlug: 'Com Espaço' })).toHaveProperty('error')
        expect(buildTarget({ ...base, unitCode: 's' })).toHaveProperty('error')
        expect(buildTarget({ ...base, unitName: ' ' })).toEqual({ error: 'Informe o nome da primeira unidade.' })
    })
})
