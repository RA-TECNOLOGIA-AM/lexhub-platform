import { useId, useLayoutEffect, useRef, useState, type ReactNode } from 'react'
import { Icon, type IconName } from '../ui/Icon.tsx'
import { AppearanceSection } from './AppearanceSection.tsx'
import { ProfileSection } from './ProfileSection.tsx'
import './settings.css'

export type SettingsSectionId = 'perfil' | 'aparencia'

type SettingsSection = {
    id: SettingsSectionId
    label: string // item do menu
    title: string // título no topo do conteúdo
    icon: IconName
    group: string // grupo do menu (ex.: "Minha conta")
    render: () => ReactNode
}

// As seções, na ordem do menu. Seção nova = um item aqui (Dispositivos, Companhias... quando existirem).
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
]

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
    const [active, setActive] = useState<SettingsSectionId>(
        SECTIONS.some((s) => s.id === initialSection) ? initialSection : SECTIONS[0].id,
    )
    const section = SECTIONS.find((s) => s.id === active) ?? SECTIONS[0]
    const groups = [...new Set(SECTIONS.map((s) => s.group))]

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
                        {SECTIONS.filter((s) => s.group === group).map((s) => (
                            <button
                                key={s.id}
                                type="button"
                                className="settings-nav-item"
                                aria-current={s.id === active ? 'page' : undefined}
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
