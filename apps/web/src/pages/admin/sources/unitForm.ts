import type { UnitInput } from '../../../types/index.ts'

// Módulo: as regras do formulário de unidade (fusos, código sugerido e validação), sem React.
// O banco valida de novo (api.create_unit / api.update_unit); aqui é para avisar antes de enviar.

// Os fusos do Brasil que o seletor oferece. Fuso novo = uma linha aqui.
export const BR_TIMEZONES: { tz: string; label: string }[] = [
    { tz: 'America/Rio_Branco', label: 'Rio Branco (AC) · UTC−5' },
    { tz: 'America/Manaus', label: 'Manaus (AM) · UTC−4' },
    { tz: 'America/Boa_Vista', label: 'Boa Vista (RR) · UTC−4' },
    { tz: 'America/Porto_Velho', label: 'Porto Velho (RO) · UTC−4' },
    { tz: 'America/Cuiaba', label: 'Cuiabá (MT) · UTC−4' },
    { tz: 'America/Campo_Grande', label: 'Campo Grande (MS) · UTC−4' },
    { tz: 'America/Sao_Paulo', label: 'São Paulo (SP, RJ, MG, Sul, DF, GO, ES) · UTC−3' },
    { tz: 'America/Bahia', label: 'Salvador (BA) · UTC−3' },
    { tz: 'America/Belem', label: 'Belém (PA, AP) · UTC−3' },
    { tz: 'America/Araguaina', label: 'Palmas (TO) · UTC−3' },
    { tz: 'America/Fortaleza', label: 'Fortaleza (CE, MA, PI, RN, PB) · UTC−3' },
    { tz: 'America/Recife', label: 'Recife (PE) · UTC−3' },
    { tz: 'America/Maceio', label: 'Maceió (AL, SE) · UTC−3' },
    { tz: 'America/Noronha', label: 'Fernando de Noronha · UTC−2' },
]

// 'America/Manaus' -> 'Manaus (AM) · UTC−4'; fuso fora da lista aparece como veio.
export const timezoneLabel = (tz: string): string => BR_TIMEZONES.find((t) => t.tz === tz)?.label ?? tz

// O que o campo Código aceita: maiúsculas, números e _ (o resto some enquanto a pessoa digita).
export const normalizeCode = (text: string): string =>
    text
        .normalize('NFD')
        .replace(/[̀-ͯ]/g, '')
        .toUpperCase()
        .replace(/[^A-Z0-9_]/g, '')
        .slice(0, 16)

// Código sugerido pelo nome: iniciais ('Luis Albert RJ' -> 'LARJ'); uma palavra só = ela inteira ('Sede' -> 'SEDE').
// Palavra curta toda em maiúsculas (sigla como 'RJ') entra inteira.
export function suggestCode(name: string): string {
    const words = name
        .normalize('NFD')
        .replace(/[̀-ͯ]/g, '')
        .split(/[^A-Za-z0-9]+/)
        .filter(Boolean)
    if (words.length === 0) return ''
    if (words.length === 1) return normalizeCode(words[0])
    const parts = words.map((w) => (w.length <= 3 && w === w.toUpperCase() ? w : w[0]))
    return normalizeCode(parts.join(''))
}

const CODE = /^[A-Z0-9_]{2,16}$/

// O primeiro problema do formulário, ou null se dá para enviar.
// create = o código também conta (formato e não repetir os da organização).
export function validateUnit(input: UnitInput, mode: 'create' | 'edit', existingCodes: string[]): string | null {
    if (!input.name.trim()) return 'Informe o nome da unidade.'
    if (mode === 'create') {
        if (!CODE.test(input.code)) return 'Código inválido: use de 2 a 16 letras maiúsculas, números ou _.'
        if (existingCodes.includes(input.code)) return `Já existe uma unidade com o código ${input.code}.`
    }
    if (!BR_TIMEZONES.some((t) => t.tz === input.timezone)) return 'Fuso inválido: escolha um da lista.'
    return null
}
