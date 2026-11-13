import { describe, expect, it } from 'vitest'
import { menuPermissions, NAV_SECTIONS, visibleItems } from './navigation.ts'

const admin = NAV_SECTIONS.find((s) => s.title === 'Administração')!
const keys = (perms: Parameters<typeof visibleItems>[1]) => visibleItems(admin, perms).map((i) => i.key)

const ALL = { access: true, members: true, sources: true, audit: true }
const NONE = { access: false, members: false, sources: false, audit: false }

describe('visibleItems', () => {
    it('Acesso só aparece para quem gere acesso (Owner, Desenvolvedor, Gestor, Controller)', () => {
        expect(keys(ALL)).toContain('acesso')
        expect(keys(NONE)).not.toContain('acesso')
    })
    it('Unidades e fontes só aparece para quem vê fontes (Owner, Desenvolvedor, Gestor, Controller)', () => {
        expect(keys(ALL)).toContain('unidades')
        expect(keys({ ...ALL, sources: false })).not.toContain('unidades')
    })
    it('Auditoria só aparece para quem vê a auditoria (Owner, Desenvolvedor)', () => {
        expect(keys(ALL)).toContain('auditoria')
        expect(keys({ ...ALL, audit: false })).not.toContain('auditoria')
    })
    it('enquanto as permissões não chegam, Acesso e Unidades ficam escondidos (não piscam para quem não gere)', () => {
        expect(keys(null)).not.toContain('acesso')
        expect(keys(null)).not.toContain('unidades')
        expect(keys(null)).toContain('membros')
    })
})

describe('menuPermissions', () => {
    it('se a consulta falhar (ex.: função ainda não aplicada no banco), mostra os itens: a página protege sozinha', () => {
        expect(menuPermissions(null, new Error('function api.my_admin_permissions does not exist'))).toEqual(ALL)
    })
    it('com resposta, usa a resposta; carregando, null', () => {
        const some = { access: false, members: true, sources: false, audit: false }
        expect(menuPermissions(some, null)).toEqual(some)
        expect(menuPermissions(null, null)).toBeNull()
    })
})
