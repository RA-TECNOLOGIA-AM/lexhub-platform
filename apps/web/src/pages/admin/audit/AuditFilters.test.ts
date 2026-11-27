import { describe, expect, it } from 'vitest'
import { kindSelectOptions } from './AuditFilters.tsx'

describe('kindSelectOptions', () => {
    it('tudo em ordem alfabética, com "Nunca acessou" no meio quando pode', () => {
        expect(kindSelectOptions(true).map((o) => o.label)).toEqual([
            'Chave de API',
            'Dashboards abertos',
            'Entradas',
            'Exportações',
            'Mudanças de acesso',
            'Nunca acessou',
            'Outros',
            'Segurança da conta',
            'Suporte',
            'Unidades e fontes',
        ])
    })

    it('sem permissão, sem "Nunca acessou"', () => {
        expect(kindSelectOptions(false).map((o) => o.value)).not.toContain('nunca')
    })
})
