import { useState } from 'react'
import type { SourceCheck } from '../../../types/index.ts'
import { Icon } from '../../../components/ui/Icon.tsx'

// Módulo: o resultado do teste de conexão (rede, login, leitura, só leitura), uma linha por checagem.
export function CheckList({ checks }: { checks: SourceCheck[] }) {
    return (
        <ul className="check-list" role="status" aria-label="Resultado do teste">
            {checks
                .filter((c) => !c.skipped)
                .map((c) => {
                    const kind = c.ok ? 'ok' : c.severity === 'warn' ? 'warn' : 'bad'
                    return (
                        <li key={c.key} className={`check-${kind}`}>
                            <Icon name={c.ok ? 'check' : c.severity === 'warn' ? 'alert' : 'xCircle'} size={16} />
                            <span>{c.message}</span>
                        </li>
                    )
                })}
        </ul>
    )
}

// Módulo: botão "Copiar" de um texto (IP, SQL). Sem permissão de área de transferência, o texto segue visível.
export function CopyButton({ text, label = 'Copiar' }: { text: string; label?: string }) {
    const [copied, setCopied] = useState(false)
    async function copy() {
        try {
            await navigator.clipboard.writeText(text)
            setCopied(true)
            window.setTimeout(() => setCopied(false), 1500)
        } catch {
            setCopied(false)
        }
    }
    return (
        <button className="btn btn-sm" type="button" onClick={copy}>
            {copied ? 'Copiado' : label}
        </button>
    )
}
