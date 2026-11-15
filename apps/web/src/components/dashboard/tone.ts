// Cor de um card ou selo: accent = laranja da marca, ok = verde, info = azul, danger = vermelho.
export type Tone = 'accent' | 'ok' | 'info' | 'danger' | 'warn' | 'neutral'

// O tom de uma variação: subir é bom (ou ruim, quando betterWhenDown); 0 ou sem comparativo é neutro.
export function deltaTone(value: number | null, betterWhenDown = false): Tone {
    if (!value) return 'neutral'
    return (betterWhenDown ? value < 0 : value > 0) ? 'ok' : 'danger'
}
