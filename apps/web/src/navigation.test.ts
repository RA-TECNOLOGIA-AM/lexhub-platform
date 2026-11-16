import { describe, expect, it } from 'vitest'
import { menuPermissions, NAV_SECTIONS, visibleItems } from './navigation.ts'

const admin = NAV_SECTIONS.find((s) => s.title === 'Administração')!
const keys = (perms: Parameters<typeof visibleItems>[1]) => visibleItems(admin, perms).map((i) => i.key)

const ALL = { access: true, members: true, sources: true, audit: true, billing: true, clients: true }
const NONE = { access: false, members: false, sources: false, audit: false, billing: false, clients: false }

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
    it('Plano e cobrança só aparece para quem vê a cobrança (Owner, Desenvolvedor, equipe RA)', () => {
        expect(keys(ALL)).toContain('plano')
        expect(keys({ ...ALL, billing: false })).not.toContain('plano')
    })
    it('enquanto as permissões não chegam, Membros, Acesso e Unidades ficam escondidos (não piscam para quem não gere)', () => {
        expect(keys(null)).not.toContain('acesso')
        expect(keys(null)).not.toContain('unidades')
        expect(keys(null)).not.toContain('membros')
    })
    it('Controller (acompanha) vê Unidades e fontes, mas não Membros nem Acesso', () => {
        const controller = {
            access: false,
            members: false,
            sources: true,
            audit: false,
            billing: false,
            clients: false,
        }
        expect(keys(controller)).toContain('unidades')
        expect(keys(controller)).not.toContain('membros')
        expect(keys(controller)).not.toContain('acesso')
    })
})

describe('Plataforma', () => {
    const platform = NAV_SECTIONS.find((s) => s.platformOnly)!
    const keysOf = (perms: Parameters<typeof visibleItems>[1], staff: boolean) =>
        visibleItems(platform, perms, staff).map((i) => i.key)

    it('Owner/Desenvolvedor da LexGroup (clients) vê Clientes, mas não Pedidos de acesso (equipe RA)', () => {
        expect(keysOf(ALL, false)).toEqual(['clientes'])
    })
    it('equipe RA vê Pedidos de acesso; sem clients nem equipe RA, a seção fica vazia', () => {
        expect(keysOf(NONE, true)).toEqual(['pedidos'])
        expect(keysOf(NONE, false)).toEqual([])
    })
})

describe('menuPermissions', () => {
    it('se a consulta falhar (ex.: função ainda não aplicada no banco), mostra os itens: a página protege sozinha', () => {
        expect(menuPermissions(null, new Error('function api.my_admin_permissions does not exist'))).toEqual(ALL)
    })
    it('com resposta, usa a resposta; carregando, null', () => {
        const some = { access: false, members: true, sources: false, audit: false, billing: false, clients: false }
        expect(menuPermissions(some, null)).toEqual(some)
        expect(menuPermissions(null, null)).toBeNull()
    })
})
