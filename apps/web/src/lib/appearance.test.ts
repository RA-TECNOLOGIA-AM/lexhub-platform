import { describe, expect, it } from 'vitest'
import type { Appearance } from '../types/index.ts'
import {
    APPEARANCE_KEY,
    applyAppearance,
    cacheAppearance,
    MANAGED_VARS,
    normalizeAppearance,
    pickAppearance,
    readCachedAppearance,
    resolveAppearance,
} from './appearance.ts'
import { contrastRatio as contrast, THEME_PRESETS } from './themeEngine.ts'

const NONE: Appearance = { mode: null, light: null, dark: null, accent: null }

function memory(initial: Record<string, string> = {}) {
    const data: Record<string, string> = { ...initial }
    return {
        data,
        getItem: (k: string) => data[k] ?? null,
        setItem: (k: string, v: string) => {
            data[k] = v
        },
    }
}

// <html> falso: só o que applyAppearance usa.
function fakeRoot() {
    const props = new Map<string, string>()
    const root = {
        dataset: {} as Record<string, string>,
        style: {
            setProperty: (k: string, v: string) => props.set(k, v),
            removeProperty: (k: string) => props.delete(k),
        },
    }
    return { root: root as unknown as HTMLElement, props, dataset: root.dataset }
}

describe('resolveAppearance', () => {
    it('sem escolha: segue o sistema e não escreve nenhuma variável (visual atual)', () => {
        expect(resolveAppearance(NONE, false)).toMatchObject({ mode: 'light', themeId: 'light-default', vars: {} })
        expect(resolveAppearance(NONE, true)).toMatchObject({ mode: 'dark', themeId: 'dark-default', vars: {} })
    })

    it('o modo escolhido manda sobre o sistema', () => {
        expect(resolveAppearance({ ...NONE, mode: 'light' }, true).mode).toBe('light')
    })

    it('tema do motor: só variáveis gerenciadas, nunca as de status/foco/link', () => {
        const r = resolveAppearance({ ...NONE, mode: 'dark', dark: 'dark-dracula' }, false)
        expect(r.themeId).toBe('dark-dracula')
        expect(r.vars['--bg']).toMatch(/^#[0-9a-f]{6}$/)
        expect(r.vars['--accent']).toBe(r.accentHex)
        for (const key of Object.keys(r.vars)) expect(MANAGED_VARS).toContain(key)
        for (const key of ['--ok', '--danger', '--warn', '--info', '--focus', '--link', '--chart-brand'])
            expect(r.vars).not.toHaveProperty(key)
    })

    it('cor fixa no Claro Padrão: só as variáveis do destaque', () => {
        const r = resolveAppearance({ ...NONE, accent: 'azul' }, false)
        expect(r.vars['--accent']).toBe('#2563eb')
        expect(r.vars['--on-accent']).toBe('#ffffff')
        expect(Object.keys(r.vars).sort()).toEqual(['--accent', '--accent-hover', '--accent-soft', '--on-accent'])
    })

    it('"Do tema" num padrão = nada; num tema do motor = a cor do tema', () => {
        expect(resolveAppearance({ ...NONE, accent: 'tema' }, false).vars).toEqual({})
        const nord = resolveAppearance({ ...NONE, mode: 'dark', dark: 'dark-nord', accent: 'tema' }, false)
        expect(nord.vars['--accent']).toBe(nord.accentHex)
    })

    it('o destaque resolvido aparece mesmo sem variáveis (faixa "Do tema" do Claro Padrão)', () => {
        expect(resolveAppearance(NONE, false).accentHex).toBe('#b35500')
    })
})

describe('barra lateral e loading nos temas do motor', () => {
    const engineThemes = THEME_PRESETS.filter((t) => !t.builtIn)

    it('lista de unidades (seletor da barra) legível sobre o fundo do menu, em todo tema', () => {
        for (const t of engineThemes) {
            const r = resolveAppearance({ ...NONE, mode: t.mode, [t.mode]: t.id }, false)
            expect(contrast(r.vars['--side-item'], r.vars['--side-hover']), t.id).toBeGreaterThanOrEqual(4.5)
        }
    })

    it('loading com o fundo do tema e uma balança visível (destaque, ou texto se o destaque some)', () => {
        for (const t of engineThemes) {
            for (const accent of ['tema', 'grafite', 'azul']) {
                const r = resolveAppearance({ ...NONE, mode: t.mode, [t.mode]: t.id, accent }, false)
                expect(r.vars['--loader-bg'], t.id).toBe(r.vars['--bg'])
                expect(
                    contrast(r.vars['--loader-logo'], r.vars['--loader-bg']),
                    `${t.id}/${accent}`,
                ).toBeGreaterThanOrEqual(3)
            }
        }
    })

    it('padrões continuam com o loading da marca (nada escrito)', () => {
        const r = resolveAppearance({ ...NONE, accent: 'azul' }, false)
        expect(r.vars).not.toHaveProperty('--loader-bg')
        expect(r.vars).not.toHaveProperty('--loader-logo')
    })
})

describe('normalizeAppearance', () => {
    it('ids desconhecidos, do modo errado ou mal formados viram null', () => {
        expect(
            normalizeAppearance({ mode: 'sepia' as never, light: 'dark-nord', dark: 'nao-existe', accent: '#12' }),
        ).toEqual(NONE)
    })
    it('mantém o que é válido', () => {
        const ok: Appearance = { mode: 'dark', light: 'light-github', dark: 'dark-nord', accent: '#e11d48' }
        expect(normalizeAppearance(ok)).toEqual(ok)
    })
    it('nada = sem escolha', () => {
        expect(normalizeAppearance(null)).toEqual(NONE)
    })
})

describe('pickAppearance', () => {
    const local: Appearance = { ...NONE, dark: 'dark-nord' }
    it('conta vazia: vale o que está no aparelho', () => {
        expect(pickAppearance(local, NONE)).toBe(local)
    })
    it('conta com alguma escolha: a conta manda', () => {
        const account: Appearance = { ...NONE, dark: 'dark-dracula' }
        expect(pickAppearance(local, account)).toEqual(account)
    })
})

describe('cópia local', () => {
    it('grava a escolha e as variáveis dos dois modos (o index.html aplica antes do React)', () => {
        const storage = memory()
        cacheAppearance({ ...NONE, light: 'light-github', dark: 'dark-dracula' }, storage)
        const saved = JSON.parse(storage.data[APPEARANCE_KEY])
        expect(saved.prefs.dark).toBe('dark-dracula')
        expect(saved.light['--bg']).toMatch(/^#/)
        expect(saved.dark['--bg']).toMatch(/^#/)
    })

    it('lê de volta o que gravou', () => {
        const storage = memory()
        const prefs: Appearance = { mode: 'dark', light: null, dark: 'dark-nord', accent: 'azul' }
        cacheAppearance(prefs, storage)
        expect(readCachedAppearance(storage)).toEqual(prefs)
    })

    it('sem cópia nova, aproveita o modo antigo (lexhub.theme)', () => {
        expect(readCachedAppearance(memory({ 'lexhub.theme': 'dark' }))).toEqual({ ...NONE, mode: 'dark' })
    })

    it('JSON quebrado, storage que lança ou nenhum storage: sem escolha', () => {
        expect(readCachedAppearance(memory({ [APPEARANCE_KEY]: '{quebrado' }))).toEqual(NONE)
        const throwing = {
            getItem: () => {
                throw new Error('bloqueado')
            },
        }
        expect(readCachedAppearance(throwing)).toEqual(NONE)
        expect(readCachedAppearance(null)).toEqual(NONE)
        expect(() =>
            cacheAppearance(NONE, {
                setItem: () => {
                    throw new Error('cheio')
                },
            }),
        ).not.toThrow()
    })
})

describe('applyAppearance', () => {
    it('escreve o modo e as variáveis do tema', () => {
        const { root, props, dataset } = fakeRoot()
        applyAppearance(resolveAppearance({ ...NONE, mode: 'dark', dark: 'dark-dracula' }, false), root)
        expect(dataset.theme).toBe('dark')
        expect(props.get('--bg')).toMatch(/^#/)
    })

    it('voltar ao padrão não deixa nenhuma variável do tema anterior', () => {
        const { root, props, dataset } = fakeRoot()
        applyAppearance(resolveAppearance({ ...NONE, mode: 'dark', dark: 'dark-dracula', accent: 'azul' }, false), root)
        applyAppearance(resolveAppearance({ ...NONE, mode: 'light' }, false), root)
        expect(dataset.theme).toBe('light')
        expect(props.size).toBe(0)
    })
})
