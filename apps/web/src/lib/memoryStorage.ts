// Módulo: um Storage em memória (getItem/setItem/removeItem/clear) para os testes.
// O Node do CI (24) não tem localStorage/sessionStorage; o Node 25+ tem. Com isto os testes rodam igual nos dois:
// vi.stubGlobal('sessionStorage', memoryStorage()).
export function memoryStorage(): Storage {
    const data = new Map<string, string>()
    return {
        get length() {
            return data.size
        },
        key: (i: number) => [...data.keys()][i] ?? null,
        getItem: (k: string) => data.get(k) ?? null,
        setItem: (k: string, v: string) => void data.set(k, String(v)),
        removeItem: (k: string) => void data.delete(k),
        clear: () => data.clear(),
    }
}
