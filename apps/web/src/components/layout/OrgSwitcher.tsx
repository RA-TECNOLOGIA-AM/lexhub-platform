import { useRef, useState } from 'react'
import { PageTransitionLink } from '../page_transition/PageTransitionLink.tsx'
import { orgInitials } from '../../lib/orgs.ts'
import type { Org } from '../../types/index.ts'
import { Icon } from '../ui/Icon.tsx'
import { useDismiss } from '../../hooks/useDismiss.ts'

type OrgSwitcherProps = {
    current: Org
    orgs: Org[] // as organizações da pessoa
    canCreate: boolean // equipe RA: mostra "Criar organização" (leva ao console da plataforma)
    onNavigate: () => void // ao escolher um item (ex.: fechar o menu do celular)
}

// Módulo: o seletor de organização da barra lateral. Cada organização é um link para o hub dela;
// trocar é só navegar (a URL manda, então cada aba fica na sua organização).
export function OrgSwitcher({ current, orgs, canCreate, onNavigate }: OrgSwitcherProps) {
    const [open, setOpen] = useState(false)
    const root = useRef<HTMLDivElement>(null)
    const button = useRef<HTMLButtonElement>(null)

    // Aberto: fecha com Esc (e devolve o foco ao botão) ou clicando fora.

    useDismiss({
        open,
        onClose: () => setOpen(false),
        isInside: (target) => !!root.current?.contains(target),
        returnFocus: button,
    })

    function choose() {
        setOpen(false)
        onNavigate()
    }

    return (
        <div className="org-switch" ref={root}>
            <button
                ref={button}
                className="org"
                type="button"
                aria-expanded={open}
                aria-controls="org-menu"
                onClick={() => setOpen((o) => !o)}
            >
                <span className="org-mark">{orgInitials(current.name)}</span>
                <span className="org-text">
                    <span className="org-name">{current.name}</span>
                    <span className="org-sub">{current.sub}</span>
                </span>
                <Icon name="chevrons" size={16} />
            </button>
            {open && (
                <div id="org-menu" className="org-menu">
                    <span className="org-menu-label">Suas organizações</span>
                    {orgs.map((o) => (
                        <PageTransitionLink
                            key={o.slug}
                            className="nav"
                            to={`/${o.slug}/dashboards`}
                            aria-current={o.slug === current.slug ? 'true' : undefined}
                            onClick={choose}
                        >
                            <span className="org-text">
                                <span>{o.name}</span>
                                <span className="org-sub">{o.sub}</span>
                            </span>
                            {o.slug === current.slug && (
                                <span role="img" aria-label="Organização atual" style={{ display: 'inline-flex' }}>
                                    <Icon name="check" size={16} />
                                </span>
                            )}
                        </PageTransitionLink>
                    ))}
                    {canCreate && (
                        <PageTransitionLink className="nav" to="/plataforma/clientes" onClick={choose}>
                            <Icon name="plus" size={16} />
                            Criar organização
                        </PageTransitionLink>
                    )}
                </div>
            )}
        </div>
    )
}
