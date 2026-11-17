import { useContext } from 'react'
import { TransitionAreaContext } from './PageTransitionContext.ts'

// Ref para a coluna do conteúdo do AppLayout: as trocas de página animam só o miolo, abaixo da topbar.
// Fora do PageTransitionProvider devolve undefined (a ref fica sem efeito).
export function useTransitionArea() {
    return useContext(TransitionAreaContext)
}
