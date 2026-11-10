import { describe, expect, it } from 'vitest'
import { toCsv } from './csv.ts'

const COLUMNS = [
    { key: 'id', label: 'ID' },
    { key: 'nome', label: 'Nome do Cliente' },
]

describe('toCsv', () => {
    it('cabeçalho com os rótulos, ; entre colunas, CRLF entre linhas e BOM no começo', () => {
        expect(toCsv(COLUMNS, [{ id: 1, nome: 'Ana' }])).toBe('\uFEFFID;Nome do Cliente\r\n1;Ana')
    })

    it('protege valores com ; aspas ou quebra de linha', () => {
        const csv = toCsv(COLUMNS, [{ id: 2, nome: 'Silva; "Ana"' }])
        expect(csv.split('\r\n')[1]).toBe('2;"Silva; ""Ana"""')
    })

    it('valor vazio ou ausente vira célula vazia', () => {
        expect(toCsv(COLUMNS, [{ id: null }]).split('\r\n')[1]).toBe(';')
    })
})
