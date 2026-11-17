import { Icon, type IconName } from './Icon.tsx'

type SegmentedProps<T extends string> = {
    label: string // o que o grupo escolhe (leitor de tela)
    options: { value: T; label: string; icon?: IconName }[]
    value: T
    onChange: (value: T) => void
    className?: string // variação visual (ex.: view-toggle no hub)
}

// Módulo: botões lado a lado em que um está escolhido (ex.: Peticionados | Protocolados no Top 10).
export function Segmented<T extends string>({ label, options, value, onChange, className }: SegmentedProps<T>) {
    return (
        <div className={className ? `segmented ${className}` : 'segmented'} role="group" aria-label={label}>
            {options.map((o) => (
                <button
                    key={o.value}
                    type="button"
                    aria-pressed={o.value === value}
                    className={o.value === value ? 'on' : undefined}
                    onClick={() => onChange(o.value)}
                >
                    {o.icon && <Icon name={o.icon} size={15} />}
                    {o.label}
                </button>
            ))}
        </div>
    )
}
