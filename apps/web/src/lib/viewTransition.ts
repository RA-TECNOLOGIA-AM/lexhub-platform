import { flushSync } from 'react-dom'

// Módulo: aplica uma mudança de estado com animação (View Transitions API do navegador).
// Parâmetro: a função que muda o estado.
// Esconde: a API do navegador e as saídas sem animação (navegador sem suporte ou "reduzir movimento").
export function withViewTransition(update: () => void) {
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (typeof document.startViewTransition !== 'function' || reduceMotion) {
        update()
        return
    }
    const transition = document.startViewTransition(() => flushSync(update))
    // Animação pulada (outra começou por cima, aba sem desenhar...): a mudança acontece igual, só não anima.
    transition.ready.catch(() => {})
}
