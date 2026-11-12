import { DataError } from '../../../services/errors.ts'

// 403 de api.access_overview = quem abriu não gere acesso nesta organização: a página mostra a
// matriz de papéis e um aviso. Qualquer outro erro vai para a tela de erro comum.
export function accessErrorView(error: unknown): { forbidden: boolean } {
    return { forbidden: error instanceof DataError && error.status === 403 }
}
