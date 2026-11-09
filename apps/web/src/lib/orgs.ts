import type { Me } from '../types/index.ts'

// 'LexGroup' -> 'LG' · 'Cliente parceiro' -> 'CP' · '[ESCRITÓRIO]' -> 'ES'
// Duas primeiras palavras; com uma só palavra, as letras maiúsculas dela (LexGroup) ou as duas primeiras letras.
export function orgInitials(name: string): string {
    const [first = '', second = ''] = name.match(/\p{L}+/gu) ?? []
    if (second) return (first.charAt(0) + second.charAt(0)).toUpperCase()
    const capitals = first.match(/\p{Lu}/gu) ?? []
    return (capitals.length >= 2 ? capitals.slice(0, 2).join('') : first.slice(0, 2)).toUpperCase()
}

// O que fazer com a organização da URL:
// 'show' = já é a ativa · 'switch' = é outra da pessoa (buscar o "me" dela) · 'deny' = a pessoa não faz parte.
export type OrgDecision = 'show' | 'switch' | 'deny'

export function orgDecision(slug: string, me: Me): OrgDecision {
    if (me.org.slug === slug) return 'show'
    return me.orgs.some((o) => o.slug === slug) ? 'switch' : 'deny'
}
