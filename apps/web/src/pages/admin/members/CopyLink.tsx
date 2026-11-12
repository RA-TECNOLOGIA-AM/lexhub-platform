import { useState } from 'react'

// Módulo: o link do LexHub com o botão "Copiar link" (o convite não manda e-mail).
export function CopyLink({ link }: { link: string }) {
    const [copied, setCopied] = useState(false)
    async function copy() {
        try {
            await navigator.clipboard.writeText(link)
            setCopied(true)
        } catch {
            setCopied(false) // sem permissão de área de transferência: o link continua visível para copiar à mão
        }
    }
    return (
        <span className="stack" style={{ gap: 4 }}>
            <code className="small" style={{ wordBreak: 'break-all' }}>
                {link}
            </code>
            <button className="linkbtn" type="button" onClick={copy} style={{ alignSelf: 'flex-start' }}>
                {copied ? 'Link copiado' : 'Copiar link'}
            </button>
        </span>
    )
}
