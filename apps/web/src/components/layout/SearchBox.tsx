import { useLocation, useNavigate, useSearchParams } from 'react-router'
import { Icon } from '../ui/Icon.tsx'
import { SEARCH_PARAM } from '../../lib/dashboardSearch.ts'

type SearchBoxProps = {
    org: string // slug da organização ativa: a busca leva ao hub dela
}

// Módulo: o campo "Buscar dashboard" do topo. O texto mora na URL do hub (?busca=), não num estado próprio:
// assim F5, voltar e link compartilhado mantêm a busca, e o hub só precisa ler a URL.
export function SearchBox({ org }: SearchBoxProps) {
    const { pathname } = useLocation()
    const [params] = useSearchParams()
    const navigate = useNavigate()

    const hub = `/${org}/dashboards`
    const onHub = pathname === hub
    const value = onHub ? (params.get(SEARCH_PARAM) ?? '') : '' // fora do hub o campo começa vazio

    function search(text: string) {
        const next = new URLSearchParams(onHub ? params : undefined) // no hub, mantém a unidade (?unidade=NG)
        if (text) next.set(SEARCH_PARAM, text)
        else next.delete(SEARCH_PARAM)
        const query = next.toString()
        // replace no hub: cada letra digitada não vira uma entrada no "voltar" do navegador.
        navigate(query ? `${hub}?${query}` : hub, { replace: onHub })
    }

    return (
        <label className="search">
            <span className="sr-only">Buscar dashboard</span>
            <input
                className="field"
                type="search"
                placeholder="Buscar dashboard"
                value={value}
                onChange={(event) => search(event.target.value)}
                onKeyDown={(event) => {
                    if (event.key === 'Escape') search('')
                }}
            />
            <Icon name="search" size={16} style={{ color: 'var(--text-muted)' }} />
        </label>
    )
}
