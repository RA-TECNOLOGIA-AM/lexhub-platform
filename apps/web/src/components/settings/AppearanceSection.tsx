import { useAppearance } from '../../contexts/appearance-context.ts'
import { resolveAppearance } from '../../lib/appearance.ts'
import { DEFAULT_THEME, isValidThemeId, THEME_PRESETS, themePreview } from '../../lib/themeEngine.ts'
import type { ThemeMode } from '../../types/index.ts'
import { Icon } from '../ui/Icon.tsx'
import { AccentPicker } from './AccentPicker.tsx'
import { ThemeCard } from './ThemeCard.tsx'

const MODES: { mode: ThemeMode; label: string; icon: 'sun' | 'moon' }[] = [
    { mode: 'light', label: 'Claro', icon: 'sun' },
    { mode: 'dark', label: 'Escuro', icon: 'moon' },
]

const GALLERIES: { mode: ThemeMode; title: string; hint: string }[] = [
    { mode: 'light', title: 'Tema claro', hint: 'Usado quando o modo claro está ativo.' },
    { mode: 'dark', title: 'Tema escuro', hint: 'Usado quando o modo escuro está ativo.' },
]

// Módulo: Configurações → Aparência (igual ao LexFlow): Modo, Cor de destaque e as galerias de tema claro
// e escuro. Tudo aplica na hora e fica salvo na conta (AppearanceProvider).
export function AppearanceSection() {
    const { appearance, resolved, setMode, setTheme, setAccent, saveError } = useAppearance()

    // O tema escolhido em cada modo (ou o padrão) e o destaque resolvido para cada miniatura.
    const chosen = (mode: ThemeMode) =>
        isValidThemeId(appearance[mode], mode) ? appearance[mode]! : DEFAULT_THEME[mode]
    const accentFor = (mode: ThemeMode, themeId: string) =>
        resolveAppearance({ ...appearance, mode, [mode]: themeId }, false).accentHex
    const previewOf = (mode: ThemeMode, themeId: string) => ({
        ...themePreview(themeId),
        accent: accentFor(mode, themeId),
    })
    const activeTheme = THEME_PRESETS.find((t) => t.id === resolved.themeId)

    return (
        <div className="settings-stack settings-appearance">
            {saveError && (
                <p className="small settings-warn" role="status">
                    {saveError}
                </p>
            )}

            <div className="settings-appearance-top">
                <section className="settings-block">
                    <h3 className="settings-block-title">Modo</h3>
                    <p className="small muted">Claro ou escuro, como você escolheu.</p>
                    <div className="settings-modes">
                        {MODES.map((m) => (
                            <ThemeCard
                                key={m.mode}
                                preview={previewOf(m.mode, chosen(m.mode))}
                                selected={resolved.mode === m.mode}
                                data={{ 'data-mode': m.mode }}
                                onSelect={() => setMode(m.mode)}
                                label={
                                    <>
                                        <Icon name={m.icon} size={15} />
                                        {m.label}
                                    </>
                                }
                            />
                        ))}
                    </div>
                </section>
                <section className="settings-block">
                    <h3 className="settings-block-title">Cor de destaque</h3>
                    <p className="small muted">Botões principais, seleção e foco. Do tema usa a cor de cada tema.</p>
                    <AccentPicker
                        accent={appearance.accent}
                        accentHex={resolved.accentHex}
                        themeAccentHex={activeTheme?.accent ?? resolved.accentHex}
                        onChange={setAccent}
                    />
                </section>
            </div>

            {GALLERIES.map((g) => (
                <section key={g.mode} className="settings-block">
                    <h3 className="settings-block-title">{g.title}</h3>
                    <p className="small muted">{g.hint}</p>
                    <div className="settings-gallery">
                        {THEME_PRESETS.filter((t) => t.mode === g.mode).map((t) => (
                            <ThemeCard
                                key={t.id}
                                preview={previewOf(g.mode, t.id)}
                                label={t.name}
                                selected={chosen(g.mode) === t.id}
                                data={{ 'data-theme-id': t.id }}
                                onSelect={() => setTheme(g.mode, t.id)}
                            />
                        ))}
                    </div>
                </section>
            ))}
        </div>
    )
}
