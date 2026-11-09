import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router'
import { orgInitials } from '../../lib/orgs.ts'
import type { Org } from '../../types/index.ts'
import { Icon } from '../ui/Icon.tsx'

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
    useEffect(() => {
        if (!open) return
        function onKey(e: KeyboardEvent) {
            if (e.key === 'Escape') {
                setOpen(false)
                button.current?.focus()
            }
        }
        function onClick(e: MouseEvent) {
            if (!root.current?.contains(e.target as Node)) setOpen(false)
        }
        document.addEventListener('keydown', onKey)
        document.addEventListener('click', onClick)
        return () => {
            document.removeEventListener('keydown', onKey)
            document.removeEventListener('click', onClick)
        }
    }, [open])

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
                        <Link
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
                        </Link>
                    ))}
                    {canCreate && (
                        <Link className="nav" to="/plataforma/clientes" onClick={choose}>
                            <Icon name="plus" size={16} />
                            Criar organização
                        </Link>
                    )}
                </div>
            )}
        </div>
    )
}
