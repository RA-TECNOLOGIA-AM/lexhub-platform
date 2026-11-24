import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { AppearanceContext, type AppearanceValue } from '../../contexts/appearance-context.ts'
import { resolveAppearance } from '../../lib/appearance.ts'
import type { Appearance } from '../../types/index.ts'
import { AppearanceSection } from './AppearanceSection.tsx'

const NONE: Appearance = { mode: null, light: null, dark: null, accent: null }

function render(appearance: Appearance, extra: Partial<AppearanceValue> = {}) {
    const value: AppearanceValue = {
        appearance,
        resolved: resolveAppearance(appearance, false),
        setMode: () => {},
        setTheme: () => {},
        setAccent: () => {},
        saveError: null,
        ...extra,
    }
    return renderToStaticMarkup(
        <AppearanceContext value={value}>
            <AppearanceSection />
        </AppearanceContext>,
    )
}

// Botões de tema de uma galeria (pelo data-theme-id) e quais estão marcados.
function themeButtons(html: string) {
    return [...html.matchAll(/<button[^>]*data-theme-id="([^"]+)"[^>]*>/g)].map((m) => ({
        id: m[1],
        pressed: m[0].includes('aria-pressed="true"'),
    }))
}

describe('AppearanceSection', () => {
    it('Modo, Cor de destaque e as duas galerias (15 claros, 27 escuros)', () => {
        const html = render(NONE)
        for (const text of ['Modo', 'Cor de destaque', 'Tema claro', 'Tema escuro']) expect(html).toContain(text)
        const buttons = themeButtons(html)
        expect(buttons.filter((b) => b.id.startsWith('light-'))).toHaveLength(15)
        expect(buttons.filter((b) => b.id.startsWith('dark-'))).toHaveLength(27)
    })

    it('marca o tema escolhido em cada galeria (e o padrão do outro modo)', () => {
        const pressed = themeButtons(render({ ...NONE, dark: 'dark-dracula' })).filter((b) => b.pressed)
        expect(pressed.map((b) => b.id).sort()).toEqual(['dark-dracula', 'light-default'])
    })

    it('marca o modo que vale agora', () => {
        expect(render({ ...NONE, mode: 'dark' })).toMatch(/aria-pressed="true"[^>]*data-mode="dark"/)
    })

    it('faixa do destaque: "Do tema" com a cor do tema; cor pronta com o nome dela', () => {
        const doTema = render(NONE)
        expect(doTema).toContain('Do tema')
        expect(doTema).toContain('#B35500')
        const azul = render({ ...NONE, accent: 'azul' })
        expect(azul).toMatch(/settings-accent-strip[\s\S]*Azul[\s\S]*#2563EB/)
    })

    it('cor livre clara avisa que o texto pode ficar ilegível; escura não', () => {
        expect(render({ ...NONE, accent: '#ffff00' })).toContain('Texto pode ficar difícil de ler nos botões')
        expect(render({ ...NONE, accent: '#2563eb' })).not.toContain('Texto pode ficar difícil de ler nos botões')
    })

    it('mostra quando a conta não salvou', () => {
        expect(render(NONE, { saveError: 'Não foi possível salvar na sua conta.' })).toContain(
            'Não foi possível salvar na sua conta.',
        )
    })
})
