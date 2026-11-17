import { useState } from 'react'

// Uma lista paginada: os itens da página atual e como trocar de página. Se a lista encolher, fica na última.
export function usePagina<T>(itens: T[], porPagina: number) {
    const [pagina, setPagina] = useState(0)
    const total = Math.max(1, Math.ceil(itens.length / porPagina))
    const atual = Math.min(pagina, total - 1)
    return {
        itens: itens.slice(atual * porPagina, (atual + 1) * porPagina),
        pagina: atual,
        total,
        setPagina,
    }
}
