import { useEffect, useEffectEvent, type RefObject } from 'react'

type DismissOptions = {
    open: boolean // só escuta enquanto o painel está aberto
    onClose: () => void // o que fazer ao fechar
    isInside: (target: Element) => boolean // o clique foi "dentro"? (dentro não fecha)
    returnFocus?: RefObject<HTMLElement | null> // quem recebe o foco ao fechar com Esc (o botão que abriu)
}

// Módulo: fecha um painel aberto com Esc ou com clique fora dele.
// Usado pelo menu do celular, pelo seletor de organização e pelos painéis dos dashboards.
export function useDismiss({ open, onClose, isInside, returnFocus }: DismissOptions) {
    // useEffectEvent: lê sempre o onClose/isInside mais recentes sem precisar religar os eventos a cada desenho.
    const onKey = useEffectEvent((event: KeyboardEvent) => {
        if (event.key !== 'Escape') return
        onClose()
        returnFocus?.current?.focus()
    })
    const onClick = useEffectEvent((event: MouseEvent) => {
        if (!isInside(event.target as Element)) onClose()
    })

    useEffect(() => {
        if (!open) return
        const handleKey = (event: KeyboardEvent) => onKey(event)
        const handleClick = (event: MouseEvent) => onClick(event)
        document.addEventListener('keydown', handleKey)
        document.addEventListener('click', handleClick)
        return () => {
            document.removeEventListener('keydown', handleKey)
            document.removeEventListener('click', handleClick)
        }
    }, [open])
}
