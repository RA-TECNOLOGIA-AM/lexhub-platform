import { useId, useLayoutEffect, useRef, useState, type ReactNode } from 'react'
import { useAuth } from '../../contexts/auth-context.ts'
import { useAsync } from '../../hooks/useAsync.ts'
import { dataClient } from '../../services/client.ts'
import { Icon, type IconName } from '../ui/Icon.tsx'
import { ApiKeySection } from './ApiKeySection.tsx'
import { AppearanceSection } from './AppearanceSection.tsx'
import { DevicesSection } from './DevicesSection.tsx'
import { ProfileSection } from './ProfileSection.tsx'
import './settings.css'

export type SettingsSectionId = 'perfil' | 'aparencia' | 'dispositivos' | 'chave-api'

type SettingsSection = {
    id: SettingsSectionId
    label: string // item do menu
    title: string // título no topo do conteúdo
    icon: IconName
    group: string // grupo do menu (ex.: "Minha conta")
    render: () => ReactNode
    apiKeyOnly?: boolean // só para quem pode pedir chave de API (Owner, Desenvolvedor, Gestor, Controller)
}

// As seções, na ordem do menu. Seção nova = um item aqui.
const SECTIONS: SettingsSection[] = [
    {
        id: 'perfil',
        label: 'Perfil',
        title: 'Meu Perfil',
        icon: 'user',
        group: 'Minha conta',
        render: () => <ProfileSection />,
    },
    {
        id: 'aparencia',
        label: 'Aparência',
        title: 'Aparência',
        icon: 'palette',
        group: 'Minha conta',
        render: () => <AppearanceSection />,
    },
    {
        id: 'dispositivos',
        label: 'Dispositivos',
        title: 'Dispositivos',
        icon: 'monitor',
        group: 'Minha conta',
        render: () => <DevicesSection />,
    },
    {
        id: 'chave-api',
        label: 'Chave de API',
        title: 'Chave de API',
        icon: 'key',
        group: 'Integrações',
        render: () => <ApiKeySection />,
        apiKeyOnly: true,
    },
]

// As seções que esta pessoa vê (a de Chave de API só aparece para quem pode pedir).
export function visibleSections(apiKeyEligible: boolean): SettingsSection[] {
    return SECTIONS.filter((s) => !s.apiKeyOnly || apiKeyEligible)
}

type SettingsDialogProps = {
    initialSection?: SettingsSectionId // abre direto numa seção (padrão: Perfil)
    onClose: () => void
}

// Módulo: o modal de Configurações (engrenagem da topbar): menu à esquerda, a seção à direita.
// Mesma mecânica do ui/Modal.tsx: <dialog> do navegador (foco preso, Esc fecha, fundo desfocado), aberto ao
// montar; ao fechar, o navegador devolve o foco à engrenagem. No celular vira tela cheia com abas no topo.
export function SettingsDialog({ initialSection = 'perfil', onClose }: SettingsDialogProps) {
    const dialog = useRef<HTMLDialogElement>(null)
    const titleId = useId()
    const org = useAuth().me?.org.slug ?? ''
    // Falha ao consultar = sem a seção (o banco nega o pedido de quem não pode, de qualquer jeito).
    const eligibility = useAsync(() => (org ? dataClient.getApiKeyEligibility(org) : Promise.resolve(null)), [org])
    const sections = visibleSections(!!eligibility.data?.eligible)
    const [active, setActive] = useState<SettingsSectionId>(initialSection)
    const section = sections.find((s) => s.id === active) ?? sections[0]
    const groups = [...new Set(sections.map((s) => s.group))]

    useLayoutEffect(() => {
        const element = dialog.current
        element?.showModal()
        return () => element?.close()
    }, [])

    function close() {
        dialog.current?.close()
        onClose()
    }

    return (
        <dialog
            ref={dialog}
            className="export-dialog settings-dialog"
            aria-labelledby={titleId}
            onCancel={(event) => {
                event.preventDefault()
                close()
            }}
        >
            <nav className="settings-nav" aria-label="Configurações">
                <p className="settings-nav-title">Configurações</p>
                {groups.map((group) => (
                    <div key={group} className="settings-nav-group">
                        <p className="settings-nav-label">{group}</p>
                        {sections
                            .filter((s) => s.group === group)
                            .map((s) => (
                                <button
                                    key={s.id}
                                    type="button"
                                    className="settings-nav-item"
                                    aria-current={s.id === section.id ? 'page' : undefined}
                                    onClick={() => setActive(s.id)}
                                >
                                    <Icon name={s.icon} size={17} />
                                    {s.label}
                                </button>
                            ))}
                    </div>
                ))}
            </nav>
            <section className="settings-main">
                <header className="settings-head">
                    <h2 className="settings-title" id={titleId}>
                        {section.title}
                    </h2>
                    <button className="iconbtn settings-close" type="button" aria-label="Fechar" onClick={close}>
                        <Icon name="close" size={16} />
                    </button>
                </header>
                <div className="settings-body">{section.render()}</div>
            </section>
        </dialog>
    )
}
