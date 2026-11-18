// Módulo: resume o user agent de uma sessão em "navegador · sistema" para a tela de Auditoria.
// Sem biblioteca: só os casos que aparecem no LexHub. Desconhecido = null (a tela omite).

const BROWSERS: [RegExp, string][] = [
    [/Edg\//, 'Edge'],
    [/OPR\/|Opera/, 'Opera'],
    [/SamsungBrowser\//, 'Samsung Internet'],
    [/Firefox\/|FxiOS\//, 'Firefox'],
    [/Chrome\/|CriOS\//, 'Chrome'],
    [/Safari\//, 'Safari'],
]

const SYSTEMS: [RegExp, string][] = [
    [/Windows/, 'Windows'],
    [/Android/, 'Android'],
    [/iPhone|iPad|iPod/, 'iOS'],
    [/Mac OS X|Macintosh/, 'macOS'],
    [/CrOS/, 'ChromeOS'],
    [/Linux/, 'Linux'],
]

// A entrada pelo QR da TV é feita pela API (Python), não por um navegador.
const SERVER = /python|httpx|aiohttp|supabase-py|node-fetch|undici/i

const pick = (ua: string, rules: [RegExp, string][]): string | null => rules.find(([re]) => re.test(ua))?.[1] ?? null

export function describeUserAgent(ua: string | null | undefined): string | null {
    if (!ua || !ua.trim()) return null
    if (SERVER.test(ua)) return 'TV (QR)'
    const parts = [pick(ua, BROWSERS), pick(ua, SYSTEMS)].filter(Boolean)
    return parts.length ? parts.join(' · ') : null
}
