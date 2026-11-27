import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { AuthContext, type AuthValue } from '../../contexts/auth-context.ts'
import type { Me } from '../../types/index.ts'
import { SettingsDialog, visibleSections } from './SettingsDialog.tsx'

const me: Me = {
    user: {
        name: 'Luís Henrique Tápia De Sousa',
        initials: 'LS',
        role_label: 'Desenvolvedor',
        can_export: true,
        can_see_commission: true,
        platform_staff: false,
        teams: ['Tecnologia', 'Controladoria'],
        offices: ['ESCRITÓRIO MASTER'],
        avatar_path: null,
        appearance: { mode: null, light: null, dark: null, accent: null },
    },
    org: { slug: 'lexgroup', name: 'LexGroup', sub: '3 unidades' },
    units: [],
    orgs: [],
}

const noop = async () => {}
const auth: AuthValue = {
    me,
    noAccess: null,
    loading: false,
    rememberLocation: true,
    signIn: noop,
    signInWithGoogle: noop,
    signOut: noop,
    refreshSession: noop,
    switchOrg: noop,
    setAvatarPath: () => {},
}

function render() {
    return renderToStaticMarkup(
        <AuthContext value={auth}>
            <SettingsDialog onClose={() => {}} />
        </AuthContext>,
    )
}

describe('SettingsDialog', () => {
    it('abre em Perfil, com o menu "Minha conta"', () => {
        const html = render()
        expect(html).toContain('Configurações')
        expect(html).toContain('Minha conta')
        expect(html).toContain('Meu Perfil')
        expect(html).toMatch(/aria-current="page"[^>]*>.*Perfil/)
    })

    it('não mostra o que ainda não existe (nem Notificações, que fica fora)', () => {
        const html = render()
        for (const item of ['Notificações', 'Companhias', 'Organização']) {
            expect(html).not.toContain(item)
        }
        expect(html).toContain('Dispositivos')
    })

    it('Perfil: nome, cargo, setores e escritórios só para leitura; foto com botão de câmera', () => {
        const html = render()
        expect(html).toContain('Luís Henrique Tápia De Sousa')
        expect(html).toContain('Desenvolvedor')
        expect(html).toContain('Tecnologia, Controladoria')
        expect(html).toContain('ESCRITÓRIO MASTER')
        expect(html).toContain('aria-label="Trocar foto"')
        expect(html).not.toContain('Editar')
        expect(html).not.toContain('Remover foto') // sem foto, nada para remover
    })

    it('com foto: oferece remover', () => {
        const withPhoto = { ...auth, me: { ...me, user: { ...me.user, avatar_path: 'u1/a.webp' } } }
        const html = renderToStaticMarkup(
            <AuthContext value={withPhoto}>
                <SettingsDialog onClose={() => {}} />
            </AuthContext>,
        )
        expect(html).toContain('Remover foto')
    })
})

describe('visibleSections', () => {
    it('Chave de API só para quem pode pedir', () => {
        expect(visibleSections(false).map((s) => s.id)).not.toContain('chave-api')
        expect(visibleSections(true).map((s) => s.id)).toContain('chave-api')
    })
})
