import { DataError } from '../../../services/errors.ts'

// 403 de api.list_members = quem abriu não gere membros nesta organização: a página mostra um
// estado próprio. Qualquer outro erro vai para a tela de erro comum.
export function membersErrorView(error: unknown): { forbidden: boolean } {
    return { forbidden: error instanceof DataError && error.status === 403 }
}
