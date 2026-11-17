import { describe, expect, it } from 'vitest'
import { parseConnectionUrl, readOnlySql } from './connectionUrl.ts'

describe('parseConnectionUrl', () => {
    it('postgres com porta, senha com caractere especial e sslmode', () => {
        expect(
            parseConnectionUrl(' postgresql://lexhub_leitura:p%40ss%3Aw@db.op.com.br:6543/operacao?sslmode=require '),
        ).toEqual({
            connector: 'postgres',
            host: 'db.op.com.br',
            port: 6543,
            database: 'operacao',
            user: 'lexhub_leitura',
            password: 'p@ss:w',
            ssl: true,
        })
    })

    it('mysql sem porta e ssl desligado', () => {
        expect(parseConnectionUrl('mysql://u:s@10.0.0.1/banco?ssl-mode=DISABLED')).toMatchObject({
            connector: 'mysql',
            port: null,
            ssl: false,
        })
    })

    it('sem sslmode a URL não decide o SSL; IPv6 sem colchetes', () => {
        expect(parseConnectionUrl('postgres://u:s@[2001:db8::1]:5432/b')).toMatchObject({
            host: '2001:db8::1',
            ssl: null,
        })
    })

    it('o que não é URL de banco não preenche nada', () => {
        expect(parseConnectionUrl('db.op.com.br')).toBeNull()
        expect(parseConnectionUrl('https://docs.google.com/x')).toBeNull()
        expect(parseConnectionUrl('')).toBeNull()
    })
})

describe('readOnlySql', () => {
    it('postgres: só SELECT e tempo máximo por consulta', () => {
        const sql = readOnlySql('postgres', 'operacao', null)
        expect(sql).toContain('GRANT CONNECT ON DATABASE "operacao" TO lexhub_leitura;')
        expect(sql).toContain("statement_timeout = '60s'")
        expect(sql).not.toMatch(/INSERT|UPDATE|DELETE/)
    })

    it('mysql: usuário preso ao IP do LexHub', () => {
        expect(readOnlySql('mysql', 'op', '203.0.113.10')).toContain("'lexhub_leitura'@'203.0.113.10'")
        expect(readOnlySql('mysql', '', null)).toContain('`banco_da_operacao`')
    })
})
