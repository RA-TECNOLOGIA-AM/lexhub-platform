import type { CSSProperties } from 'react'
import './LogoJustica.css'

type LogoJusticaProps = {
    /** `none` = estático; `once` = uma sequência e para; `loop` = repete. */
    animation?: 'none' | 'once' | 'loop'
    /** Duração de uma sequência completa (mão → círculo → volta → mão), em ms. */
    durationMs?: number
    size?: number | string
    className?: string
}

// Mão segurando a balança. Animado: vira um círculo, dá uma volta e retorna à mão
// com a balança pousando por cima.
export function LogoJustica({ animation = 'none', durationMs = 6000, size = 100, className }: LogoJusticaProps) {
    const style = { '--logo-justica-dur': `${durationMs}ms` } as CSSProperties
    const classes = ['logo-justica', `logo-justica--${animation}`, className].filter(Boolean).join(' ')

    return (
        <svg
            className={classes}
            style={style}
            viewBox="0 0 100 100"
            width={size}
            height={size}
            aria-hidden="true"
            fill="none"
            stroke="currentColor"
            strokeLinecap="round"
            strokeLinejoin="round"
        >
            {animation !== 'none' && (
                <g className="logo-justica__circulo">
                    <circle
                        className="logo-justica__anel"
                        cx="50"
                        cy="50"
                        r="36"
                        strokeWidth="6"
                        transform="rotate(-90 50 50)"
                    />
                    <circle cx="50" cy="14" r="5" fill="currentColor" stroke="none" />
                </g>
            )}

            <g className="logo-justica__mao">
                <rect
                    x="10"
                    y="62"
                    width="10"
                    height="26"
                    rx="2"
                    fill="currentColor"
                    stroke="none"
                    transform="rotate(-8 15 75)"
                />
                <path strokeWidth="5" d="M23 66 C30 61 38 61 46 63 L57 66 C61 67.5 61 72.5 56.5 72.5 L44 72" />
                <path
                    strokeWidth="5"
                    d="M23 84 L52 86 C57 86 61 84.5 65 82 L84 69.5 C88.5 66.5 85 59.5 80 62 L64 71.5"
                />
            </g>

            <g className="logo-justica__balanca">
                <circle cx="50" cy="11" r="3.5" fill="currentColor" stroke="none" />
                <path strokeWidth="4" d="M50 14 V50" />
                <path fill="currentColor" stroke="none" d="M40 55 H60 L57 49 H43 Z" />
                <g className="logo-justica__travessao">
                    <path strokeWidth="4" d="M27 20 H73" />
                    <path strokeWidth="2.5" d="M30 20 L22 38 M30 20 L38 38 M70 20 L62 38 M70 20 L78 38" />
                    <path
                        fill="currentColor"
                        stroke="none"
                        d="M19 38 H41 A11 8 0 0 1 19 38 Z M59 38 H81 A11 8 0 0 1 59 38 Z"
                    />
                </g>
            </g>
        </svg>
    )
}
