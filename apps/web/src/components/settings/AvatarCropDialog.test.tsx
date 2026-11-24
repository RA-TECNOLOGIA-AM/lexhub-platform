import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { AvatarCropDialog } from './AvatarCropDialog.tsx'

const noop = () => {}

function render(props: { busy?: boolean; error?: string | null } = {}) {
    return renderToStaticMarkup(
        <AvatarCropDialog
            src="blob:foto"
            busy={props.busy ?? false}
            error={props.error ?? null}
            onCancel={noop}
            onChange={noop}
            onSave={noop}
        />,
    )
}

describe('AvatarCropDialog (igual ao LexFlow)', () => {
    it('cabeçalho, zoom e botões', () => {
        const html = render()
        for (const text of [
            'Ajustar foto do perfil',
            'Arraste para mover · Scroll para zoom',
            'Trocar',
            'Cancelar',
            'Salvar foto',
            '0%',
        ]) {
            expect(html).toContain(text)
        }
        expect(html).toContain('aria-label="Zoom"')
        expect(html).toContain('aria-label="Diminuir zoom"')
        expect(html).toContain('aria-label="Aumentar zoom"')
    })

    it('salvando: botões travados e "Salvando…"', () => {
        const html = render({ busy: true })
        expect(html).toContain('Salvando…')
        expect(html).not.toContain('Salvar foto')
    })

    it('mostra o erro do envio', () => {
        expect(render({ error: 'Não foi possível enviar a foto.' })).toContain('Não foi possível enviar a foto.')
    })
})
