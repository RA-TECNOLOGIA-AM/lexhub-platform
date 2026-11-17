import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { useNavigate, type To } from 'react-router'
import { TransitionAreaContext, TransitionContext, TransitionHoldContext } from './PageTransitionContext.ts'
import { LogoJustica } from '../ui/LogoJustica.tsx'
import './PageTransition.css'

const LOADING_MS = 1500 // tempo mínimo da animação (uma volta da logo)
const EXITING_MS = 450
const SETTLE_MS = 200 // folga entre um "carregando" e o próximo (ex.: porteiro → página)
const MAX_WAIT_MS = 20000 // trava de segurança: se algo nunca termina, o overlay sai mesmo assim

// loading = tempo mínimo; waiting = já navegou (ou o app acabou de abrir), esperando parar de carregar.
type TransitionPhase = 'idle' | 'loading' | 'waiting' | 'exiting'

// Onde a logo aparece: null = tela inteira; senão, o miolo (de onde termina a topbar e começa a coluna
// do conteúdo até o canto da janela).
type Bounds = { top: number; left: number }

function measure(area: HTMLElement | null): Bounds | null {
    if (!area?.isConnected) return null
    const box = area.getBoundingClientRect()
    const topbar = area.querySelector(':scope > .topbar')
    return { top: topbar ? topbar.getBoundingClientRect().bottom : Math.max(box.top, 0), left: box.left }
}

const sameBounds = (a: Bounds | null, b: Bounds | null) => a?.top === b?.top && a?.left === b?.left

export function PageTransitionProvider({ children }: { children: ReactNode }) {
    const navigate = useNavigate()
    const [phase, setPhase] = useState<TransitionPhase>('idle')
    const phaseRef = useRef<TransitionPhase>('idle')
    const timers = useRef<ReturnType<typeof setTimeout>[]>([])

    // Quantos "carregando" estão na tela. Ref (e não estado) porque é lido logo depois do commit
    // da navegação; o holdTick só serve para avisar o provider que o número mudou.
    const holds = useRef(0)
    const [holdTick, setHoldTick] = useState(0)

    // Coluna do conteúdo do AppLayout (registrada por ele). Na tela = a troca de página anima só o miolo.
    const area = useRef<HTMLElement | null>(null)
    const [bounds, setBounds] = useState<Bounds | null>(null)
    const registerArea = useCallback((element: HTMLElement | null) => {
        area.current = element
    }, [])

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
        later(
            () => {
                changePhase('idle')
                setBounds(null)
            },
            reducedMotion ? 0 : EXITING_MS,
        )
    }, [])

    const transitionTo = useCallback(
        (to: To): void => {
            // 'loading': já tem uma navegação agendada; esta seria um clique repetido.
            if (phaseRef.current === 'loading') return

            // 'waiting'/'exiting': o overlay já está na tela (ex.: abertura do app na volta do Google).
            // Antes a chamada era descartada e a página que esperava por ela ficava preta para sempre;
            // agora navega na hora e o overlay continua até o destino terminar de carregar.
            if (phaseRef.current !== 'idle') {
                clearTimers()
                navigate(to)
                changePhase('waiting')
                later(exit, MAX_WAIT_MS)
                return
            }

            const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
            setBounds(measure(area.current))
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

    // Logo no miolo: acompanha a janela, a topbar quebrando linha e o menu recolhendo enquanto está na tela.
    const active = phase !== 'idle'
    const inContent = bounds !== null
    useEffect(() => {
        const element = area.current
        if (!active || !inContent || !element) return
        const observer = new ResizeObserver(() => {
            const next = measure(element)
            setBounds((current) => (sameBounds(current, next) ? current : next))
        })
        observer.observe(element)
        const topbar = element.querySelector(':scope > .topbar')
        if (topbar) observer.observe(topbar)
        return () => observer.disconnect()
    }, [active, inContent])

    const transitionValue = useMemo(() => ({ transitionTo }), [transitionTo])

    return (
        <TransitionContext.Provider value={transitionValue}>
            <TransitionHoldContext.Provider value={hold}>
                <TransitionAreaContext.Provider value={registerArea}>{children}</TransitionAreaContext.Provider>

                {phase !== 'idle' && (
                    <div
                        className={`transition-overlay ${phase}${bounds ? ' in-content' : ''}`}
                        style={bounds ?? undefined}
                        aria-label="Carregando página"
                        role="status"
                    >
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
