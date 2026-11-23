import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { Freshness } from './Freshness.tsx'

describe('Freshness (card do hub)', () => {
    it('sem hora: "Atualiza ao abrir", neutro (a API só busca a fonte quando alguém abre o dashboard)', () => {
        const html = renderToStaticMarkup(<Freshness syncedAt={null} source="LexFlow" />)
        expect(html).toContain('Atualiza ao abrir · LexFlow')
        expect(html).not.toContain('late')
    })

    it('sincronizado há pouco: verde, "Atualizado"', () => {
        const html = renderToStaticMarkup(<Freshness syncedAt={new Date().toISOString()} source="LexPre" />)
        expect(html).toContain('Atualizado')
        expect(html).not.toContain('late')
    })

    it('fonte desligada pela TI: "Fonte desligada", cinza, no lugar da hora', () => {
        const html = renderToStaticMarkup(
            <Freshness syncedAt={new Date().toISOString()} source="Planilha do financeiro" disabled />,
        )
        expect(html).toContain('Fonte desligada · Planilha do financeiro')
        expect(html).toContain('fresh off')
        expect(html).not.toContain('Atualizado')
    })

    it('passou do limite: âmbar, "Fonte atrasada"', () => {
        const tresHoras = new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString()
        const html = renderToStaticMarkup(<Freshness syncedAt={tresHoras} source="LexPre" maxDelayMin={60} />)
        expect(html).toContain('Fonte atrasada')
        expect(html).toContain('fresh late')
    })
})
