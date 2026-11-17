import { useState } from 'react'
import { storedSidebarCollapsed, storeSidebarCollapsed } from '../lib/sidebar.ts'

// Hook: barra lateral recolhida ou aberta, lembrada no localStorage (lib/sidebar.ts).
export function useSidebarCollapsed(): { collapsed: boolean; setCollapsed: (collapsed: boolean) => void } {
    const [collapsed, setState] = useState(() => storedSidebarCollapsed())

    const setCollapsed = (next: boolean) => {
        storeSidebarCollapsed(next)
        setState(next)
    }

    return { collapsed, setCollapsed }
}
