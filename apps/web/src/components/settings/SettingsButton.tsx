import { useState } from 'react'
import { Icon } from '../ui/Icon.tsx'
import { SettingsDialog } from './SettingsDialog.tsx'

// Módulo: a engrenagem da topbar. Abre o modal de Configurações (Perfil, Aparência...).
export function SettingsButton() {
    const [open, setOpen] = useState(false)
    return (
        <>
            <button
                className="iconbtn"
                type="button"
                aria-label="Configurações"
                title="Configurações"
                aria-haspopup="dialog"
                onClick={() => setOpen(true)}
            >
                <Icon name="settings" />
            </button>
            {open && <SettingsDialog onClose={() => setOpen(false)} />}
        </>
    )
}
