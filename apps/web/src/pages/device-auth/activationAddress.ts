// Endereço legível da página de ativação, tirado do link do QR (sem protocolo, sem ?code=).
// Ex.: "https://hub.lexgroup.com.br/ativar?code=ABCD-EFGH" -> "hub.lexgroup.com.br/ativar".
// Link inválido: devolve null e a TV não mostra endereço.
export function activationAddress(verificationUri: string): string | null {
    try {
        const url = new URL(verificationUri)
        return `${url.host}${url.pathname}`.replace(/\/$/, '')
    } catch {
        return null
    }
}
