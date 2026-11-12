import { useContext, useLayoutEffect } from 'react'
import { TransitionHoldContext } from './PageTransitionContext.ts'

// Enquanto o componente que chama estiver montado, o overlay da transição não sai.
// useLayoutEffect: registra antes da tela pintar, para o overlay não "piscar" e sair cedo.
// Fora do PageTransitionProvider não faz nada.
export function useHoldTransition(): void {
    const hold = useContext(TransitionHoldContext)

    useLayoutEffect(() => hold?.(), [hold])
}
