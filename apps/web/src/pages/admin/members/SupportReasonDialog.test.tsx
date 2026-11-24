import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { SupportReasonDialog } from './SupportReasonDialog.tsx'
import { reasonState } from './supportReason.ts'

const noop = () => {}

describe('reasonState', () => {
    it('vale com 5 a 500 caracteres, sem contar os espaços das pontas', () => {
        expect(reasonState('abcd')).toEqual({ reason: 'abcd', length: 4, ok: false })
        expect(reasonState('   abcd  ').ok).toBe(false)
        expect(reasonState(' #4521 ')).toEqual({ reason: '#4521', length: 5, ok: true })
        expect(reasonState('x'.repeat(500)).ok).toBe(true)
        expect(reasonState('x'.repeat(501)).ok).toBe(false)
    })
})

describe('SupportReasonDialog', () => {
    it('título com o nome, campo do motivo, contador e botões', () => {
        const html = renderToStaticMarkup(
            <SupportReasonDialog name="Bruna Lima" busy={false} error={null} onStart={noop} onClose={noop} />,
        )
        for (const text of ['Ver como Bruna Lima', 'Motivo (ex.: número do chamado)', '0/500', 'Cancelar', 'Começar']) {
            expect(html).toContain(text)
        }
        expect(html).toContain('maxLength="500"')
        // vazio: Começar travado
        expect(html).toMatch(/<button[^>]*disabled=""[^>]*>Começar<\/button>/)
    })

    it('erro da API aparece como alerta; iniciando: "Começando…"', () => {
        const html = renderToStaticMarkup(
            <SupportReasonDialog name="Bruna" busy error="Sem acesso" onStart={noop} onClose={noop} />,
        )
        expect(html).toContain('role="alert"')
        expect(html).toContain('Sem acesso')
        expect(html).toContain('Começando…')
    })
})
