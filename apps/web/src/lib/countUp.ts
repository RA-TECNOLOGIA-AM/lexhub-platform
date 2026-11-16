// Módulo: as contas da animação dos números (sem React; testado em countUp.test.ts).

// Começa rápido e freia no fim (como a contagem da v1).
export const easeOutCubic = (t: number) => 1 - (1 - t) ** 3

// O valor no instante t (0 = de onde sai, 1 = aonde chega).
export function tween(from: number, to: number, t: number): number {
    const k = easeOutCubic(Math.min(1, Math.max(0, t)))
    return from + (to - from) * k
}

// Quem pediu menos movimento no sistema vê o número final direto.
export function prefersReducedMotion(): boolean {
    return typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches === true
}
