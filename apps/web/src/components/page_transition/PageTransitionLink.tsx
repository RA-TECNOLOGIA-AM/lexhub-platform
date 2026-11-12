import type { MouseEvent } from 'react'
import { Link, type LinkProps } from 'react-router'
import { usePageTransition } from './usePageTransition.ts'

export function PageTransitionLink({ onClick, ...props }: LinkProps) {
    const { transitionTo } = usePageTransition()

    function handleClick(event: MouseEvent<HTMLAnchorElement>) {
        onClick?.(event)

        if (
            event.defaultPrevented ||
            event.button !== 0 ||
            event.metaKey ||
            event.altKey ||
            event.ctrlKey ||
            event.shiftKey ||
            (props.target && props.target !== '_self') ||
            props.download != null
        ) {
            return
        }

        event.preventDefault()
        transitionTo(props.to)
    }

    return <Link {...props} onClick={handleClick} />
}
