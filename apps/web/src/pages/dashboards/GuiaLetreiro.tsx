import type { CSSProperties } from 'react'
import { PageTransitionLink } from '../../components/page_transition/PageTransitionLink.tsx'
import './GuiaLetreiro.css'

// Módulo: a faixa do hub que avisa que existe o guia de Primeiros passos, no mesmo letreiro da faixa "Atenção"
// (DadosFaltando), em amarelo como ela. Clicar abre o guia. Quem pediu menos movimento vê as frases paradas.
// slug: o guia que abre (docRegistry); avisos: as frases que passam no letreiro.
const AVISOS = [
    'Novo por aqui? Veja o guia de Primeiros passos!',
    'Aprenda a escolher a unidade, achar e ler um dashboard',
    'Filtre, exporte e deixe o LexHub do seu jeito',
]

export function GuiaLetreiro({
    org,
    slug = 'guia-do-usuario',
    avisos = AVISOS,
}: {
    org: string
    slug?: string
    avisos?: string[]
}) {
    if (avisos.length === 0) return null
    return (
        <PageTransitionLink
            to={`/${org}/documentacao/${slug}`}
            className="hub-guia"
            title="Guia de Primeiros passos: como entrar, achar e ler um dashboard, filtrar e exportar. Clique para abrir"
        >
            <span className="hub-guia-letreiro" style={{ '--dur': `${14 * avisos.length}s` } as CSSProperties}>
                {avisos.map((a) => (
                    <span key={a}>📘 Primeiros passos 📘 {a}</span>
                ))}
            </span>
        </PageTransitionLink>
    )
}
