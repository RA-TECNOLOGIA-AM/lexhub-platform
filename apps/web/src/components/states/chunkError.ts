// Depois de um deploy, os arquivos antigos (chunks) somem da Vercel e o import() do lazy falha.
// Esse erro não é bug da tela: recarregar a página baixa a versão nova.
const CHUNK_ERROR = /dynamically imported module|Importing a module script failed|error loading dynamically/i

export function isChunkLoadError(error: unknown): boolean {
    return error instanceof Error && CHUNK_ERROR.test(error.message)
}
