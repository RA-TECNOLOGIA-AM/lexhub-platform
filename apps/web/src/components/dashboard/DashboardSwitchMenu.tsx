import { useRef, useState } from 'react'
import { Icon } from '../ui/Icon.tsx'
import { useDismiss } from '../../hooks/useDismiss.ts'

type DashboardSwitchMenuProps = {
    title: string // nome do dashboard (para os rótulos de acessibilidade)
    units: string[] // unidades do card
    disabledUnits: string[] // as desligadas
    onChange: (unit: string, enabled: boolean) => Promise<void> // quem usa grava (API) e atualiza a tela
}

// Módulo: o menu ⋯ do card do hub (só o Desenvolvedor vê): uma chave por unidade para ligar/desligar.
// Desligado some do hub e da API para os outros; o Dev continua vendo o card marcado "Desativado".
// Esconde: abrir/fechar (Esc, clique fora), o "salvando" por unidade e a mensagem de erro.
export function DashboardSwitchMenu({ title, units, disabledUnits, onChange }: DashboardSwitchMenuProps) {
    const [open, setOpen] = useState(false)
    const [saving, setSaving] = useState<string | null>(null)
    const [error, setError] = useState<string | null>(null)
    const button = useRef<HTMLButtonElement>(null)
    const panel = useRef<HTMLDivElement>(null)

    useDismiss({
        open,
        onClose: () => setOpen(false),
        isInside: (target) => !!panel.current?.contains(target) || !!button.current?.contains(target),
        returnFocus: button,
    })

    async function toggle(unit: string, enabled: boolean) {
        setSaving(unit)
        setError(null)
        try {
            await onChange(unit, enabled)
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Não foi possível salvar.')
        } finally {
            setSaving(null)
        }
    }

    return (
        <span className="dswitch">
            <button
                ref={button}
                type="button"
                className="fav-btn"
                aria-label={`Ligar ou desligar ${title}`}
                aria-haspopup="true"
                aria-expanded={open}
                onClick={() => setOpen((o) => !o)}
            >
                <Icon name="more" />
            </button>
            {open && (
                <div ref={panel} className="dswitch-panel" role="group" aria-label={`Unidades de ${title}`}>
                    <span className="dswitch-title">Dashboard ligado em</span>
                    {units.map((unit) => {
                        const on = !disabledUnits.includes(unit)
                        const label = unit.replace('_', ' ')
                        return (
                            <span key={unit} className="dswitch-row">
                                <span>{label}</span>
                                {/* Mesma chave da tela de fontes (ManageSource). */}
                                <button
                                    type="button"
                                    role="switch"
                                    className="switch"
                                    aria-checked={on}
                                    aria-label={`${title} em ${label}`}
                                    title={on ? 'Desligar nesta unidade' : 'Ligar nesta unidade'}
                                    disabled={saving !== null}
                                    aria-busy={saving === unit}
                                    onClick={() => toggle(unit, !on)}
                                />
                            </span>
                        )
                    })}
                    <span className="dswitch-hint muted small">Desligado some para todos; você continua vendo.</span>
                    {error && (
                        <span className="dswitch-error small" role="alert">
                            {error}
                        </span>
                    )}
                </div>
            )}
        </span>
    )
}
