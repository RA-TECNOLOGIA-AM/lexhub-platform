import type { ReactNode } from 'react'
import { fmt } from '../../lib/format.ts'
import { Icon, type IconName } from '../ui/Icon.tsx'
import { deltaTone, type Tone } from './tone.ts'

// Módulo: os cards de indicador dos dashboards com seções (layout novo do Protocolo).
// HeroStat = card grande (valor, selo ao lado ou embaixo, rodapé); MiniStat = linha compacta;
// Pill = selo; DeltaPill = "↗ +52,73%" pintado de bom/ruim.

type HeroStatProps = {
    label: string
    icon: IconName
    tone: Tone // a faixa de cima e o ícone
    value: ReactNode
    aside?: ReactNode // selo à direita do valor (ex.: DeltaPill)
    below?: ReactNode // selo embaixo do valor (valor longo, como R$)
    footer?: ReactNode // depois do divisor
    hint?: string // "i" com a explicação (opcional)
    outline?: boolean // borda inteira na cor do tom (cards de devolução)
    className?: string // posição numa grade própria (ex.: card alto do Comercial)
}

export function HeroStat({ label, icon, tone, value, aside, below, footer, hint, outline, className }: HeroStatProps) {
    return (
        <div className={`card hero tone-${tone}${outline ? ' outline' : ''}${className ? ` ${className}` : ''}`}>
            <div className="hero-top">
                <span className="hero-l">{label}</span>
                <span className="hero-tools">
                    {hint && <InfoTip text={hint} />}
                    <ToneIcon icon={icon} tone={tone} />
                </span>
            </div>
            <div className="hero-mid">
                <span className="hero-v num">{value}</span>
                {aside}
            </div>
            {/* Sempre presente (vazio sem comparativo): na fileira da seção 01, cada card tem as mesmas 4 linhas. */}
            <div className="hero-below">{below}</div>
            {footer && <div className="hero-foot">{footer}</div>}
        </div>
    )
}

type MiniStatProps = {
    label: string
    icon: IconName
    tone: Tone
    value: ReactNode
    extra?: ReactNode // ao lado do valor ("no período")
    below?: ReactNode // linha centralizada embaixo (o comparativo vs mês anterior)
    hint?: string
    className?: string // posição numa grade própria
}

export function MiniStat({ label, icon, tone, value, extra, below, hint, className }: MiniStatProps) {
    return (
        <div className={className ? `card mini ${className}` : 'card mini'}>
            <div className="mini-text">
                <span className="hero-l">
                    {label}
                    {/* No compacto empilhado (.grid-mini-stack), o "i" vem logo após o rótulo e só o ícone fica no
                        canto: sobra espaço para rótulos longos. Fora dele, o "i" fica ao lado do ícone. */}
                    {hint && (
                        <span className="mini-l-tip">
                            <InfoTip text={hint} />
                        </span>
                    )}
                </span>
                <span className="mini-line">
                    <span className="mini-v num">{value}</span>
                    {extra}
                </span>
            </div>
            <span className="hero-tools">
                {hint && (
                    <span className="mini-side-tip">
                        <InfoTip text={hint} />
                    </span>
                )}
                <ToneIcon icon={icon} tone={tone} />
            </span>
            {below && <div className="mini-below">{below}</div>}
        </div>
    )
}

export function ToneIcon({ icon, tone }: { icon: IconName; tone: Tone }) {
    return (
        <span className={`tone-icon tone-${tone}`} aria-hidden="true">
            <Icon name={icon} size={16} />
        </span>
    )
}

export function Pill({ tone = 'neutral', children }: { tone?: Tone; children: ReactNode }) {
    return <span className={`pill num tone-${tone}`}>{children}</span>
}

// "↗ +52,73%" (ou "0,00%"). null = sem comparativo: não mostra nada.
// Com legenda ("vs mês anterior"), ela vai numa linha embaixo da porcentagem, como na v1.
export function DeltaPill({
    value,
    betterWhenDown = false,
    suffix,
    plain = false,
}: {
    value: number | null
    betterWhenDown?: boolean
    suffix?: string // "vs mês anterior"
    plain?: boolean // sem fundo (dentro do MiniStat)
}) {
    if (value === null) return null
    const tone = deltaTone(value, betterWhenDown)
    const sign = value > 0 ? '+' : value < 0 ? '-' : ''
    const content = (
        <>
            {value !== 0 && <span aria-hidden="true">{value > 0 ? '↗' : '↘'}</span>}
            {sign}
            {fmt.pct2(Math.abs(value))}
        </>
    )
    const delta = plain ? (
        <span className={`delta-plain num tone-${tone}`}>{content}</span>
    ) : (
        <Pill tone={tone}>{content}</Pill>
    )
    if (!suffix) return delta
    return (
        <span className="delta-stack">
            {delta}
            <span className="delta-caption">{suffix.trim()}</span>
        </span>
    )
}

// Um número com legenda embaixo, no formato do comparativo (ex.: "39,8%" / "na fila").
export function StackedRate({ text, caption, tone }: { text: string; caption: string; tone: Tone }) {
    return (
        <span className="delta-stack">
            <span className={`delta-plain num tone-${tone}`}>{text}</span>
            <span className="delta-caption">{caption}</span>
        </span>
    )
}

// "i" que mostra a explicação ao passar o mouse ou focar com o teclado.
export function InfoTip({ text }: { text: string }) {
    return (
        <span className="tip" tabIndex={0} aria-label={text} data-tip={text}>
            <Icon name="info" size={15} />
        </span>
    )
}

// Rodapé de duas pontas: texto à esquerda, texto à direita.
export function FootRow({ left, right }: { left: ReactNode; right?: ReactNode }) {
    return (
        <div className="foot-row">
            <span>{left}</span>
            {right !== undefined && <span>{right}</span>}
        </div>
    )
}
