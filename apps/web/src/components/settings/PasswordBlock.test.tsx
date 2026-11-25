import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { PasswordBlockView, type PasswordBlockViewProps, validatePassword } from './PasswordBlock.tsx'

const noop = () => {}
const render = (over: Partial<PasswordBlockViewProps>) =>
    renderToStaticMarkup(
        <PasswordBlockView
            hasPassword={false}
            editing={false}
            password=""
            confirm=""
            busy={false}
            error={null}
            saved={false}
            onEdit={noop}
            onCancel={noop}
            onSave={noop}
            onPassword={noop}
            onConfirm={noop}
            {...over}
        />,
    )

describe('validatePassword', () => {
    it('pede os dois campos, senhas iguais e 6 caracteres', () => {
        expect(validatePassword('', 'abc123')).toBe('Preencha os dois campos.')
        expect(validatePassword('abc123', '   ')).toBe('Preencha os dois campos.')
        expect(validatePassword('abc123', 'abc124')).toBe('As senhas não coincidem.')
        expect(validatePassword('12345', '12345')).toBe('A senha precisa ter pelo menos 6 caracteres.')
        expect(validatePassword('abc123', 'abc123')).toBeNull()
    })
})

describe('PasswordBlockView', () => {
    it('só Google: "Não definida" e "Criar senha"', () => {
        const html = render({ hasPassword: false })
        expect(html).toContain('Não definida')
        expect(html).toContain('Criar senha')
        expect(html).not.toContain('Alterar senha')
    })

    it('com senha: pontos e "Alterar senha"', () => {
        const html = render({ hasPassword: true })
        expect(html).toContain('••••••••')
        expect(html).toContain('Alterar senha')
    })

    it('carregando: traço e sem botão', () => {
        const html = render({ hasPassword: null })
        expect(html).toContain('—')
        expect(html).not.toContain('Criar senha')
    })

    it('editando: dois campos, Salvar e Cancelar, sem o botão de abrir', () => {
        const html = render({ editing: true })
        expect(html).toContain('Nova senha')
        expect(html).toContain('Confirmar nova senha')
        expect(html).toContain('Salvar')
        expect(html).toContain('Cancelar')
        expect(html).not.toContain('Criar senha')
        expect(html).toContain('autoComplete="new-password"')
    })

    it('erro aparece como alerta com os campos abertos', () => {
        const html = render({ editing: true, error: 'Senha fraca. Use mais caracteres, com letras e números.' })
        expect(html).toContain('role="alert"')
        expect(html).toContain('Senha fraca.')
        expect(html).toContain('Nova senha')
    })

    it('salvo: aviso de sucesso', () => {
        const html = render({ hasPassword: true, saved: true })
        expect(html).toContain('Senha salva. Você já pode entrar com e-mail e senha.')
    })

    it('salvando: botão desabilitado com "Salvando…"', () => {
        const html = render({ editing: true, busy: true })
        expect(html).toContain('Salvando…')
        expect(html).toMatch(/<button[^>]*disabled[^>]*>Salvando…/)
    })
})
