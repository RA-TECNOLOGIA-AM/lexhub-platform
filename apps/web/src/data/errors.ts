// Erro com o status HTTP, igual ao que a API real vai devolver (401, 403, 404...).
export class DataError extends Error {
    status: number

    constructor(status: number, message: string) {
        super(message)
        this.name = 'DataError'
        this.status = status
    }
}