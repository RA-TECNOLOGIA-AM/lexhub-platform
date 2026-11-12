import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { useNavigate, type To } from 'react-router'
import { TransitionContext, TransitionHoldContext } from './PageTransitionContext.ts'
import { LogoJustica } from '../ui/LogoJustica.tsx'
import './PageTransition.css'

const LOADING_MS = 1500 // tempo mínimo da animação (uma volta da logo)
const EXITING_MS = 450
const SETTLE_MS = 200 // folga entre um "carregando" e o próximo (ex.: porteiro → página)
const MAX_WAIT_MS = 20000 // trava de segurança: se algo nunca termina, o overlay sai mesmo assim

// loading = tempo mínimo; waiting = já navegou (ou o app acabou de abrir), esperando parar de carregar.
type TransitionPhase = 'idle' | 'loading' | 'waiting' | 'exiting'

export function PageTransitionProvider({ children }: { children: ReactNode }) {
    const navigate = useNavigate()
    const [phase, setPhase] = useState<TransitionPhase>('idle')
    const phaseRef = useRef<TransitionPhase>('idle')
    const timers = useRef<ReturnType<typeof setTimeout>[]>([])

    // Quantos "carregando" estão na tela. Ref (e não estado) porque é lido logo depois do commit
    // da navegação; o holdTick só serve para avisar o provider que o número mudou.
    const holds = useRef(0)
    const [holdTick, setHoldTick] = useState(0)

    function later(fn: () => void, ms: number): void {
        timers.current.push(setTimeout(fn, ms))
    }

    function clearTimers(): void {
        timers.current.forEach(clearTimeout)
        timers.current = []
    }

    useEffect(() => clearTimers, [])

    function changePhase(next: TransitionPhase): void {
        phaseRef.current = next
        setPhase(next)
    }

    const exit = useCallback((): void => {
        if (phaseRef.current !== 'waiting') return
        clearTimers()
        const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
        changePhase('exiting')
        later(() => changePhase('idle'), reducedMotion ? 0 : EXITING_MS)
    }, [])

    const transitionTo = useCallback(
        (to: To): void => {
            if (phaseRef.current !== 'idle') return

            const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
            changePhase('loading')

            later(
                () => {
                    navigate(to)
                    changePhase('waiting')
                    later(exit, MAX_WAIT_MS)
                },
                reducedMotion ? 0 : LOADING_MS,
            )
        },
        [navigate, exit],
    )

    const hold = useCallback(() => {
        holds.current += 1
        setHoldTick((t) => t + 1)
        return () => {
            holds.current -= 1
            setHoldTick((t) => t + 1)
        }
    }, [])

    // Abertura do app (F5, volta do login do Google): se a 1ª tela já nasce carregando, mostra a logo
    // em vez do "Carregando…" cru. Layout effect roda depois dos filhos e antes de pintar: não pisca.
    useLayoutEffect(() => {
        if (holds.current === 0) return
        changePhase('waiting')
        later(exit, MAX_WAIT_MS)
    }, [exit]) // exit é estável: roda só na montagem

    // Já na página destino: sai quando nada mais estiver carregando (e continuar assim por SETTLE_MS).
    useEffect(() => {
        if (phase !== 'waiting' || holds.current > 0) return
        const timer = setTimeout(() => {
            if (holds.current === 0) exit()
        }, SETTLE_MS)
        return () => clearTimeout(timer)
    }, [phase, holdTick, exit])

    const transitionValue = useMemo(() => ({ transitionTo }), [transitionTo])

    return (
        <TransitionContext.Provider value={transitionValue}>
            <TransitionHoldContext.Provider value={hold}>
                {children}

                {phase !== 'idle' && (
                    <div className={`transition-overlay ${phase}`} aria-label="Carregando página" role="status">
                        <div className="loader-container">
                            {/* loop: a 1ª volta é igual à do "once"; se a página demora, continua girando. */}
                            <LogoJustica animation="loop" durationMs={LOADING_MS} size={180} />
                        </div>
                    </div>
                )}
            </TransitionHoldContext.Provider>
        </TransitionContext.Provider>
    )
}
