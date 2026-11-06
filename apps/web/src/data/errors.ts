// Erro com o status HTTP, igual ao que a API real vai devolver (401, 403, 404...).
export class DataError extends Error {
    status: number

    constructor(status: number, message: string) {
        super(message)
        this.name = 'DataError'
        this.status = status
    }
}
// Qualquer erro vira DataError: as telas lidam com um tipo só (status 0 = erro fora da API).
export function toDataError(err: unknown): DataError {
    return err instanceof DataError ? err : new DataError(0, 'Erro inesperado. Tente de novo.')
}
