import type { ReactNode } from 'react'
import type { ThemePreview } from '../../lib/themeEngine.ts'
import { Icon } from '../ui/Icon.tsx'

type ThemeCardProps = {
    preview: ThemePreview // cores do tema (themePreview), já com o destaque resolvido
    label: ReactNode // nome (ou ícone + nome, nos cartões de modo)
    selected: boolean
    onSelect: () => void
    data?: Record<`data-${string}`, string> // marca para testes e estilos (ex.: data-theme-id)
}

// Módulo: o cartão com a miniatura de uma tela (barra lateral + cartão + botão no destaque) e o nome embaixo.
// Usado nas galerias de tema e nos cartões de Modo. As cores vêm por style (não dependem das variáveis
// da página), então cada miniatura mostra o próprio tema mesmo com outro tema ativo.
export function ThemeCard({ preview, label, selected, onSelect, data }: ThemeCardProps) {
    return (
        <button type="button" className="theme-card" aria-pressed={selected} {...data} onClick={onSelect}>
            <span className="theme-mini" style={{ background: preview.bg }} aria-hidden="true">
                <span className="theme-mini-side" style={{ background: preview.sidebar }}>
                    <i style={{ background: preview.sideText }} />
                    <i style={{ background: preview.sideText }} />
                    <i style={{ background: preview.sideText }} />
                    <i style={{ background: preview.sideText }} />
                </span>
                <span className="theme-mini-main">
                    <i className="theme-mini-title" style={{ background: preview.text }} />
                    <span className="theme-mini-card" style={{ background: preview.card, borderColor: preview.border }}>
                        <i style={{ background: preview.text }} />
                        <i className="theme-mini-btn" style={{ background: preview.accent }} />
                    </span>
                </span>
            </span>
            <span className="theme-card-label">
                <span className="theme-card-name">{label}</span>
                {selected && <Icon name="check" size={15} />}
            </span>
        </button>
    )
}
