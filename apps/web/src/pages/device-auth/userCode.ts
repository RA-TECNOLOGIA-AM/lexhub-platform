// O código que a TV mostra: 8 caracteres, em dois blocos (ABCD-EFGH).
// Mesmo alfabeto da API (device_auth.py): sem 0, 1, I e O, que se confundem na tela.
const ALPHABET = /^[A-HJ-NP-Z2-9]{8}$/

function compact(input: string): string {
    return input.toUpperCase().replace(/[^A-Z0-9]/g, '')
}

// Para o campo: maiúsculas, só letras/números e o hífen no lugar, enquanto a pessoa digita.
export function formatUserCode(input: string): string {
    const chars = compact(input).slice(0, 8)
    return chars.length > 4 ? `${chars.slice(0, 4)}-${chars.slice(4)}` : chars
}

// Para enviar: "xb88 ga8v" -> "XB88-GA8V"; inválido -> null.
export function normalizeUserCode(input: string): string | null {
    const chars = compact(input)
    return ALPHABET.test(chars) ? `${chars.slice(0, 4)}-${chars.slice(4)}` : null
}
