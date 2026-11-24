import { useRef } from 'react'
import { contrastWithWhite, isCustomAccent, isThemeAccent, THEME_ACCENTS } from '../../lib/themeEngine.ts'
import { Icon } from '../ui/Icon.tsx'

type AccentPickerProps = {
    accent: string | null // a escolha guardada ('tema' | id | '#rrggbb'; null = "Do tema")
    accentHex: string // a cor que vale agora (em "Do tema", a do tema ativo)
    themeAccentHex: string // a cor do tema ativo (pinta a bolinha "Do tema")
    onChange: (accent: string) => void
}

// Módulo: Cor de destaque — "Do tema" + as cores prontas + "+" (qualquer cor, pelo seletor do navegador)
// e a faixa com o nome e o hex da cor que vale. Cor livre clara demais ganha um aviso (não bloqueia).
export function AccentPicker({ accent, accentHex, themeAccentHex, onChange }: AccentPickerProps) {
    const colorInput = useRef<HTMLInputElement>(null)
    const fromTheme = isThemeAccent(accent)
    const custom = isCustomAccent(accent)
    const name = fromTheme
        ? 'Do tema'
        : custom
          ? 'Personalizada'
          : (THEME_ACCENTS.find((a) => a.id === accent)?.name ?? 'Do tema')
    const hardToRead = contrastWithWhite(accentHex) < 4.5

    return (
        <div className="settings-accent">
            <div className="settings-swatches" role="group" aria-label="Cor de destaque">
                {THEME_ACCENTS.map((a) => {
                    const selected = a.hex ? accent === a.id : fromTheme
                    return (
                        <button
                            key={a.id}
                            type="button"
                            className="settings-swatch"
                            aria-pressed={selected}
                            aria-label={a.name}
                            title={a.name}
                            style={{
                                background:
                                    a.hex ??
                                    `linear-gradient(135deg, ${themeAccentHex} 50%, color-mix(in srgb, ${themeAccentHex} 55%, #fff) 50%)`,
                            }}
                            onClick={() => onChange(a.id)}
                        >
                            {selected && <Icon name="check" size={14} />}
                        </button>
                    )
                })}
                <button
                    type="button"
                    className="settings-swatch settings-swatch-custom"
                    aria-pressed={custom}
                    aria-label="Escolher outra cor"
                    title="Escolher outra cor"
                    style={custom ? { background: accentHex } : undefined}
                    onClick={() => colorInput.current?.click()}
                >
                    <Icon name={custom ? 'check' : 'plus'} size={14} />
                </button>
                <input
                    ref={colorInput}
                    type="color"
                    className="sr-only"
                    tabIndex={-1}
                    aria-hidden="true"
                    value={accentHex}
                    onChange={(e) => onChange(e.target.value)}
                />
            </div>
            <div className="settings-accent-strip">
                <span className="settings-accent-dot" style={{ background: accentHex }} />
                <span className="settings-accent-name">{name}</span>
                <span className="settings-accent-hex">{accentHex.toUpperCase()}</span>
            </div>
            {hardToRead && <p className="small settings-warn">Texto pode ficar difícil de ler nos botões.</p>}
        </div>
    )
}
