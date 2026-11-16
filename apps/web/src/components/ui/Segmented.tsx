type SegmentedProps<T extends string> = {
    label: string // o que o grupo escolhe (leitor de tela)
    options: { value: T; label: string }[]
    value: T
    onChange: (value: T) => void
}

// Módulo: botões lado a lado em que um está escolhido (ex.: Peticionados | Protocolados no Top 10).
export function Segmented<T extends string>({ label, options, value, onChange }: SegmentedProps<T>) {
    return (
        <div className="segmented" role="group" aria-label={label}>
            {options.map((o) => (
                <button
                    key={o.value}
                    type="button"
                    aria-pressed={o.value === value}
                    className={o.value === value ? 'on' : undefined}
                    onClick={() => onChange(o.value)}
                >
                    {o.label}
                </button>
            ))}
        </div>
    )
}
