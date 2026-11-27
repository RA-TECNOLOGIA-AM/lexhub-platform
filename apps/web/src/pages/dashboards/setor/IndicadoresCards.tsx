import type { ReactNode } from 'react'
import { DeltaPill, InfoTip, Pill, ToneIcon } from '../../../components/dashboard/StatCard.tsx'
import type { Tone } from '../../../components/dashboard/tone.ts'
import type { IconName } from '../../../components/ui/Icon.tsx'
import { fmt } from '../../../lib/format.ts'

// Cards da seção 01 dos setores LexPre (Org. Documentos, Peticionamento) que o HeroStat/MiniStat não cobrem: o
// card "duplo" (dois números lado a lado, como Média x Mediana), o card do modo manual x automático e o card
// compacto com selo e borda de alerta.

export type Caixa = {
    label: string
    value: ReactNode
    delta?: number | null // variação vs mês anterior (DeltaPill)
    betterWhenDown?: boolean
    destaque?: boolean // número na cor do card (ex.: o automático)
}

type CardDuploProps = {
    label: string
    icon: IconName
    tone: Tone
    badge?: ReactNode // selo ao lado do título (ex.: "77,8% Auto")
    hint?: string
    caixas: [Caixa, Caixa]
    footer?: ReactNode
}

export function CardDuplo({ label, icon, tone, badge, hint, caixas, footer }: CardDuploProps) {
    return (
        <div className={`card hero tone-${tone}`}>
            <div className="hero-top">
                <span className="hero-l">{label}</span>
                <span className="hero-tools">
                    {badge}
                    {hint && <InfoTip text={hint} />}
                    {!badge && <ToneIcon icon={icon} tone={tone} />}
                </span>
            </div>
            <div className="duo">
                {caixas.map((c) => (
                    <div key={c.label} className="fbox duo-box">
                        <span className="duo-l">{c.label}</span>
                        <span className={`duo-v num${c.destaque ? ' tone-text-info' : ''}`}>{c.value}</span>
                        {c.delta !== undefined && <DeltaPill value={c.delta} betterWhenDown={c.betterWhenDown} plain />}
                    </div>
                ))}
            </div>
            {footer && <div className="hero-foot">{footer}</div>}
        </div>
    )
}

type CardCompactoProps = {
    label: string
    icon: IconName
    tone: Tone
    value: ReactNode
    delta: number | null // comparativo vs mês anterior, centralizado embaixo (padrão dos cards de cima)
    betterWhenDown?: boolean
    below?: ReactNode // no lugar do comparativo (ex.: "agora · não depende do período")
    hint?: string
    alerta?: boolean // borda e selo "Atenção"
}

// Mesma estrutura do MiniStat (texto | ícone, e a linha centralizada embaixo), com o selo "Atenção" no rótulo.
export function CardCompacto({
    label,
    icon,
    tone,
    value,
    delta,
    betterWhenDown,
    below,
    hint,
    alerta,
}: CardCompactoProps) {
    return (
        <div className={`card mini compacto${alerta ? ' alerta' : ''}`}>
            <div className="mini-text">
                <span className="hero-l compacto-l">
                    <span className={alerta ? 'tone-text-danger' : undefined}>{label}</span>
                    {alerta && <Pill tone="danger">Atenção</Pill>}
                    {hint && <InfoTip text={hint} />}
                </span>
                <span className="mini-line">
                    <span className="mini-v num">{value}</span>
                </span>
            </div>
            <span className="hero-tools">
                <ToneIcon icon={icon} tone={tone} />
            </span>
            <div className="mini-below">
                {below ?? <DeltaPill value={delta} betterWhenDown={betterWhenDown} suffix=" vs mês anterior" plain />}
            </div>
        </div>
    )
}

type CardModoProps = {
    label: string // "Modo de peticionamento"
    manual: number
    auto: number
    deltaManual: number | null
    deltaAuto: number | null
    hint?: string
}

// Manual x automático numa linha compacta: selo "% Auto", os dois números com a variação e a barra dividida.
export function CardModo({ label, manual, auto, deltaManual, deltaAuto, hint }: CardModoProps) {
    const pctAuto = manual + auto > 0 ? (auto / (manual + auto)) * 100 : 0
    return (
        <div className="card mini modo">
            <span className="hero-l compacto-l">
                {label}
                {hint && <InfoTip text={hint} />}
            </span>
            <div className="reaj-cols">
                <div className="fstack">
                    <span className="muted">Manualmente</span>
                    <span className="mini-line">
                        <span className="mini-v num">{fmt.int(manual)}</span>
                        <DeltaPill value={deltaManual} plain />
                    </span>
                </div>
                <div className="fstack">
                    <span className="muted">Automaticamente</span>
                    <span className="mini-line">
                        <span className="mini-v num tone-text-info">{fmt.int(auto)}</span>
                        <DeltaPill value={deltaAuto} plain />
                    </span>
                </div>
            </div>
            <div className="modo-barra">
                <div className="split" aria-hidden="true">
                    <span className="split-b" style={{ flexGrow: manual }} />
                    <span className="split-info" style={{ flexGrow: auto }} />
                </div>
                <div className="modo-legenda num">
                    <span>
                        <span className="dot split-b" aria-hidden="true" />
                        Manual: {fmt.dec1(100 - pctAuto)}%
                    </span>
                    <span className="tone-text-info">
                        <span className="dot split-info" aria-hidden="true" />
                        Automático: {fmt.dec1(pctAuto)}%
                    </span>
                </div>
            </div>
        </div>
    )
}

// Rodapé dos cards de Tempo (média + mediana): "Ganho de velocidade em ambos", "Perda de velocidade em ambos" ou cada um.
export function RitmoDosDois({ media, mediana }: { media: number | null; mediana: number | null }) {
    const sentido = (v: number | null) => (!v ? 0 : v < 0 ? -1 : 1) // -1 = ganho (tempo caiu)
    const a = sentido(media)
    const b = sentido(mediana)
    if (a === 0 && b === 0) return <span className="muted">Sem variação</span>
    if (a === b) {
        return a < 0 ? (
            <span className="tone-text-ok">Ganho de velocidade em ambos</span>
        ) : (
            <span className="tone-text-danger">Perda de velocidade em ambos</span>
        )
    }
    const nome = (v: number) => (v < 0 ? 'ganho' : v > 0 ? 'perda' : 'estável')
    return (
        <span className="muted">
            Média: <span className={a < 0 ? 'tone-text-ok' : 'tone-text-danger'}>{nome(a)}</span> · Mediana:{' '}
            <span className={b < 0 ? 'tone-text-ok' : 'tone-text-danger'}>{nome(b)}</span>
        </span>
    )
}
