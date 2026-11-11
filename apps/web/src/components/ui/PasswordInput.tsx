import { useState } from 'react'
import { Icon } from './Icon.tsx'

type PasswordInputProps = {
    id: string
    value: string
    onChange: (value: string) => void
    autoComplete?: string
}

// Campo de senha com o cadeado à esquerda e o botão de mostrar/ocultar (o olho) à direita.
export function PasswordInput({ id, value, onChange, autoComplete = 'current-password' }: PasswordInputProps) {
    const [visible, setVisible] = useState(false)
    return (
        <div className="field-icon">
            <Icon name="lock" size={17} />
            <input
                className="field"
                id={id}
                type={visible ? 'text' : 'password'}
                autoComplete={autoComplete}
                value={value}
                onChange={(e) => onChange(e.target.value)}
            />
            <button
                className="field-toggle"
                type="button"
                onClick={() => setVisible((v) => !v)}
                aria-label={visible ? 'Ocultar senha' : 'Mostrar senha'}
                aria-pressed={visible}
            >
                <Icon name={visible ? 'eyeOff' : 'eye'} size={17} />
            </button>
        </div>
    )
}
