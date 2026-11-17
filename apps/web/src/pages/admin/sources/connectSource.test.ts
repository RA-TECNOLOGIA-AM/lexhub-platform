import { describe, expect, it } from 'vitest'
import type { DataSource, ProductOffice, SourceCheck } from '../../../types/index.ts'
import { CONNECTORS, connectorBlock, failedChecks, officeSub, sortOffices } from './connectSource.ts'

const office = (ref: string, name: string, linked = false): ProductOffice => ({
    ref,
    name,
    activity: 1234,
    linkedTo: linked ? { org: 'LexGroup', unit: 'NG', unitName: 'Nicolas Gomes' } : null,
})

const lexpre = { id: 'lexpre' } as DataSource

const check = (over: Partial<SourceCheck>): SourceCheck => ({
    key: 'login',
    ok: true,
    message: '',
    ms: 0,
    severity: 'error',
    skipped: false,
    ...over,
})

describe('connectSource', () => {
    it('os 5 tipos; banco e planilha guardam segredo', () => {
        expect(CONNECTORS.map((c) => c.key)).toEqual(['lexpre', 'lexflow', 'postgres', 'mysql', 'sheets'])
        expect(CONNECTORS.filter((c) => c.secret).map((c) => c.key)).toEqual(['postgres', 'mysql', 'sheets'])
    })

    it('bloqueia produto que a unidade já tem e banco/planilha sem a chave na API', () => {
        expect(connectorBlock('lexpre', false, [lexpre], true)).toBe('Já ligado a esta unidade')
        expect(connectorBlock('lexflow', false, [lexpre], false)).toBeNull()
        expect(connectorBlock('postgres', true, [], false)).toBe('Falta configurar a chave de cifra na API')
        expect(connectorBlock('sheets', true, [], true)).toBeNull()
    })

    it('aviso de usuário que escreve não conta como falha; pulada também não', () => {
        const checks = [
            check({ key: 'network' }),
            check({ key: 'readOnly', ok: false, severity: 'warn' }),
            check({ key: 'read', ok: false, skipped: true }),
        ]
        expect(failedChecks(checks)).toEqual([])
        expect(failedChecks([check({ ok: false, message: 'senha' })])).toHaveLength(1)
    })

    it('escritórios livres primeiro, por nome; ligados no fim', () => {
        const sorted = sortOffices([office('1', 'Nicolas Gomes', true), office('5', 'Belém'), office('4', 'Amazonas')])
        expect(sorted.map((o) => o.ref)).toEqual(['4', '5', '1'])
    })

    it('a linha de baixo mostra a atividade ou onde já está ligado', () => {
        expect(officeSub(office('4', 'A'), 'processos')).toBe('1.234 processos')
        expect(officeSub(office('1', 'B', true), 'processos')).toBe('Ligado à unidade NG (LexGroup)')
    })
})
