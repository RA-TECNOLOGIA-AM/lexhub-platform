import { describe, expect, it } from 'vitest'
import { menuPermissions, NAV_SECTIONS, visibleItems } from './navigation.ts'

const admin = NAV_SECTIONS.find((s) => s.title === 'Administração')!
const keys = (perms: Parameters<typeof visibleItems>[1]) => visibleItems(admin, perms).map((i) => i.key)

describe('visibleItems', () => {
    it('Acesso só aparece para quem gere acesso (Owner, Desenvolvedor, Gestor, Controller)', () => {
        expect(keys({ access: true, members: true })).toContain('acesso')
        expect(keys({ access: false, members: false })).not.toContain('acesso')
    })
    it('enquanto as permissões não chegam, Acesso fica escondido (não pisca para quem não gere)', () => {
        expect(keys(null)).not.toContain('acesso')
        expect(keys(null)).toContain('membros')
    })
})

describe('menuPermissions', () => {
    it('se a consulta falhar (ex.: função ainda não aplicada no banco), mostra os itens: a página protege sozinha', () => {
        expect(menuPermissions(null, new Error('function api.my_admin_permissions does not exist'))).toEqual({
            access: true,
            members: true,
        })
    })
    it('com resposta, usa a resposta; carregando, null', () => {
        expect(menuPermissions({ access: false, members: true }, null)).toEqual({ access: false, members: true })
        expect(menuPermissions(null, null)).toBeNull()
    })
})
