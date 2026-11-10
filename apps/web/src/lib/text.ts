// Módulo: comparar textos como uma pessoa compara, sem acento e sem maiúsculas ("Gestão" = "gestao").
// Usado em toda busca do app (Membros, hub...).

// 'Pré-Protocolo' -> 'pre-protocolo'
export const normalizeText = (text: string): string =>
    text
        .normalize('NFD')
        .replace(/\p{Diacritic}/gu, '')
        .toLowerCase()

// O texto contém a busca? Busca vazia (ou só espaços) = sim, para "sem busca" mostrar tudo.
export function matchesText(text: string, query: string): boolean {
    const q = normalizeText(query.trim())
    return !q || normalizeText(text).includes(q)
}
