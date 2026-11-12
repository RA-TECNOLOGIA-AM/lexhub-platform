import { useEffect, useRef, useState, type ReactNode } from 'react'
import { useNavigate, type To } from 'react-router'
import { TransitionContext } from './PageTransitionContext.ts'
import { LogoJustica } from '../ui/LogoJustica.tsx'
import './PageTransition.css'

const LOADING_MS = 1500
const EXITING_MS = 450

type TransitionPhase = 'idle' | 'loading' | 'exiting'

export function PageTransitionProvider({ children }: { children: ReactNode }) {
    const navigate = useNavigate()
    const [phase, setPhase] = useState<TransitionPhase>('idle')
    const phaseRef = useRef<TransitionPhase>('idle')
    const loadingTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
    const exitingTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

    useEffect(
        () => () => {
            if (loadingTimer.current !== null) clearTimeout(loadingTimer.current)
            if (exitingTimer.current !== null) clearTimeout(exitingTimer.current)
        },
        [],
    )

    function transitionTo(to: To): void {
        if (phaseRef.current !== 'idle') return

        const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
        phaseRef.current = 'loading'
        setPhase('loading')

        loadingTimer.current = setTimeout(
            () => {
                navigate(to)
                phaseRef.current = 'exiting'
                setPhase('exiting')

                exitingTimer.current = setTimeout(
                    () => {
                        phaseRef.current = 'idle'
                        setPhase('idle')
                    },
                    reducedMotion ? 0 : EXITING_MS,
                )
            },
            reducedMotion ? 0 : LOADING_MS,
        )
    }

    return (
        <TransitionContext.Provider value={{ transitionTo }}>
            {children}

            {phase !== 'idle' && (
                <div className={`transition-overlay ${phase}`} aria-label="Carregando página" role="status">
                    <div className="loader-container">
                        <LogoJustica animation="once" durationMs={LOADING_MS} size={180} />
                    </div>
                </div>
            )}
        </TransitionContext.Provider>
    )
}
